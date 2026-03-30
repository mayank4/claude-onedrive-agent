import os
from flask import Flask, request, redirect, session, render_template_string
from dotenv import load_dotenv

from src.api.onedrive_client import get_auth_url, acquire_token_by_authorization_code
from src.services.search_service import get_context_from_onedrive
from src.api.claude_client import ask_claude

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/")
def index():
    if "access_token" not in session:
        auth_url = get_auth_url()
        return f'<a href="{auth_url}">Connect OneDrive</a>'
    return """
        <form method="POST" action="/ask">
            <input type="text" name="question" placeholder="Ask about your OneDrive files" style="width:400px;">
            <button type="submit">Ask</button>
        </form>
    """

@app.route("/callback")
def callback():
    code = request.args.get("code")
    tokens = acquire_token_by_authorization_code(code)
    session["access_token"] = tokens["access_token"]
    return redirect("/")

@app.route("/ask", methods=["POST"])
def ask():
    if "access_token" not in session:
        return redirect("/")
    question = request.form.get("question", "")
    access_token = session["access_token"]

    context, files = get_context_from_onedrive(access_token, question)
    answer = ask_claude(question, context)

    html = f"""
    <p><b>Question:</b> {question}</p>
    <p><b>Answer:</b><br>{answer.replace('\n','<br>')}</p>
    <p><b>Files searched:</b> {', '.join(files)}</p>
    <p><a href="/">Ask another</a></p>
    """
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "True") == "True")
