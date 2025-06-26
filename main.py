from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN_TEMP")

@app.route("/")
def index():
    return "Backend do Spotify está vivo. Use /connect para autenticar."

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
    return jsonify({"auth_url": auth_url})

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

    return jsonify({
        "status": "Autenticado com sucesso",
        "access_token": token_info.get("access_token"),
        "refresh_token": refresh_token,
        "obs": "Copie esse refresh_token e cole no Render!"
    })

@app.route("/rfid", methods=["POST"])
def play_album_from_tag():
    data = request.get_json()
    album_uri = data.get("album_uri")
    
    if not album_uri:
        return jsonify({"error": "album_uri não encontrado"}), 400

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "context_uri": album_uri
    }

    play_url = "https://api.spotify.com/v1/me/player/play"

    response = requests.put(play_url, headers=headers, json=body)

    if response.status_code != 204:
        return jsonify({
            "error": "Erro ao tocar álbum",
            "status_code": response.status_code,
            "resposta": response.text
        }), 500

    return jsonify({"status": "Música iniciada com sucesso!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

