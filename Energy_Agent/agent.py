import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from prompts import INPUT_UNDERSTANDING, STATE_TRACKER, TASK_PLANNER, OUTPUT_GENERATOR

# -----------------------------
# Load API key securely from .env
# -----------------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found. Please add it to your .env file.")

client = OpenAI(api_key=api_key)

# -----------------------------
# Simple in-memory state (resettable)
# -----------------------------
STATE = {
    "location_type": "",
    "appliances": {},
    "usage_pattern": {},
    "missing_info": []
}

def reset_state():
    global STATE
    STATE = {
        "location_type": "",
        "appliances": {},
        "usage_pattern": {},
        "missing_info": []
    }

# -----------------------------
# Helper: call the LLM (non-streaming)
# -----------------------------
def call_llm(system_prompt: str, user_content: str, expect_json: bool = True):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2
    )
    content = resp.choices[0].message.content

    if expect_json:
        try:
            return json.loads(content)
        except Exception:
            return {"error": "Invalid JSON", "raw": content}
    return content

# -----------------------------
# Helper: stream the LLM output (word-by-word)
# -----------------------------
def stream_llm(system_prompt: str, user_content: str):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        stream=True
    )
    for chunk in resp:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# -----------------------------
# Modules
# -----------------------------
def input_understanding(user_text: str):
    return call_llm(INPUT_UNDERSTANDING, user_text, expect_json=True)

def state_tracker(classification: dict):
    payload = json.dumps({"current_state": STATE, "new_input": classification})
    updated = call_llm(STATE_TRACKER, payload, expect_json=True)
    if isinstance(updated, dict) and "missing_info" in updated:
        for k in ["location_type", "appliances", "usage_pattern", "missing_info"]:
            STATE[k] = updated.get(k, STATE.get(k))
    return STATE

def task_planner():
    payload = json.dumps({"state": STATE})
    return call_llm(TASK_PLANNER, payload, expect_json=True)

def output_generator(plan: dict, stream: bool = False):
    payload = json.dumps({"state": STATE, "plan": plan})
    if stream:
        return stream_llm(OUTPUT_GENERATOR, payload)
    else:
        return call_llm(OUTPUT_GENERATOR, payload, expect_json=False)
