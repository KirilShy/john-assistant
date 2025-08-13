# John Assistant

A modular AI assistant I’m building **from scratch** to learn AI/ML daily and keep a steady GitHub streak.  
Supports multi-turn chat, GUI, voice input (Whisper), and natural TTS (ElevenLabs). Answers are short by design.

---

## Quick Start

```bash
# Python 3.10+ recommended. Using uv:
uv venv && . .venv/Scripts/activate    # Windows
# or: source .venv/bin/activate        # macOS/Linux
uv pip install openai elevenlabs sounddevice scipy
```

Create `config.json`:
```json
{
  "OPENAI_API_KEY": "sk-***",
  "ELEVEN_API_KEY": "eleven-***",
  "MODEL": "gpt-5-nano",
  "SPEAK": true
}
```

Create `system_prompt.txt` (short answers):
```
You are John, a friendly, concise personal assistant for an 18-year-old AI/ML learner.
- Default to 1–2 short sentences.
- If listing, use ≤3 bullets.
- Be direct; tiny follow-ups only if useful.
```

Run (CLI):
```bash
python assistant.py
```

Run (GUI):
```bash
python gui.py
```

> **Windows TTS note:** For ElevenLabs playback, install ffmpeg (e.g. `winget install --id=Gyan.FFmpeg -e`), or switch to a fallback that saves MP3s.

---

## Features

- **LLM chat loop** (multi-turn, trimmed context; model: `gpt-5-nano`)
- **GUI** (Tkinter) with a **non-blocking** UX (LLM + TTS on background threads)
- **Voice input** (mic → Whisper) via a **🎤 Talk** button (adjustable duration)
- **Natural TTS** via **ElevenLabs** (toggle Speak on/off)
- **Hot-reload** of `config.json` and `system_prompt.txt` from the GUI
- **Logging**: JSONL chat history with session IDs & UTC timestamps

---

## GUI Guide

- **Top bar:**  
  - **Model** label  
  - **Speak** toggle  
  - **Mic (s)** slider (2–15s)  
  - **🎤 Talk** (record & transcribe)  
  - **Reload** (re-read config & prompt)  
  - **Clear** (reset chat)  
  - **Save** (markdown transcript in `logs/`)

- **Status line:** shows `idle / listening… / thinking…`

---

## Project Layout

```
.
├─ assistant.py          # CLI (text + optional voice)
├─ gui.py                # GUI (threaded LLM/TTS; mic button)
├─ system_prompt.txt     # persona (short answers)
├─ config.json           # keys & settings (ignored in git)
├─ src/
│  └─ john/
│     ├─ __init__.py
│     └─ core.py        # shared logic: ask_llm, say, record/transcribe, reload
└─ logs/
   ├─ history.jsonl     # chat logs (JSONL)
   └─ transcript-*.md   # saved sessions
```

---

## Logging

- Chats append to `logs/history.jsonl`:
  - one JSON per line with `session`, `role`, `content`, `ts`
- Use these logs later to build datasets or fine-tune small components.

---