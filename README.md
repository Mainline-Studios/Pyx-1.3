# Pyx 1.3 (Starter)

Pyx 1.3 is a separate starter kit for building UI + AI features into your own app.

## Download ZIP

- [Download ZIP](https://github.com/Mainline-Studios/Pyx-1.3/archive/refs/heads/main.zip)

## What this repo is

- A minimal, clean starting point.
- Drop-in UI files (`ui/`) for a simple "ask AI" panel.
- A tiny client helper (`src/pyx13-client.js`) you can copy into your codebase.
- No local Llama / OSS runtime in this starter.

## Quick start

1. Open `ui/index.html`.
2. Set your API base URL in `src/pyx13-config.js`.
3. Wire the client into your own project.

## Integrate into existing app

Copy these pieces:

- `src/pyx13-client.js`
- `src/pyx13-config.js`
- optional UI: `ui/pyx13-widget.css` and `ui/pyx13-widget.js`

Then mount the widget:

```html
<div id="pyx13-widget"></div>
<script type="module" src="./ui/pyx13-widget.js"></script>
```

## Notes

- Current production site remains Pyx 1.0 cloud flows.
- Pyx 1.3 implementation details will be added incrementally.
