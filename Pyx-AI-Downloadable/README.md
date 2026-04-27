# Pyx-AI-Downloadable (local chatbot core)

**No cloud APIs. No API keys. No Groq.** This is a small Python server that runs a **GGUF** model on your machine, keeps **conversation memory**, and can optionally **ground replies** using the same **DuckDuckGo HTML** search flow as Pyx Talk (snippets are context only — the model still **writes** the answer).

## Requirements

- Python 3.10+
- A **GGUF** chat model on disk (e.g. Llama-3, Qwen, Mistral — your choice)
- Network only if you enable web search (DDG HTML; no search API key)

## Install

```bash
cd Pyx-AI-Downloadable
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If `llama-cpp-python` fails to install, follow the [official install hints](https://github.com/abetlen/llama-cpp-python) for your platform (Metal/CUDA/CPU).

## Configure

| Env var | Meaning |
|--------|---------|
| `PYX13_GGUF` | **Required.** Path to your `.gguf` file. |
| `PYX13_HOST` | Bind address (default `127.0.0.1`). |
| `PYX13_PORT` | Port (default `8767`). |
| `PYX13_N_CTX` | Context size (default `8192`). |
| `PYX13_N_GPU_LAYERS` | GPU layers for llama.cpp (`-1` = try all, default `0` CPU). |
| `PYX13_MAX_HISTORY` | Max prior turns stored per session (default `40`). |

## Run

```bash
export PYX13_GGUF="$HOME/models/your-model.Q4_K_M.gguf"
python run_server.py
```

Health check: `GET http://127.0.0.1:8767/health`

## API

### `POST /chat` (JSON)

```json
{
  "message": "What is Rust?",
  "session_id": "optional-stable-id",
  "use_web": false,
  "use_web_auto": true,
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 512
}
```

Response:

```json
{
  "reply": "...",
  "session_id": "...",
  "web": { "used": false, "provider": null, "error": null, "query": null },
  "history_len": 3
}
```

### `POST /chat` (streaming)

Same body with `"stream": true`. Returns **SSE** (`text/event-stream`): lines `data: {"token":"..."}` then `data: [DONE]`.

### `POST /session/reset`

Body: `{ "session_id": "..." }` — clears server-side memory for that session.

### `GET /session/export?session_id=...`

Returns full message list for that session (JSON).

## Embed in your app

1. Run this server alongside your site or desktop app.
2. Call `/chat` from your UI (see `../Pyx-1.3-Template-UI` for a ready-made page).
3. Style and host your UI anywhere; this folder is **backend only**.

## License

Use under the same terms as the parent Pyx-1.3 repository.
