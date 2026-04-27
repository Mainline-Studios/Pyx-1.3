(function () {
  var API = window.PYX13_API_BASE || "http://127.0.0.1:8767";
  var SESSION_KEY = "pyx13_session_id";

  var logEl = document.getElementById("log");
  var inputEl = document.getElementById("input");
  var sendEl = document.getElementById("send");
  var statusEl = document.getElementById("status");
  var useWebEl = document.getElementById("useWeb");
  var useWebAutoEl = document.getElementById("useWebAuto");
  var useStreamEl = document.getElementById("useStream");
  var tempEl = document.getElementById("temperature");
  var maxTokEl = document.getElementById("maxTokens");
  var btnReset = document.getElementById("btnReset");
  var btnExport = document.getElementById("btnExport");

  function sessionId() {
    var s = localStorage.getItem(SESSION_KEY);
    if (!s) {
      s = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(SESSION_KEY, s);
    }
    return s;
  }

  function addBubble(role, text) {
    var div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "bot");
    var r = document.createElement("div");
    r.className = "role";
    r.textContent = role === "user" ? "You" : "Pyx 1.3";
    div.appendChild(r);
    var body = document.createElement("div");
    body.textContent = text;
    div.appendChild(body);
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
    return body;
  }

  function postJson(path, body) {
    return fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  function sendNonStream(msg) {
    statusEl.textContent = "Thinking…";
    sendEl.disabled = true;
    return postJson("/chat", {
      message: msg,
      session_id: sessionId(),
      use_web: useWebEl.checked,
      use_web_auto: useWebAutoEl.checked,
      stream: false,
      temperature: parseFloat(tempEl.value) || 0.7,
      max_tokens: parseInt(maxTokEl.value, 10) || 512,
    })
      .then(function (res) {
        return res.json().then(function (j) {
          if (!res.ok) throw new Error(j.error || "HTTP " + res.status);
          return j;
        });
      })
      .then(function (j) {
        addBubble("assistant", j.reply || "");
        if (j.web && j.web.used) {
          statusEl.textContent = j.web.error
            ? "Web: " + j.web.error
            : "Web context used · " + (j.web.provider || "ok");
        } else {
          statusEl.textContent = "Ready";
        }
      })
      .catch(function (e) {
        statusEl.textContent = String(e.message || e);
        addBubble("assistant", "Error: " + (e.message || e));
      })
      .finally(function () {
        sendEl.disabled = false;
      });
  }

  function sendStream(msg) {
    statusEl.textContent = "Generating…";
    sendEl.disabled = true;
    var bodyEl = addBubble("assistant", "");

    return fetch(API + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: msg,
        session_id: sessionId(),
        use_web: useWebEl.checked,
        use_web_auto: useWebAutoEl.checked,
        stream: true,
        temperature: parseFloat(tempEl.value) || 0.7,
        max_tokens: parseInt(maxTokEl.value, 10) || 512,
      }),
    })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (j) {
            throw new Error(j.error || "HTTP " + res.status);
          });
        }
        var reader = res.body.getReader();
        var dec = new TextDecoder();
        var buf = "";

        function pump() {
          return reader.read().then(function (chunk) {
            if (chunk.done) {
              sendEl.disabled = false;
              statusEl.textContent = "Ready";
              return;
            }
            buf += dec.decode(chunk.value, { stream: true });
            var lines = buf.split("\n");
            buf = lines.pop() || "";
            for (var i = 0; i < lines.length; i++) {
              var line = lines[i].trim();
              if (!line.startsWith("data:")) continue;
              var payload = line.slice(5).trim();
              if (payload === "[DONE]") continue;
              try {
                var obj = JSON.parse(payload);
                if (obj.token) bodyEl.textContent += obj.token;
                if (obj.error) throw new Error(obj.error);
                if (obj.done && obj.web) {
                  statusEl.textContent = obj.web.error
                    ? "Web: " + obj.web.error
                    : "Web context used · " + (obj.web.provider || "ok");
                }
              } catch (e) {
                if (e instanceof SyntaxError) continue;
                throw e;
              }
            }
            logEl.scrollTop = logEl.scrollHeight;
            return pump();
          });
        }
        return pump();
      })
      .catch(function (e) {
        statusEl.textContent = String(e.message || e);
        bodyEl.textContent += "\n[Error: " + (e.message || e) + "]";
        sendEl.disabled = false;
      });
  }

  function send() {
    var text = (inputEl.value || "").trim();
    if (!text) return;
    inputEl.value = "";
    addBubble("user", text);
    if (useStreamEl.checked) {
      sendStream(text);
    } else {
      sendNonStream(text);
    }
  }

  sendEl.addEventListener("click", send);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      send();
    }
  });

  btnReset.addEventListener("click", function () {
    var sid = sessionId();
    postJson("/session/reset", { session_id: sid })
      .then(function () {
        localStorage.removeItem(SESSION_KEY);
        logEl.innerHTML = "";
        statusEl.textContent = "New session";
      })
      .catch(function () {
        localStorage.removeItem(SESSION_KEY);
        logEl.innerHTML = "";
        statusEl.textContent = "New session (reset may have failed if server down)";
      });
  });

  btnExport.addEventListener("click", function () {
    var sid = sessionId();
    fetch(API + "/session/export?session_id=" + encodeURIComponent(sid))
      .then(function (r) {
        return r.json();
      })
      .then(function (j) {
        if (!j.messages) throw new Error(j.error || "export failed");
        var blob = new Blob([JSON.stringify(j.messages, null, 2)], {
          type: "application/json",
        });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "pyx13-chat-export.json";
        a.click();
        URL.revokeObjectURL(a.href);
        statusEl.textContent = "Exported";
      })
      .catch(function (e) {
        statusEl.textContent = String(e.message || e);
      });
  });

  fetch(API + "/health")
    .then(function (r) {
      return r.json();
    })
    .then(function (j) {
      if (j.status === "ok") {
        statusEl.textContent = "Connected · local model loaded";
      } else {
        statusEl.textContent = "Server up but PYX13_GGUF missing — check server";
      }
    })
    .catch(function () {
      statusEl.textContent = "Cannot reach " + API + " — start run_server.py";
    });
})();
