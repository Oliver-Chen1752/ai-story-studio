"""Ai故事工坊后端：Flask API + 本地 JSON 持久化。

接口：
  GET  /api/status                 前端据此显示"AI 模式 / 演示模式"
  POST /api/story/opening          由设定生成开篇
  POST /api/story/continue         续写后继节点
  POST /api/story/ending           生成结局
  POST /api/story/diagnose         结构诊断
  GET  /api/stories                作品列表
  GET  /api/stories/<sid>          读取作品
  POST /api/stories                新建/保存作品（整份覆盖）
"""
import json
import os
import re

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import story_engine as engine
from llm import llm_available, MODEL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, static_folder=None)
CORS(app)

_SAFE = re.compile(r"^[0-9a-f]{8,32}$")


def _path(sid):
    if not _SAFE.match(sid or ""):
        return None
    return os.path.join(DATA_DIR, f"{sid}.json")


# ------------------------------------------------------------------ AI 接口

@app.post("/api/story/opening")
def api_opening():
    story = request.get_json(force=True) or {}
    result = engine.generate_opening(story)
    return jsonify(result)


@app.post("/api/story/continue")
def api_continue():
    body = request.get_json(force=True) or {}
    story = body.get("story") or {}
    path = body.get("path") or []
    chosen = body.get("chosen_label") or ""
    result = engine.generate_continuation(story, path, chosen)
    return jsonify(result)


@app.post("/api/story/ending")
def api_ending():
    body = request.get_json(force=True) or {}
    result = engine.generate_ending(body.get("story") or {}, body.get("path") or [])
    return jsonify(result)


@app.post("/api/story/diagnose")
def api_diagnose():
    story = request.get_json(force=True) or {}
    return jsonify(engine.diagnose_structure(story))


@app.get("/api/status")
def api_status():
    return jsonify({
        "ai": llm_available(),
        "model": MODEL if llm_available() else "mock",
        "mode": "AI" if llm_available() else "DEMO",
    })


# ------------------------------------------------------------------ 持久化

@app.get("/api/stories")
def list_stories():
    out = []
    for fn in sorted(os.listdir(DATA_DIR), reverse=True):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(DATA_DIR, fn), encoding="utf-8") as f:
                d = json.load(f)
            out.append({
                "id": d.get("id"),
                "title": d.get("title") or "未命名",
                "nodes": len(d.get("nodes") or {}),
                "endings": sum(1 for n in (d.get("nodes") or {}).values() if n.get("is_ending")),
                "updated": d.get("updated"),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return jsonify(out)


@app.get("/api/stories/<sid>")
def get_story(sid):
    p = _path(sid)
    if not p or not os.path.exists(p):
        return jsonify({"error": "not found"}), 404
    with open(p, encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.post("/api/stories")
def save_story():
    story = request.get_json(force=True) or {}
    sid = story.get("id") or engine.new_id()
    story["id"] = sid
    p = _path(sid)
    if not p:
        return jsonify({"error": "bad id"}), 400
    with open(p, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    return jsonify({"id": sid, "ok": True})


@app.delete("/api/stories/<sid>")
def delete_story(sid):
    p = _path(sid)
    if p and os.path.exists(p):
        os.remove(p)
        return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


# ------------------------------------------------------------------ 静态托管（生产）

@app.route("/", defaults={"sub": ""})
@app.route("/<path:sub>")
def spa(sub):
    if os.path.isdir(DIST_DIR):
        full = os.path.join(DIST_DIR, sub)
        if sub and os.path.isfile(full):
            return send_from_directory(DIST_DIR, sub)
        return send_from_directory(DIST_DIR, "index.html")
    return jsonify({"hint": "前端未构建：开发模式请另起 vite，见 README"}), 200


if __name__ == "__main__":
    print(f"[分支工坊] AI 模式: {'DeepSeek:' + MODEL if llm_available() else 'DEMO(mock 生成器)'}")
    # host 0.0.0.0 + 读 PORT，兼容本地(默认5001)与 PaaS 部署
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=False)
