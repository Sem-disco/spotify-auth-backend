from flask import Flask, redirect, request
import os
import requests

app = Flask(__name__)

# Corrigido: remove espaços/quebras de linha
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

@app.route("/")
def index():
    return "Backend para autenticação do Spotify está rodando!"

@app.route("/connect")
def connect():
    # Debug print para logs
    print("DEBUG - CLIENT_ID:", CLIENT_ID)
    print("DEBUG - CLIENT_SECRET:", CLIENT_SECRET)
    print("DEBUG - REDIRECT_URI:", REDIRECT_URI)

    scope = "user-read-playback-state user-modify-playback-state"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&scope={scope}"
        f"&redirect_uri={REDIRECT_URI}"
    )

    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Erro: código de autorização não recebido"

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        return f"Erro ao obter token: {response.text}"

    token_info = response.json()
    return token_info
