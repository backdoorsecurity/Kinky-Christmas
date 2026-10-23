#!/usr/bin/env python3
"""Transcribe audio with frozenlab/qwen3-asr running in local Ollama.

The model expects 16 kHz mono WAV, at most about 60 seconds per request, sent
base64-encoded in the chat message ``images`` field with an empty prompt.
Replies look like ``language English<asr_text>…``.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
ASR_MARK = "<asr_text>"
DEFAULT_MODEL = "frozenlab/qwen3-asr:latest"
DEFAULT_HOST = "http://127.0.0.1:11434"
# Accuracy is flat through 60s and drops off near 2 minutes.
MAX_WINDOW_S = 60.0


def die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_pcm(path: Path) -> bytes:
    if shutil.which("ffmpeg") is None:
        die("ffmpeg is required to decode audio, and it is not on PATH")
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        die(err or f"ffmpeg failed to read {path}")
    if not proc.stdout:
        die(f"no audio decoded from {path}")
    return proc.stdout


def wav_bytes(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm)
    return buf.getvalue()


def iter_windows(pcm: bytes, window_s: float) -> list[tuple[float, float, bytes]]:
    window_bytes = int(window_s * SAMPLE_RATE) * SAMPLE_WIDTH
    if window_bytes < SAMPLE_WIDTH:
        die("window must cover at least one sample")
    spans: list[tuple[float, float, bytes]] = []
    for start in range(0, len(pcm), window_bytes):
        piece = pcm[start : start + window_bytes]
        if not piece:
            continue
        t0 = start / (SAMPLE_RATE * SAMPLE_WIDTH)
        t1 = (start + len(piece)) / (SAMPLE_RATE * SAMPLE_WIDTH)
        spans.append((t0, t1, piece))
    return spans


def parse_reply(text: str) -> tuple[str | None, str]:
    """Split ``language English<asr_text>transcript`` into language and text."""
    if ASR_MARK not in text:
        return None, text.strip()
    pre, post = text.split(ASR_MARK, 1)
    language = None
    marker = "language "
    idx = pre.rfind(marker)
    if idx != -1:
        language = pre[idx + len(marker) :].strip() or None
    return language, post.strip()


def transcribe_wav(
    wav: bytes,
    *,
    model: str,
    host: str,
    timeout: float,
) -> str:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "messages": [
            {
                "role": "user",
                "content": "",
                "images": [base64.b64encode(wav).decode("ascii")],
            }
        ],
    }
    request = urllib.request.Request(
        host.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        die(f"Ollama returned HTTP {exc.code}: {detail or exc.reason}")
    except urllib.error.URLError as exc:
        die(
            f"could not reach Ollama at {host} ({exc.reason}). "
            "Start it with `ollama serve` if it is not already running."
        )
    except TimeoutError:
        die(f"Ollama did not respond within {timeout:.0f}s")

    message = body.get("message") or {}
    content = message.get("content") or ""
    if not content and message.get("thinking"):
        content = message["thinking"]
    if not isinstance(content, str) or not content.strip():
        die(f"Ollama returned an empty transcript: {json.dumps(body)[:500]}")
    return content


def transcribe_file(
    path: Path,
    *,
    model: str,
    host: str,
    window_s: float,
    timeout: float,
) -> dict:
    pcm = load_pcm(path)
    duration = len(pcm) / (SAMPLE_RATE * SAMPLE_WIDTH)
    # One request for clips that already fit. Longer audio is cut into windows
    # because quality falls off past about a minute.
    piece_s = duration if duration <= MAX_WINDOW_S else window_s
    spans = iter_windows(pcm, piece_s)

    segments = []
    languages: list[str] = []
    for index, (t0, t1, piece) in enumerate(spans, start=1):
        print(
            f"[{index}/{len(spans)}] {t0:.1f}s–{t1:.1f}s",
            file=sys.stderr,
            flush=True,
        )
        raw = transcribe_wav(
            wav_bytes(piece),
            model=model,
            host=host,
            timeout=timeout,
        )
        language, text = parse_reply(raw)
        if language:
            languages.append(language)
        segments.append(
            {
                "start": round(t0, 3),
                "end": round(t1, 3),
                "language": language,
                "text": text,
                "raw": raw,
            }
        )

    language = languages[0] if languages else None
    if languages and any(item != language for item in languages):
        language = None
    text = " ".join(segment["text"] for segment in segments if segment["text"]).strip()
    return {
        "model": model,
        "language": language,
        "duration": round(duration, 3),
        "text": text,
        "segments": segments,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="audio or video file to transcribe")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Ollama base URL (default: {DEFAULT_HOST})")
    parser.add_argument(
        "--window",
        type=float,
        default=30.0,
        help=f"chunk length in seconds for audio longer than {MAX_WINDOW_S:.0f}s (default: 30, max {MAX_WINDOW_S:.0f})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="per-request timeout in seconds (default: 300; the first call also loads the model)",
    )
    parser.add_argument("--json", action="store_true", help="print segments as JSON instead of plain text")
    parser.add_argument("--raw", action="store_true", help="print the model reply before stripping the language tag")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if not args.audio.is_file():
        die(f"file not found: {args.audio}")
    if not 0 < args.window <= MAX_WINDOW_S:
        die(f"--window must be between 0 and {MAX_WINDOW_S:.0f} seconds")

    result = transcribe_file(
        args.audio,
        model=args.model,
        host=args.host,
        window_s=args.window,
        timeout=args.timeout,
    )
    if args.json:
        if not args.raw:
            for segment in result["segments"]:
                segment.pop("raw", None)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    if args.raw:
        print("\n".join(segment["raw"] for segment in result["segments"]))
        return
    if result["language"]:
        print(f"language: {result['language']}", file=sys.stderr)
    print(result["text"])


if __name__ == "__main__":
    main()
