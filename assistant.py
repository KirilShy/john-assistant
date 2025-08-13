import json, os, uuid
from openai import OpenAI
from datetime import datetime, UTC

# --- load config (key + model) ---
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

client = OpenAI(api_key=cfg["OPENAI_API_KEY"])
MODEL = cfg.get("MODEL", "gpt-5-nano")

# --- John’s persona (system prompt) ---
SYSTEM_PROMPT = (
    "You are John, a friendly, concise personal assistant for an 18-year-old "
    "AI/ML learner. Be encouraging, practical, and brief unless asked for detail."
)

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

def chat_loop():
    print("John is ready. Type 'exit' to quit.")
    session = uuid.uuid4().hex

    # seed with system prompt, and log it
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    log_event({"session": session, "role": "system", "content": SYSTEM_PROMPT, "model": MODEL})

    while True:
        user_text = input("You: ").strip()
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

def main():
    chat_loop()

if __name__ == "__main__":
    main()
