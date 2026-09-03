"""DeepSeek API 客户端：真实调用 + 无 key 时自动降级为本地 mock 生成器（演示模式）。"""
import json
import os
import re
import urllib.request
import urllib.error


def _load_dotenv(path):
    """极简 .env 解析，避免额外依赖。"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
# v4-flash 默认开启思考链，推理 token 计费高且慢；关掉可省 2~3 倍输出费用。
THINKING = os.environ.get("DEEPSEEK_THINKING", "disabled").strip().lower()


def llm_available():
    return bool(API_KEY) and not API_KEY.startswith("sk-xxxx")


class LLMError(Exception):
    pass


def chat_json(system_prompt, user_prompt, temperature=1.0, retries=1):
    """调用 DeepSeek 并解析 JSON 输出；失败重试 retries 次。"""
    if not llm_available():
        raise LLMError("LLM 未配置")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        # 思考链会占用该预算，故留足余量，避免正文被截断成非法 JSON
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }
    if THINKING != "enabled":
        payload["thinking"] = {"type": "disabled"}
    body = json.dumps(payload).encode("utf-8")
    last_err = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            # 显式识别截断，避免把半截 JSON 当成"内容"返回
            if choice.get("finish_reason") == "length":
                raise LLMError("输出被 max_tokens 截断")
            return _parse_json_loose(choice["message"]["content"])
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, IndexError, LLMError) as e:
            last_err = e
    raise LLMError(f"LLM 调用失败: {last_err}")


def _parse_json_loose(text):
    """容忍模型输出包裹 ```json 围栏的情况。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    return json.loads(text)
