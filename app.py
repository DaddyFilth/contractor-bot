import os
from flask import Flask
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

if not url or not key:
    raise RuntimeError(f"Missing env vars — URL: {'set' if url else 'MISSING'}, KEY: {'set' if key else 'MISSING'}")

app = Flask(__name__)
supabase: Client = create_client(url, key)

@app.route("/")
def index():
    response = supabase.table("todos").select("*").execute()
    todos = response.data
    html = "<h1>Todos</h1><ul>"
    for todo in todos:
        html += f"<li>{todo['name']}</li>"
    return html + "</ul>"

if __name__ == "__main__":
    app.run(debug=True)
