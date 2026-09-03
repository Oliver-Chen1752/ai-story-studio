"""端到端冒烟测试：开篇 -> 续写 -> 结局 -> 诊断 -> 保存/读取。"""
import json
import urllib.request

BASE = "http://127.0.0.1:5001"


def post(url, body):
    req = urllib.request.Request(BASE + url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def get(url):
    return json.loads(urllib.request.urlopen(BASE + url, timeout=30).read())


story = {
    "title": "", "world": "一座被永恒浓雾困住的滨海城市",
    "protagonist": "林澈，28岁，替人寻物的私家侦探",
    "premise": "一位老妇人出价十万，请他在雾中找到失踪三十年的女儿",
    "tone": "冷峻悬疑", "characters": [], "threads": [],
    "root": None, "nodes": {},
}

print("== status ==")
print(get("/api/status"))

print("== opening ==")
op = post("/api/story/opening", story)
print("mock:", op.get("_mock"), "| title:", op["title"], "| options:", len(op["options"]))
print("text head:", op["text"][:80].replace("\n", " "))
assert len(op["options"]) >= 2, "开篇至少要有2个选项"
assert op["characters"], "应提取角色"
assert op["threads"], "应提取伏笔"

# 组装成前端会保存的形态
sid = "e2e00001"
story["id"] = sid
story["title"] = op["title"]
root_id = "root0001"
story["root"] = root_id
story["nodes"][root_id] = {"id": root_id, "text": op["text"], "is_ending": False,
                           "ending_type": "", "options": op["options"]}
story["characters"] = op["characters"]
story["threads"] = op["threads"]

print("== continue ==")
opt = story["nodes"][root_id]["options"][0]
path = [{"id": root_id, "text": op["text"], "chosen_label": None}]
ct = post("/api/story/continue", {"story": story, "path": path, "chosen_label": opt["label"]})
print("mock:", ct.get("_mock"), "| options:", len(ct["options"]))
print("text head:", ct["text"][:80].replace("\n", " "))
assert ct["text"], "续写正文为空"

child_id = "child0001"
story["nodes"][child_id] = {"id": child_id, "text": ct["text"], "is_ending": False,
                            "ending_type": "", "options": ct["options"]}
opt["child"] = child_id

print("== ending ==")
path2 = path + [{"id": child_id, "text": ct["text"], "chosen_label": opt["label"]}]
en = post("/api/story/ending", {"story": story, "path": path2})
print("mock:", en.get("_mock"), "| type:", en.get("ending_type"))
assert en["text"], "结局正文为空"
story["nodes"][child_id]["is_ending"] = True
story["nodes"][child_id]["ending_type"] = en.get("ending_type", "结局")
story["nodes"][child_id]["text"] = en["text"]
story["nodes"][child_id]["options"] = []

print("== diagnose ==")
dg = post("/api/story/diagnose", story)
print("summary:", dg["summary"])
print("issues:", json.dumps(dg["issues"], ensure_ascii=False)[:300])

print("== save/load ==")
print(post("/api/stories", story))
loaded = get("/api/stories/" + sid)
assert loaded["title"] == story["title"], "读取不一致"
lst = get("/api/stories")
print("library:", json.dumps(lst, ensure_ascii=False)[:200])

print("\nALL PASS ✅")
