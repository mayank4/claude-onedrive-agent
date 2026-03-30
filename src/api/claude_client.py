import os
from anthropic import Anthropic, BadRequestError
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask_claude(question: str, context: str) -> str:
    prompt = f"""
You are an assistant with access to text from OneDrive files.

User question:
{question}

Relevant file content:
{context}

Answer succinctly and mention which files/sections you used when relevant.
"""
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except BadRequestError as e:
        # Show a friendly message in the UI instead of crashing
        return (
            "The AI backend returned an error.\n\n"
            f"Details: {getattr(e, 'message', str(e))}\n\n"
            "If this mentions low credit balance, please add credits or change the API key."
        )
