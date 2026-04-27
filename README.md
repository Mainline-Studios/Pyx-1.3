# Pyx 1.3

**Local-first AI starter** — no Groq, no cloud API keys. You run a **GGUF** model on your own hardware and optionally ground answers with **DuckDuckGo HTML** search (no search API key). The assistant always responds with **generated text**; web results are context only.

## What’s in this repo

| Folder | Purpose |
|--------|---------|
| **`Pyx-AI-Downloadable/`** | Python server: chat API, session memory, web snippets → model, streaming. |
| **`Pyx-1.3-Template-UI/`** | Ready-made browser UI (optional). |

## Quick start

1. **Download a GGUF** chat model (your choice) and note the path.
2. **Install & run the server** — see [Pyx-AI-Downloadable/README.md](Pyx-AI-Downloadable/README.md).
3. **Optional UI** — see [Pyx-1.3-Template-UI/README.md](Pyx-1.3-Template-UI/README.md).

## ZIP download

- [Download repository ZIP](https://github.com/Mainline-Studios/Pyx-1.3/archive/refs/heads/main.zip)

Copy `Pyx-AI-Downloadable/` into your project, add your own UI, or use the template.

## Requirements

- Python 3.10+
- `llama-cpp-python` + a **.gguf** file (see downloadable README)
- Internet only if you enable **web search** in the UI/API

## Differences from Pyx 1.0 (pyx-ai site)

The public **pyx-ai** site remains **Groq / cloud** Pyx 1.0. **Pyx 1.3** in this repo is **offline-capable** local inference only.

## License

Specify in your downstream project; starter code is provided as-is for integration.
