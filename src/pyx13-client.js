import { PYX13_CONFIG } from "./pyx13-config.js";

export async function pyx13Talk(message, mode = "smart") {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), PYX13_CONFIG.timeoutMs);
  try {
    const res = await fetch(
      `${PYX13_CONFIG.apiBase}${PYX13_CONFIG.talkEndpoint}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          messages: [{ role: "user", content: message }],
        }),
        signal: ctrl.signal,
      }
    );
    const j = await res.json();
    if (!res.ok) throw new Error(j.error || `HTTP ${res.status}`);
    return j.reply || "";
  } finally {
    clearTimeout(t);
  }
}
