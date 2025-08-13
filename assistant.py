import json
from openai import OpenAI

# Load API key from config.json
with open("config.json", "r") as f:
    config = json.load(f)

client = OpenAI(api_key=config["OPENAI_API_KEY"])

def ask_llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content

def main():
    user_text = input("You: ")
    reply = ask_llm(user_text)
    print(f"John: {reply}")

if __name__ == "__main__":
    main()
