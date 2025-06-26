from flask import Flask, request, redirect, jsonify
import os
import requests
from urllib.parse import quote

app = Flask(__name__)

# VARIÁVEIS FIXADAS COM BASE NA SUA CONTA SPOTIFY
CLIENT_ID = "935fcd06bb444612afdf2023b3f5bbee"
CLIENT_SECRET = "baa76034ecfd43a5b63cf93b1f01ddf0"
REDIRECT_URI = "https://spotify-auth-backend-ir7p.onrender.com/callback"

ACCESS_TOKEN = "BQCedeDqZ3Wqzo6_a5HUR7Qgud1nC1gsH4PtB6qUcFAe7jYLNVf0fK2okkFBD3WPMS0yy630N9gmh17Qih4ozgz_un_EqTx7X469o_P8eXo_bRMMNSEhdLkJvlX9luS1000VEA6tuyzzxK"
REFRESH_TOKEN = "AQCPWyHFTne5VG1gAWWlcQvImIze4NkGSzVGXLAdFMu-3IlU9kOWbEGe6-KW_yhD9ldBdIRbFdk94gNZXBPbHElZpiNkoETnD2ldAzG3yQ3h5BPp3Km5PKBoVUPorDQesdI"

TAG_TO_URI = {
    "165819162692": "spotify:album:2UJwKSBUz6rtW4QLK74kQu"  # Nirvana - Nevermind
}

@app.route("/")
def home():
    return "🎵 Backend RFID Spotify online e funcional!"

@app.route("/connect")
def connect():
    scope = "user-read-playback-state user-modify-playback-state"
    return redirect(
        f"https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={quote(REDIRECT_URI)}"
        f"&scope={quote(scope)}"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Código de autorização ausente", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=data)
    if r.status_code != 200:
        return f"Erro ao obter token: {r.text}", 500

    return jsonify(r.json())

def refresh_access_token(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post("https://accounts.spotify.com/api/token", data=data)
    r.raise_for_status()
    return r.json()["access_token"]

@app.route("/rfid", methods=["POST"])
def rfid():
    global ACCESS_TOKEN

    tag_id = str(request.json.get("tag_id"))
    if not tag_id or tag_id not in TAG_TO_URI:
        return jsonify({"error": "Tag inválida"}), 400

    uri = TAG_TO_URI[tag_id]

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "context_uri": uri
    }

    r = requests.put("https://api.spotify.com/v1/me/player/play", headers=headers, json=payload)

    if r.status_code == 401:
        ACCESS_TOKEN = refresh_access_token(REFRESH_TOKEN)
        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        r = requests.put("https://api.spotify.com/v1/me/player/play", headers=headers, json=payload)

    if r.status_code != 204:
        return jsonify({"error": r.text}), r.status_code

    return jsonify({"message": f"Tocando: {uri}"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
