import { pyx13Talk } from "../src/pyx13-client.js";

const root = document.getElementById("pyx13-widget");
root.innerHTML = `
  <label for="pyx13-input"><strong>Ask AI</strong></label>
  <div id="pyx13-log" aria-live="polite"></div>
  <textarea id="pyx13-input" placeholder="Ask something..."></textarea>
  <button id="pyx13-send" type="button">Send</button>
`;

const log = document.getElementById("pyx13-log");
const input = document.getElementById("pyx13-input");
const send = document.getElementById("pyx13-send");

function addLine(prefix, text) {
  const div = document.createElement("div");
  div.textContent = `${prefix}: ${text}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

send.addEventListener("click", async () => {
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  addLine("You", q);
  send.disabled = true;
  try {
    const out = await pyx13Talk(q, "smart");
    addLine("Pyx", out || "(empty response)");
  } catch (e) {
    addLine("Error", e.message || String(e));
  } finally {
    send.disabled = false;
  }
});
