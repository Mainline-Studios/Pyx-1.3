# Pyx-1.3-Template-UI

Optional **browser UI** for [Pyx-AI-Downloadable](../Pyx-AI-Downloadable). No build step — static HTML/JS.

## Run local AI server first

From `Pyx-AI-Downloadable`:

```bash
export PYX13_GGUF="/path/to/your/model.gguf"
python run_server.py
```

Default API: `http://127.0.0.1:8767`

## Open the template

Because browsers restrict `file://` fetches, serve this folder:

```bash
cd Pyx-1.3-Template-UI
python3 -m http.server 8080
```

Then open `http://127.0.0.1:8080/`

Edit `config.js` if you changed `PYX13_HOST` / `PYX13_PORT`.

## Features

- **Session memory** (server-side + stable `session_id` in `localStorage`)
- **Web search** toggle + **auto** (DDG HTML, no API keys) — model still **generates** the reply
- **Streaming** tokens
- **Export** conversation JSON
- **Reset** session

## Embed in your site

Copy `index.html`, `styles.css`, `app.js`, and `config.js` into your project and point `PYX13_API_BASE` at your running local server (same machine or tunnel).
