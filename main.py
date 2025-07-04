from flask import Flask, request, jsonify, redirect
import requests
import os
import base64

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
DEVICE_NAME = "Raspberry-JBL"

def get_access_token():
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN
    }
    r = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if r.status_code != 200:
        raise Exception(f"Erro ao renovar token: {r.text}")
    return r.json()["access_token"]

def play_album(album_uri, access_token):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    res_devices = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    if res_devices.status_code != 200:
        raise Exception(f"Erro ao obter dispositivos: {res_devices.text}")
    devices = res_devices.json().get("devices", [])
    device_id = next((d["id"] for d in devices if d["name"] == DEVICE_NAME), None)
    if not device_id:
        raise Exception(f"Dispositivo '{DEVICE_NAME}' não encontrado.")
    res_play = requests.put(
        f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
        headers=headers,
        json={"context_uri": album_uri}
    )
    if res_play.status_code == 401:
        new_token = get_access_token()
        return play_album(album_uri, new_token)
    if res_play.status_code not in [200, 204]:
        raise Exception(f"Erro ao tocar álbum: {res_play.status_code} - {res_play.text}")
    return "Reprodução iniciada"

@app.route("/rfid", methods=["POST"])
def receber_rfid():
    try:
        data = request.json
        album_uri = data.get("album_uri")
        if not album_uri:
            return jsonify({"error": "album_uri não encontrado"}), 400
        access_token = get_access_token()
        resultado = play_album(album_uri, access_token)
        return jsonify({"mensagem": resultado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/connect")
def connect():
    """Redirects the user to Spotify's OAuth authorization page."""
    scope = "user-read-playback-state user-modify-playback-state streaming"
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    r = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if r.status_code != 200:
        return f"Erro: {r.text}", 400
    response_json = r.json()
    refresh_token = response_json.get("refresh_token")
    access_token = response_json.get("access_token")
    return jsonify({
        "refresh_token": refresh_token,
        "access_token": access_token
    })

@app.route("/", methods=["GET"])
def home():
    return "Backend RFID Spotify OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
