# parser.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv() 

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_install_command(user_input: str):
    """
    Use Groq LLM (gemma2-9b-it) to parse user input.
    Returns (intent, app, version) or None
    """

    prompt = f"""
    You are an intent parser for a software installation bot.
    Extract the intent, app name, and version from the following text:

    User input: "{user_input}"

    Respond in strict JSON format:
    {{
      "intent": "<intent or none>",
      "app": "<application name or none>",
      "version": "<version or latest>"
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    # Get LLM response text
    content = response.choices[0].message.content.strip()

    import json
    try:
        data = json.loads(content)
        if data.get("intent") == "install":
            return data["app"].lower(), data.get("version", "latest")
    except Exception as e:
        print("LLM parsing failed:", e, content)

    return None
