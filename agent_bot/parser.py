import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _bulletize(text: str) -> str:
    """
    Normalize any free-form text into bullet points where each line starts with '- '.
    Formatting-only; does not change core parsing behaviors.
    """
    if not text or not text.strip():
        return ""
    raw = text.strip()

    # Split into non-empty lines
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    # If it already looks like bullets, normalize the bullet marker to "- "
    if lines and all(ln[:1] in ("-", "*", "•") for ln in lines):
        return "\n".join("- " + ln.lstrip("-*• ").strip() for ln in lines)

    # Otherwise, split by sentences and bulletize
    import re
    sentences = re.split(r'(?<=[.!?])\s+', raw)
    sentences = [s.strip() for s in sentences if s.strip()]
    return "\n".join(f"- {s}" for s in sentences)


def _fix_common_json_breaks(raw: str) -> str:
    """
    Repairs a common LLM failure mode where `"answer"` is emitted as multiple
    consecutive JSON strings on separate lines, e.g.:

      "answer": "- line 1"
        "- line 2"
        "- line 3"

    This merges them into a single JSON string with '\\n' separators.
    If nothing to fix, returns the original `raw`.
    """
    try:
        # Fast path: already valid
        json.loads(raw)
        return raw
    except Exception:
        pass

    lines = raw.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '"answer"' in line and ':' in line:
            # We found the "answer": field. Try to gather broken bullet lines that follow.
            out_before = []
            out_after = []
            # Split only on the first occurrence to keep the rest of the line intact
            prefix, after = line.split('"answer"', 1)
            out_before.append(prefix + '"answer"')  # keep the key as-is

            # Ensure we are at the colon and the value begins
            if ':' not in after:
                # Can't confidently fix; emit original and continue
                out.append(line)
                i += 1
                continue

            key_rest = after.split(':', 1)
            out_before[-1] += ':' + key_rest[0]  # preserve spacing between key and colon if any
            value_part = key_rest[1]

            # If value starts with a quote, start collecting lines until we hit a comma
            # or a line that looks like the next JSON field.
            value_accum = None

            def _strip_wrapping_quotes(s: str) -> str:
                s = s.strip()
                if s.startswith('"') and s.endswith('"') and len(s) >= 2:
                    return s[1:-1]
                return s

            # First piece on the same line as "answer":
            value_part_stripped = value_part.strip()

            if value_part_stripped.startswith('"'):
                # Extract the part inside this line's quotes (if closed),
                # otherwise we take it as the initial fragment.
                # We'll treat this permissively and just strip the outer quotes if present.
                first_piece = _strip_wrapping_quotes(value_part_stripped.rstrip(','))
                value_accum = [first_piece] if first_piece != '' else []

                # Now try to consume subsequent lines that look like: " - something "
                j = i + 1
                while j < len(lines):
                    nxt = lines[j].strip()
                    # A "broken" bullet line typically is a full JSON string line:
                    #   "- something"
                    # wrapped in quotes:      " - something "
                    if (
                        len(nxt) >= 2
                        and nxt.startswith('"')
                        and nxt.endswith('"')
                        and _strip_wrapping_quotes(nxt).lstrip().startswith('-')
                    ):
                        value_accum.append(_strip_wrapping_quotes(nxt))
                        j += 1
                        continue

                    # Stop when we reach something that looks like the next field or end of object/array
                    break

                # Merge if we actually collected extra lines
                if value_accum is not None and len(value_accum) > 0:
                    merged = "\\n".join(v for v in value_accum if v != '')
                    # Rebuild a single valid JSON value with a trailing comma if the original had one
                    trailing_comma = ',' if value_part.rstrip().endswith(',') or (j < len(lines) and lines[j].strip().startswith(',')) else ','
                    fixed_line = out_before[0] + f' "{merged}"{trailing_comma}'
                    out.append(fixed_line)
                    i = j
                    continue
                else:
                    # Nothing accumulated; fall through and keep the original line
                    out.append(line)
                    i += 1
                    continue
            else:
                # Value didn't start with a quote; we won't try to fix
                out.append(line)
                i += 1
                continue
        else:
            out.append(line)
            i += 1

    fixed = "\n".join(out)
    # If still not valid, just return original raw so caller can handle gracefully
    try:
        json.loads(fixed)
        return fixed
    except Exception:
        return raw


def parse_install_command(user_input: str):
    """
    Use Groq LLM to parse any intent.
    Returns a dict: {intent, app, version, answer}
    - If intent == "install": contains app + version
    - If intent != "install": contains an answer (free-form text reply in bullet points if possible)
    """

    prompt = f"""
You are an intent parser + responder for a software installation bot.

Rules (VERY IMPORTANT):
- If the user asks "how to install <app>", provide clear step-by-step instructions
  formatted ONLY as bullet points (one step per line, each line starting with "- ").
  At the end, ask if they want to proceed with installation (also as a bullet).
- If the user directly says "install <app> <version>", set intent = "install"
  and return app + version. In this case, "answer" MUST be an empty string.
- If the user provides an invalid or unavailable version, ask for clarification or
  suggest the latest version — ALWAYS as bullet points (each line starts with "- ").
- If the user only says "install" without app/version, ask them to clarify the
  application and version — ALWAYS as bullet points (each line starts with "- ").
- If the query is not about installation, generate a helpful answer — ALWAYS as
  bullet points (each line starts with "- "). Keep it moderate-length (3–7 bullets).
- The JSON must be the ONLY output. The "answer" MUST be a SINGLE JSON string with '\\n'
  between bullets. DO NOT emit multiple quoted strings on separate lines for "answer".
- NEVER include numbering, emojis, or prose paragraphs in "answer".

User input: "{user_input}"

Respond in strict JSON format only:
{{
  "intent": "<install | question | other>",
  "app": "<application name or none>",
  "version": "<version or latest>",
  "answer": "<bot's response if not install, else empty string. Each line MUST start with '- ' and lines are separated by \\n>"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        # If supported by Groq's OpenAI-compatible API, this enforces valid JSON.
        # Safe to keep; if unsupported, Groq will ignore it.
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content.strip()

    # Clean markdown fences if LLM adds them
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()

    # Try parsing; if it fails due to the broken multiline "answer" pattern, repair then parse.
    try:
        data = json.loads(content)
    except Exception as e1:
        repaired = _fix_common_json_breaks(content)
        try:
            data = json.loads(repaired)
        except Exception as e2:
            print("LLM parsing failed:", e2, content)
            return {
                "intent": "other",
                "app": None,
                "version": None,
                "answer": "Sorry, I didn't understand that."
            }

    # Normalize answer to bullet points (formatting-only; core logic unchanged)
    if data.get("answer"):
        data["answer"] = _bulletize(data["answer"])

    return data