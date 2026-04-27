"""GGUF inference via llama-cpp-python."""

from __future__ import annotations

import os
import threading
from typing import Any, Iterator

_SYSTEM_BASE = """You are Pyx 1.3 Local, a helpful assistant running entirely on the user's device.
Be concise, accurate, and friendly. If you are given web search snippets, use them only as evidence;
answer in your own words — do not dump raw search results unless the user asks for links or quotes."""

_WEB_PREFIX = (
    "The following are web search snippets for grounding (not user-visible verbatim output).\n"
    "Synthesize a natural reply; cite site names when stating specific facts.\n\n--- Snippets ---\n"
)


class LocalLlama:
    def __init__(self, model_path: str) -> None:
        from llama_cpp import Llama

        n_ctx = int(os.environ.get("PYX13_N_CTX", "8192"))
        n_gpu = int(os.environ.get("PYX13_N_GPU_LAYERS", "0"))
        self._llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu,
            verbose=False,
        )
        self._lock = threading.Lock()

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        with self._lock:
            out = self._llm.create_chat_completion(
                messages=messages,
                temperature=max(0.05, min(temperature, 1.5)),
                max_tokens=max(16, min(max_tokens, 8192)),
            )
        choices = out.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        return (msg.get("content") or "").strip()

    def stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> Iterator[str]:
        with self._lock:
            stream = self._llm.create_chat_completion(
                messages=messages,
                temperature=max(0.05, min(temperature, 1.5)),
                max_tokens=max(16, min(max_tokens, 8192)),
                stream=True,
            )
            for chunk in stream:
                try:
                    delta = chunk["choices"][0]["delta"]
                    t = delta.get("content") or ""
                    if t:
                        yield t
                except (KeyError, IndexError, TypeError):
                    continue


def build_messages(
    history: list[dict[str, str]],
    user_message: str,
    *,
    web_context: str | None = None,
) -> list[dict[str, str]]:
    system = _SYSTEM_BASE
    if web_context and web_context.strip():
        system = _SYSTEM_BASE + "\n\n" + _WEB_PREFIX + web_context.strip()
    msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in history:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_message.strip()})
    return msgs


def load_engine(model_path: str | None) -> LocalLlama:
    path = (model_path or os.environ.get("PYX13_GGUF") or "").strip()
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(
            "Set PYX13_GGUF to a valid .gguf file path (or pass model_path)."
        )
    return LocalLlama(path)
