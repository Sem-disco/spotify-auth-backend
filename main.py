from flask import Flask, redirect, request, jsonify
import os
import requests
from urllib.parse import quote

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()
ACCESS_TOKEN_TEMP = os.getenv("ACCESS_TOKEN_TEMP", "").strip()

@app.route("/")
def home():
    return "🔊 Backend do Spotify está no ar!"

@app.route("/connect")
def connect():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        return "Erro: Variáveis de ambiente faltando ou inválidas.", 500

    scope = "user-read-playback-state user-modify-playback-state"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={quote(REDIRECT_URI)}"
        f"&scope={quote(scope)}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Código não fornecido", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post("https://accounts.spotify.com/api/token", data=data)
    if response.status_code != 200:
        return f"Erro ao obter token: {response.text}", 500

    return jsonify(response.json())

@app.route("/play", methods=["POST"])
def play_album():
    album_uri = request.json.get("album_uri")
    if not album_uri:
        return jsonify({"error": "album_uri é obrigatório"}), 400

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN_TEMP}",
        "Content-Type": "application/json"
    }

    data = {
        "context_uri": album_uri
    }

    response = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        json=data,
        headers=headers
    )

    if response.status_code != 204:
        return jsonify({"error": response.text}), response.status_code

    return jsonify({"message": "Reprodução iniciada com sucesso!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
