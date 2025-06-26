from flask import Flask, redirect, request, jsonify
import os
import requests

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# 1. Rota para iniciar autenticação
@app.route("/connect")
def connect():
    scope = "user-read-playback-state user-modify-playback-state streaming"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

# 2. Rota de callback do Spotify
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Erro: code não recebido.", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_url = "https://accounts.spotify.com/api/token"

    try:
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Erro ao obter token: {e}\nResposta: {response.text}", 500

    token_info = response.json()
    refresh_token = token_info.get("refresh_token")

    if not refresh_token:
        return f"Erro: refresh_token ausente. Resposta: {token_info}", 500

    # Só loga o token, pois não podemos salvar no Render por aqui
    return jsonify({
        "status": "Autenticado com sucesso",
        "access_token": token_info.get("access_token"),
        "refresh_token": refresh_token,
        "obs": "Copie esse refresh_token e cole no Render!"
    })

# 3. Ping simples para ver se tá vivo
@app.route("/")
def index():
    return "Backend do Spotify está vivo. Use /connect para autenticar."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
