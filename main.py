from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
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
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Identifica o device
    devices_res = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    if devices_res.status_code != 200:
        raise Exception(f"Erro ao obter dispositivos: {devices_res.text}")

    devices = devices_res.json().get("devices", [])
    device_id = next((d["id"] for d in devices if d["name"] == DEVICE_NAME), None)
    if not device_id:
        raise Exception(f"Dispositivo '{DEVICE_NAME}' não encontrado.")

    # Tenta tocar o álbum
    play_res = requests.put(
        f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
        headers=headers,
        json={"context_uri": album_uri}
    )

    if play_res.status_code == 401:
        # Token expirou, tenta renovar e tentar novamente
        new_token = get_access_token()
        return play_album(album_uri, new_token)

    if play_res.status_code not in [200, 204]:
        raise Exception(f"Erro ao tocar álbum: {play_res.status_code} - {play_res.text}")

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

@app.route("/", methods=["GET"])
def home():
    return "Backend RFID Spotify OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
