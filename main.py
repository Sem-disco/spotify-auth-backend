from flask import Flask, redirect, request, jsonify
import os
import requests
from urllib.parse import quote

app = Flask(__name__)

# Carregar variáveis de ambiente (garantindo que estão limpas)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

@app.route("/")
def home():
    return "Backend do Spotify está no ar!"

@app.route("/connect")
def connect():
    # Segurança: verifica se as variáveis estão válidas
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        return "Erro: Variáveis de ambiente faltando ou inválidas.", 500

    scope = "user-read-playback-state user-modify-playback-state"

    # Cria URL de autenticação sem caracteres ilegais
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={quote(CLIENT_ID)}"
        f"&scope={quote(scope)}"
        f"&redirect_uri={quote(REDIRECT_URI)}"
    )

    print("DEBUG - Redirecionando para:", auth_url)
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return "Erro: código de autorização ausente.", 400

    # Troca o código por um token de acesso
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        return f"Erro ao obter token: {response.text}", 500

    tokens = response.json()
    return jsonify(tokens)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
