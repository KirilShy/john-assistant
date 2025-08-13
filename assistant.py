import json, os, uuid
from datetime import datetime, UTC
from openai import OpenAI
from elevenlabs import ElevenLabs, play
import sounddevice as sd
from scipy.io.wavfile import write

# --- load config (key + model) ---
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

client = OpenAI(api_key=cfg["OPENAI_API_KEY"])
MODEL = cfg.get("MODEL", "gpt-5-nano")
SPEAK = bool(cfg.get("SPEAK", False))

# --- load system prompt ---
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# --- init ElevenLabs ---
eleven = ElevenLabs(api_key=cfg.get("ELEVEN_API_KEY"))

def say(text: str):
    if not SPEAK or not cfg.get("ELEVEN_API_KEY"):
        return
    try:
        audio = eleven.text_to_speech.convert(
            voice_id="kqVT88a5QfII1HNAEPTJ",  # pick any from your ElevenLabs dashboard
            model_id="eleven_multilingual_v2",
            text=text
        )
        play(audio)
    except Exception as e:
        print(f"[TTS error] {e}")


# --- logging helpers ---
LOG_DIR = "logs"
HISTORY_PATH = os.path.join(LOG_DIR, "history.jsonl")

def _ensure_logs():
    os.makedirs(LOG_DIR, exist_ok=True)

def log_event(event: dict):
    """Append one JSON object (with auto ts) to logs/history.jsonl."""
    _ensure_logs()
    event = {**event, "ts": datetime.now(UTC).isoformat()}
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")   

# --- LLM call ---
def ask_llm(messages: list[dict]) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_completion_tokens=400,       # GPT-5 Nano uses this (not max_tokens)
        reasoning_effort="minimal"       # cheap/fast
    )
    return resp.choices[0].message.content

def record_audio(filename="input.wav", duration=5, samplerate=16000):
    """Record audio from the mic and save as WAV."""
    print(f"[Recording for {duration} seconds...]")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    write(filename, samplerate, audio)
    print("[Recording complete]")
    return filename

def transcribe_audio(path: str) -> str:
    """Send audio file to OpenAI Whisper and return text."""
    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",  # cheap + accurate
            file=f
        )
    return transcript.text.strip()

def chat_loop():
    print("John is ready. Type 'exit' to quit.")
    session = uuid.uuid4().hex

    # seed with system prompt, and log it
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    log_event({"session": session, "role": "system", "content": SYSTEM_PROMPT, "model": MODEL})

    while True:
        choice = input("Type your message or press Enter to talk: ").strip()
        if choice == "":
            wav_path = record_audio(duration=5)  # record 5 seconds
            user_text = transcribe_audio(wav_path)
            print(f"You (voice): {user_text}")
        else:
            user_text = choice
        if user_text.lower() in {"exit", "quit", "q"}:
            print("John: Bye!")
            log_event({"session": session, "role": "meta", "event": "end"})
            break

        messages.append({"role": "user", "content": user_text})
        log_event({"session": session, "role": "user", "content": user_text})

        # keep costs low: trim old turns (keep system + last ~14)
        if len(messages) > 16:
            messages = [messages[0]] + messages[-14:]

        reply = ask_llm(messages)
        messages.append({"role": "assistant", "content": reply})
        log_event({"session": session, "role": "assistant", "content": reply, "model": MODEL})
        print(f"John: {reply}")
        say(reply)  # speak the reply if enable

def main():
    chat_loop()

if __name__ == "__main__":
    main()
