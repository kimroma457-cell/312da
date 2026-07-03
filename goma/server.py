import os
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from . import engine
from . import identity as identity_module
from . import memory
from . import reflect as reflect_module

REFLECT_EVERY = 6

app = Flask(__name__)
_lock = threading.Lock()


def _identity_summary(identity):
    return {
        "growth_stage": identity["growth_stage"],
        "personality_traits": identity["personality_traits"],
        "values": identity["values"],
        "interaction_count": identity["interaction_count"],
        "reflection_count": identity["reflection_count"],
    }


def _run_reflection(identity):
    entries = memory.recent_memory(limit=30)
    context = memory.format_memory_context(entries)
    eligible = identity_module.is_eligible_to_grow(identity)
    result = reflect_module.run_reflection(identity, context, eligible)

    identity["reflection_count"] += 1
    identity["last_reflection_at"] = datetime.now(timezone.utc).isoformat()

    summary = reflect_module.apply_reflection(identity, result, eligible)
    identity_module.save(identity)
    return summary


@app.route("/status", methods=["GET"])
def status():
    with _lock:
        identity = identity_module.load()
        return jsonify(_identity_summary(identity))


@app.route("/journal", methods=["GET"])
def journal():
    creations = memory.recent_creations(limit=10)
    return jsonify(
        [{"type": c["type"], "content": c["content"], "timestamp": c["timestamp"]} for c in creations]
    )


@app.route("/reflect", methods=["POST"])
def reflect_endpoint():
    with _lock:
        identity = identity_module.load()
        summary = _run_reflection(identity)
        return jsonify({"summary": summary, "identity": _identity_summary(identity)})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message가 비어 있습니다."}), 400

    with _lock:
        identity = identity_module.load()
        entries = memory.recent_memory(limit=20)
        context = memory.format_memory_context(entries)

        try:
            reply = engine.chat(identity, context, message)
        except Exception as e:
            return jsonify({"error": str(e)}), 502

        memory.append_memory("user", message)
        memory.append_memory("goma", reply)
        identity["interaction_count"] += 1
        identity_module.save(identity)

        reflection_summary = None
        if identity["interaction_count"] % REFLECT_EVERY == 0:
            reflection_summary = _run_reflection(identity)

        return jsonify(
            {
                "reply": reply,
                "identity": _identity_summary(identity),
                "reflection": reflection_summary,
            }
        )


def main():
    host = os.environ.get("GOMA_HOST", "0.0.0.0")
    port = int(os.environ.get("GOMA_PORT", "8765"))
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
