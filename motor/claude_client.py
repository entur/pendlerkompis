"""Kaller Claude CLI for å generere Kontrakt B fra en prompt."""

from __future__ import annotations

import json
import re
import subprocess
import sys


def call_claude(prompt: str, verbose: bool = False) -> dict:
    """Send prompt til Claude og returner Kontrakt B som dict.

    Bruker 'claude -p' (print-modus) som benytter eksisterende Claude Code-autentisering.
    """
    if verbose:
        print("[motor] Sender prompt til Claude...", file=sys.stderr)

    result = subprocess.run(
        [
            "claude",
            "-p", prompt,
            "--output-format", "json",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI feilet (exit {result.returncode}):\n"
            f"stdout: {result.stdout[:500]}\n"
            f"stderr: {result.stderr[:500]}"
        )

    # --output-format json gir: {"type":"result","result":"<tekst>","cost_usd":...}
    try:
        wrapper = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Kunne ikke parse Claude CLI-output: {e}\n{result.stdout[:500]}")

    raw_text = wrapper.get("result", "")

    if verbose:
        print(f"[motor] Claude svarte ({len(raw_text)} tegn)", file=sys.stderr)

    return _extract_json(raw_text)


def _extract_json(text: str) -> dict:
    """Trekk ut JSON-objekt fra tekst (håndterer markdown-kodeblokker)."""
    # Prøv ren parsing først
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown-kodeblokk
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Finn første { ... } i teksten
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return json.loads(text[start:end])

    raise ValueError(f"Fant ingen gyldig JSON i Claude-svaret:\n{text[:500]}")
