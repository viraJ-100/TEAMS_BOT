# parser.py
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv() 

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_install_command(user_input: str):
    """
    Use Groq LLM to parse any intent.
    Returns a dict: {intent, app, version, answer}
    - If intent == "install": contains app + version
    - If intent != "install": contains an answer (free-form text reply)
    """

    prompt = f"""
    You are an intent parser + responder for a software installation bot.
    - If the user is requesting to install software, extract app + version.
    - If the user is asking something general (not install), generate a helpful short answer.

    User input: "{user_input}"

    Respond in strict JSON format:
    {{
      "intent": "<install | greeting | smalltalk | question | other>",
      "app": "<application name or none>",
      "version": "<version or latest>",
      "answer": "<bot's response if not install, else empty string>"
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    content = response.choices[0].message.content.strip()

    # Clean markdown fences if LLM adds them
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()

    try:
        data = json.loads(content)
        return data
    except Exception as e:
        print("LLM parsing failed:", e, content)
        return {"intent": "other", "app": None, "version": None, "answer": "Sorry, I didn't understand that."}
