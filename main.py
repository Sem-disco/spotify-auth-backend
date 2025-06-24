from flask import Flask, redirect, request, jsonify
import os
import requests
from urllib.parse import quote

app = Flask(__name__)

# Carregar variáveis de ambiente
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

# Página inicial
@app.route("/")
def home():
    return "🎧 Backend do Spotify está no ar!"

# Conectar ao Spotify
@app.route("/connect")
def connect():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        return "❌ Erro: Variáveis de ambiente não configuradas corretamente.", 500

    auth_url = (
        "https://accounts.spotify.com/authorize"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={quote(REDIRECT_URI)}"
        "&scope=user-read-playback-state user-modify-playback-state"
    )
    return redirect(auth_url)

# Callback de autorização
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ Erro: Código de autorização não recebido.", 400

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code != 200:
        return f"❌ Erro ao obter token: {response.text}", 500

    tokens = response.json()
    access_token = tokens.get("access_token")

    if not access_token:
        return "❌ Erro: Token de acesso não encontrado.", 500

    return jsonify({"access_token": access_token})

# Endpoint para tocar álbum via Raspberry Pi
@app.route("/play", methods=["POST"])
def play_album():
    data = request.json
    album_uri = data.get("album_uri")

    if not album_uri:
        return jsonify({"error": "URI do álbum não fornecida"}), 400

    # Requisição para pegar token do ambiente (exemplo: para simplificar)
    access_token = os.getenv("ACCESS_TOKEN_TEMP", "").strip()
    if not access_token:
        return jsonify({"error": "Token de acesso não encontrado. Faça login pelo /connect"}), 401

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "context_uri": album_uri,
        "offset": {"position": 0},
        "position_ms": 0
    }

    r = requests.put("https://api.spotify.com/v1/me/player/play", json=body, headers=headers)
    if r.status_code != 204:
        return jsonify({"error": "Erro ao tocar álbum", "details": r.text}), r.status_code

    return jsonify({"message": "Álbum iniciado com sucesso!"})

if __name__ == "__main__":
    app.run(debug=True)
