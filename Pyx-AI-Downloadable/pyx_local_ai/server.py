"""HTTP API for local chat — no external LLM APIs."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from flask import Flask, Response, jsonify, request, stream_with_context

from pyx_local_ai.engine import build_messages, load_engine
from pyx_local_ai.sessions import SessionStore
from pyx_local_ai.web_search import fetch_snippets, should_auto_search

_sessions = SessionStore()
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = load_engine(None)
    return _engine


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def _cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    @app.route("/health")
    def health():
        gguf = os.environ.get("PYX13_GGUF", "")
        ok = bool(gguf and os.path.isfile(gguf))
        return jsonify(
            {
                "status": "ok" if ok else "no_model",
                "local_ai": True,
                "model_configured": ok,
                "model_path": gguf if ok else None,
            }
        )

    @app.route("/chat", methods=["POST", "OPTIONS"])
    def chat():
        if request.method == "OPTIONS":
            return Response(status=204)
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message is required"}), 400

        use_web = bool(data.get("use_web"))
        use_web_auto = bool(data.get("use_web_auto"))
        stream = bool(data.get("stream"))
        temperature = float(data.get("temperature") or 0.7)
        max_tokens = int(data.get("max_tokens") or 512)

        do_web = use_web or (use_web_auto and should_auto_search(message))
        web_meta: dict[str, Any] = {
            "used": do_web,
            "provider": None,
            "error": None,
            "query": None,
        }
        web_context = ""
        if do_web:
            web_meta["query"] = message[:500]
            snippets, provider, werr = fetch_snippets(message)
            web_meta["provider"] = provider
            web_meta["error"] = werr
            if snippets:
                web_context = snippets
            elif werr:
                web_context = f"(Search note: {werr})"

        sid, sess = _sessions.get_or_create(data.get("session_id"))
        history = sess.snapshot()

        try:
            eng = get_engine()
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 503

        msgs = build_messages(history, message, web_context=web_context if web_context else None)

        if stream:

            def gen():
                buf: list[str] = []
                try:
                    for piece in eng.stream(
                        msgs, temperature=temperature, max_tokens=max_tokens
                    ):
                        buf.append(piece)
                        yield f"data: {json.dumps({'token': piece})}\n\n"
                except Exception as ex:
                    yield f"data: {json.dumps({'error': str(ex)})}\n\n"
                    return
                full_reply = "".join(buf).strip()
                sess.append("user", message)
                sess.append("assistant", full_reply)
                yield f"data: {json.dumps({'done': True, 'session_id': sid, 'web': web_meta})}\n\n"
                yield "data: [DONE]\n\n"

            return Response(
                stream_with_context(gen()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                },
            )

        try:
            reply = eng.complete(msgs, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        sess.append("user", message)
        sess.append("assistant", reply)
        return jsonify(
            {
                "reply": reply,
                "session_id": sid,
                "web": web_meta,
                "history_len": len(sess.snapshot()),
            }
        )

    @app.route("/session/reset", methods=["POST", "OPTIONS"])
    def session_reset():
        if request.method == "OPTIONS":
            return Response(status=204)
        data = request.get_json(silent=True) or {}
        sid = (data.get("session_id") or "").strip()
        if not sid:
            return jsonify({"error": "session_id required"}), 400
        ok = _sessions.reset(sid)
        return jsonify({"ok": ok})

    @app.route("/session/export", methods=["GET"])
    def session_export():
        sid = (request.args.get("session_id") or "").strip()
        if not sid:
            return jsonify({"error": "session_id required"}), 400
        msgs = _sessions.export(sid)
        if msgs is None:
            return jsonify({"error": "unknown session"}), 404
        return jsonify({"session_id": sid, "messages": msgs})

    return app


def main() -> None:
    host = os.environ.get("PYX13_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PYX13_PORT", "8767"))
    except ValueError:
        port = 8767

    if not os.environ.get("PYX13_GGUF"):
        print("ERROR: Set PYX13_GGUF to your .gguf file path.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(os.environ["PYX13_GGUF"]):
        print(f"ERROR: PYX13_GGUF file not found: {os.environ['PYX13_GGUF']}", file=sys.stderr)
        sys.exit(1)

    app = create_app()
    print(f"Pyx 1.3 local AI — http://{host}:{port}")
    print("  POST /chat  |  GET /health  |  GET /session/export")
    app.run(host=host, port=port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
