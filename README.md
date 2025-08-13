# John Assistant

A modular AI assistant I’m building **from scratch** to learn AI/ML daily and keep a steady GitHub streak.

## Logging
All chats are saved to `logs/history.jsonl` as JSONL, with a `session` id and timestamps.
Use this file later to fine-tune intent classifiers or build datasets.


## Run
```bash
pip install openai
# or: uv pip install openai
python assistant.py
