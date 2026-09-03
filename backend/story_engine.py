"""故事引擎：prompt 工程、mock 降级生成器、结构诊断。

AI 的四个参与点：
  1. generate_opening  —— 从设定生成开篇节点 + 有后果暗示的分歧选项
  2. generate_continuation —— 带故事圣经续写后继节点，保证跨分支一致性
  3. generate_ending  —— 收束结局，回应路径上埋下的伏笔
  4. diagnose_structure —— 结构诊断（死路/孤立/失衡），属于"AI 帮产品"
"""
import random
import string
import uuid

from llm import chat_json, llm_available, LLMError


def new_id():
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------- prompt 构建

SYSTEM_WRITER = (
    "你是一位精通互动叙事（Choose-Your-Own-Adventure / 分支剧）的中文小说家与编剧。\n"
    "你的作品特点：画面感强、节奏紧凑、每个选择都真正改变故事走向。\n"
    "你必须只输出一个合法的 JSON 对象，不要输出任何解释文字、不要使用 markdown 代码围栏。"
)


def _bible_block(story):
    """故事圣经：跨分支一致性的唯一事实来源。"""
    lines = [
        f"【故事标题】{story.get('title') or '未命名'}",
        f"【世界观设定】{story.get('world') or '（未填写）'}",
        f"【主角】{story.get('protagonist') or '（未填写）'}",
        f"【故事前提】{story.get('premise') or '（未填写）'}",
        f"【基调/风格】{story.get('tone') or '（未指定）'}",
    ]
    chars = story.get("characters") or []
    if chars:
        lines.append("【已确立角色】")
        for c in chars:
            lines.append(f"  - {c.get('name')}：{c.get('desc')}")
    threads = story.get("threads") or []
    if threads:
        lines.append("【已埋伏笔 / 未解悬念】")
        for t in threads:
            lines.append(f"  - {t}")
    return "\n".join(lines)


def _path_block(path):
    """当前路径摘要：从根节点到当前节点的已读文本。"""
    if not path:
        return "（这是故事的开篇，尚无已发生情节。）"
    parts = ["【玩家已经历的情节（按顺序）】"]
    for item in path:
        parts.append(f"◆ {item.get('text','')}")
        if item.get("chosen_label"):
            parts.append(f"  → 玩家选择了：{item['chosen_label']}")
    return "\n".join(parts)


OPENING_SCHEMA = """输出 JSON，结构严格如下：
{
  "title": "8字以内的故事标题",
  "text": "开篇正文，350-500字，中文。必须在前100字内抛出钩子，结尾停在需要抉择的时刻。",
  "characters": [{"name":"角色名","desc":"身份+性格+当前状态，30字内"}],
  "threads": ["故事中埋下的伏笔或未解悬念，每条20字内，2-4条"],
  "options": [
    {"label":"选项短句，15字内","hint":"这个选择可能导致什么，20字内"}
  ]
}
options 必须 2-3 个，且彼此导向真正不同的走向（不可是同义改写）。"""

CONT_SCHEMA = """基于故事圣经与已发生情节，续写玩家做出上一个选择之后的情节。
输出 JSON，结构严格如下：
{
  "text": "本节点正文，300-450字，中文。必须承接上一节点末尾，并体现玩家所选行动的直接后果。",
  "characters": [{"name":"角色名","desc":"身份+性格+当前状态，30字内"}],
  "threads": ["新增伏笔或已回收的伏笔，每条20字内"],
  "options": [
    {"label":"选项短句，15字内","hint":"这个选择可能导致什么，20字内"}
  ]
}
规则：
- 严禁与已确立角色设定矛盾；若某角色已死亡/离场，不得无故出现。
- options 为 2-3 个；若本节点情节上适合收束为结局，则 options 返回空数组 []。"""

ENDING_SCHEMA = """为这条故事路径写一个结局收束段。
输出 JSON，结构严格如下：
{
  "text": "结局正文，250-400字，中文。必须回应路径上埋下的伏笔，给玩家'原来如此'或'意料之外'的收束感。",
  "ending_type": "其中一个：圆满结局 / 悲剧结局 / 开放式结局 / 反转结局",
  "resolved_threads": ["本结局回收了哪些伏笔"]
}"""

DIAG_SCHEMA = """你是互动故事的结构审校。检查下面的故事树并输出诊断。
输出 JSON：
{
  "issues": [
    {"node_id":"节点ID","type":"dead_end|shallow|repetitive","message":"一句话中文说明"}
  ],
  "summary": "对整体结构的一句话评价，40字内"
}
判定标准：
- dead_end：既无选项也非结局，玩家会卡住。
- shallow：结局铺垫不足（该路径总字数过少）。
- repetitive：不同分支出现雷同情节或雷同选项。
若无问题，issues 返回空数组。"""


# ---------------------------------------------------------------- AI 任务

def generate_opening(story):
    """1. 开篇生成。返回 dict（含 mock 标记）。"""
    if not llm_available():
        return _mock_opening(story)
    user = f"{_bible_block(story)}\n\n请据此创作互动故事的开篇。\n{OPENING_SCHEMA}"
    try:
        data = chat_json(SYSTEM_WRITER, user, temperature=1.2)
        data["_mock"] = False
        return _validate_node(data)
    except LLMError:
        data = _mock_opening(story)
        data["_degraded"] = True
        return data


def generate_continuation(story, path, chosen_label):
    """2. 续写生成：注入故事圣经 + 路径上下文，保证跨分支一致。"""
    if not llm_available():
        return _mock_continuation(story, chosen_label)
    brief = dict(story)
    user = (
        f"{_bible_block(brief)}\n\n{_path_block(path)}\n\n"
        f"玩家刚刚选择了：「{chosen_label}」。请续写下一个节点。\n{CONT_SCHEMA}"
    )
    try:
        data = chat_json(SYSTEM_WRITER, user, temperature=1.1)
        data["_mock"] = False
        return _validate_node(data)
    except LLMError:
        data = _mock_continuation(story, chosen_label)
        data["_degraded"] = True
        return data


def generate_ending(story, path):
    """3. 结局收束。"""
    if not llm_available():
        return _mock_ending(story)
    user = f"{_bible_block(story)}\n\n{_path_block(path)}\n\n请为这条路径写结局。\n{ENDING_SCHEMA}"
    try:
        data = chat_json(SYSTEM_WRITER, user, temperature=1.0)
        data["_mock"] = False
        data.setdefault("ending_type", "开放式结局")
        return data
    except LLMError:
        data = _mock_ending(story)
        data["_degraded"] = True
        return data


def diagnose_structure(story):
    """4. 结构诊断：规则先行（确定、免费），有 LLM 时叠加语义判断。"""
    issues, summary = _rule_diagnosis(story)
    if llm_available():
        try:
            data = chat_json(
                "你是互动叙事结构审校专家，只输出合法 JSON。",
                f"以下是故事树 JSON：\n{_compact_tree(story)}\n\n{DIAG_SCHEMA}",
                temperature=0.3,
            )
            seen = {(i.get("node_id"), i.get("type")) for i in issues}
            for it in data.get("issues", []):
                if (it.get("node_id"), it.get("type")) not in seen:
                    issues.append(it)
            if data.get("summary"):
                summary = data["summary"]
        except LLMError:
            pass
    return {"issues": issues, "summary": summary, "mock": not llm_available()}


# ---------------------------------------------------------------- 校验/规整

def _validate_node(data):
    """对模型输出做防御式校验：缺字段补默认，选项结构规整。"""
    if not isinstance(data, dict):
        raise LLMError("模型输出不是对象")
    text = str(data.get("text", "")).strip()
    if not text:
        raise LLMError("正文为空")
    opts = []
    for o in (data.get("options") or [])[:3]:
        if not isinstance(o, dict):
            continue
        label = str(o.get("label", "")).strip()
        if not label:
            continue
        opts.append({
            "id": new_id(),
            "label": label,
            "hint": str(o.get("hint", "")).strip(),
            "child": None,
        })
    return {
        "title": str(data.get("title", "")).strip(),
        "text": text,
        "options": opts,
        "characters": [c for c in (data.get("characters") or []) if isinstance(c, dict) and c.get("name")],
        "threads": [str(t) for t in (data.get("threads") or []) if t],
    }


# ---------------------------------------------------------------- 结构诊断（规则层）

def _rule_diagnosis(story):
    issues = []
    nodes = story.get("nodes", {})
    root = story.get("root")

    # 可达性
    reachable, stack = set(), [root] if root else []
    while stack:
        nid = stack.pop()
        if nid in reachable or nid not in nodes:
            continue
        reachable.add(nid)
        for o in nodes[nid].get("options", []):
            if o.get("child"):
                stack.append(o["child"])

    for nid, n in nodes.items():
        if nid not in reachable:
            issues.append({"node_id": nid, "type": "orphan",
                           "message": "该节点没有任何路径可以到达，是孤立内容。"})
        if not n.get("is_ending") and not n.get("options"):
            issues.append({"node_id": nid, "type": "dead_end",
                           "message": "既无选项也非结局，玩家会在此卡住。"})
        if n.get("is_ending") and len(n.get("text", "")) < 120:
            issues.append({"node_id": nid, "type": "shallow",
                           "message": "结局铺垫偏短，建议补充收束内容。"})

    endings = [n for n in nodes.values() if n.get("is_ending")]
    total = len(nodes)
    summary = f"共 {total} 个节点、{len(endings)} 个结局。"
    if total >= 3 and not endings:
        summary += "尚无任何结局，建议至少完成一条路径。"
    elif total and len(endings) >= 2:
        summary += "多结局结构已成形，注意各结局的差异化。"
    elif total:
        summary += "目前只有一个结局，分支价值尚未充分体现。"
    return issues, summary


def _compact_tree(story):
    """给 LLM 的精简树结构，控制 token。"""
    slim = {}
    for nid, n in story.get("nodes", {}).items():
        slim[nid] = {
            "text": n.get("text", "")[:180],
            "is_ending": bool(n.get("is_ending")),
            "options": [{"label": o.get("label"), "child": o.get("child")}
                        for o in n.get("options", [])],
        }
    import json as _j
    return _j.dumps({"root": story.get("root"), "nodes": slim}, ensure_ascii=False)


# ---------------------------------------------------------------- mock 生成器（演示模式）

_PREMISE_POOL = [
    ("《雾中来信》", "一封没有署名的信，把{p}引向了{w}深处那栋据说三十年没人住过的宅子。"),
    ("《第七次日落》", "{w}的时钟停在了第七次日落。{p}是唯一记得昨天发生过什么的人。"),
    ("《无声车站》", "末班车进站时，{p}发现整节车厢的人都不眨眼。而{w}的广播，正在念{p}的名字。"),
]


def _subject(story):
    p = (story.get("protagonist") or "一个陌生人").strip()
    w = (story.get("world") or "一座被雾困住的城市").strip()
    return p, w


def _mock_opening(story):
    p, w = _subject(story)
    title, tpl = random.choice(_PREMISE_POOL)
    text = tpl.format(p=p, w=w) + (
        f"\n\n{story.get('premise') or ''}".strip()[:120]
        + "\n\n风穿过街道，带来一句几乎听不见的提醒：往前走，或者回头，都只有一次机会。"
        "你的手停在门把上，指尖发凉。远处某个地方，有东西正在靠近。"
    )
    return {
        "title": title,
        "text": text,
        "characters": [{"name": p.split("，")[0][:8], "desc": "故事主角，被卷入异常事件"}],
        "threads": ["没有署名的信从何而来", "远处靠近的究竟是什么"],
        "options": [
            {"id": new_id(), "label": "推门进去", "hint": "直面未知，可能发现真相", "child": None},
            {"id": new_id(), "label": "转身离开", "hint": "回避风险，但线索会消失", "child": None},
            {"id": new_id(), "label": "先查看信件", "hint": "谨慎行事，可能获得提示", "child": None},
        ],
        "_mock": True,
    }


_MID = [
    "门在身后合上，屋里比想象中更冷。{l}——你最终还是这样做了。桌上摊开的笔记写着半行字，墨迹未干。",
    "你退到街角，霓虹把影子拉得很长。{l}看似安全，但口袋里的信纸突然变得滚烫。",
    "你压低呼吸，把一切看在眼里。{l}让你避开了正面冲突，却也错过了某个关键的东西。",
]


def _mock_continuation(story, chosen_label):
    text = random.choice(_MID).format(l=f"「{chosen_label}」")
    if random.random() < 0.35:
        return {
            "title": "",
            "text": text + "\n\n就在这时，答案以最意想不到的方式出现了——故事在这里抵达了它的终点。",
            "options": [],
            "characters": [],
            "threads": [f"选择「{chosen_label}」的直接后果"],
            "_mock": True,
        }
    return {
        "title": "",
        "text": text + "\n\n走廊尽头有两扇门，一扇透着光，一扇传来极轻的敲击声。",
        "options": [
            {"id": new_id(), "label": "走向有光的门", "hint": "光里可能有出口，也可能是陷阱", "child": None},
            {"id": new_id(), "label": "循敲击声而去", "hint": "那里有人——或者曾经有人", "child": None},
        ],
        "characters": [],
        "threads": ["敲击声来自哪里"],
        "_mock": True,
    }


def _mock_ending(story):
    return {
        "text": "雾散的时候，你终于明白：这一切从来不是意外。你做出的每个选择，"
               "都在把故事推向此刻。有些门一旦推开就再也关不上，而你，已经推开了。",
        "ending_type": random.choice(["圆满结局", "悲剧结局", "开放式结局", "反转结局"]),
        "resolved_threads": ["信件的来源","雾中靠近之物"],
        "_mock": True,
    }
