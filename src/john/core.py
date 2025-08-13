# src/john/core.py
import json
from openai import OpenAI
from elevenlabs import ElevenLabs, play

import sounddevice as sd
from scipy.io.wavfile import write

# --- Load config ---
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

client = OpenAI(api_key=cfg["OPENAI_API_KEY"])
MODEL = cfg.get("MODEL", "gpt-5-nano")
SPEAK = bool(cfg.get("SPEAK", False))

# --- Load system prompt ---
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# --- Init ElevenLabs ---
eleven = ElevenLabs(api_key=cfg.get("ELEVEN_API_KEY"))

def say(text: str):
    """Speak text using ElevenLabs if SPEAK=True in config."""
    if not SPEAK or not cfg.get("ELEVEN_API_KEY"):
        return
    try:
        audio = eleven.text_to_speech.convert(
            voice_id="Cb8NLd0sUB8jI4MW2f9M",  # change to your voice ID
            model_id="eleven_multilingual_v2",
            text=text
        )
        play(audio)
    except Exception as e:
        print(f"[TTS error] {e}")

def ask_llm(messages: list[dict]) -> str:
    """Send chat history to the LLM and return its reply."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_completion_tokens=400,
        reasoning_effort="minimal"
    )
    return resp.choices[0].message.content

def get_system_prompt():
    return SYSTEM_PROMPT

def get_model():
    return MODEL

def record_audio(filename="input.wav", duration=5, samplerate=16000):
    """Record audio from the mic and save as WAV."""
    print(f"[Recording for {duration} seconds...]")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    write(filename, samplerate, audio)
    print("[Recording complete]")
    return filename

def transcribe_audio(path: str) -> str:
    """Send audio file to OpenAI Whisper and return text."""
    with open(path, "rb") as f:
        tr = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
        )
    return tr.text.strip()
# --- runtime toggles & reloads ---

def get_speak() -> bool:
    return SPEAK

def set_speak(flag: bool) -> None:
    global SPEAK
    SPEAK = bool(flag)

def reload_config() -> dict:
    """
    Re-read config.json and system_prompt.txt at runtime.
    Returns a small dict with current settings for the UI.
    """
    global cfg, client, MODEL, SPEAK, SYSTEM_PROMPT, eleven
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    client = OpenAI(api_key=cfg["OPENAI_API_KEY"])
    MODEL = cfg.get("MODEL", "gpt-5-nano")
    SPEAK = bool(cfg.get("SPEAK", False))
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
    eleven = ElevenLabs(api_key=cfg.get("ELEVEN_API_KEY"))
    return {"model": MODEL, "speak": SPEAK}

