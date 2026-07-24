from flask import Flask, request, jsonify
import requests
import binascii
import random
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

app = Flask(__name__)

# ---------- Constants ----------
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
FREEFIRE_VERSION = "OB54"

KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

DEVICES = [
    {"model": "SM-G998B", "android": "13", "api": "33", "cpu": "ARMv8 | 2800 | 8", "gpu": "Mali-G78", "res": ["1440", "1080"], "dpi": "480", "ram": "8192", "build": "TP1A.220624.014"},
    {"model": "realme C31", "android": "12", "api": "31", "cpu": "ARMv8 | 2000 | 8", "gpu": "Mali-G52", "res": ["720", "1600"], "dpi": "320", "ram": "4096", "build": "SQ3A.220705.003"},
    {"model": "Mi 11", "android": "12", "api": "32", "cpu": "ARMv8 | 2500 | 8", "gpu": "Adreno 650", "res": ["1080", "2400"], "dpi": "395", "ram": "6144", "build": "SQ3A.220705.003"},
]

def get_random_device():
    device = random.choice(DEVICES)
    return {
        "model": device["model"],
        "android": device["android"],
        "api": device["api"],
        "cpu": device["cpu"],
        "gpu": device["gpu"],
        "width": device["res"][0],
        "height": device["res"][1],
        "dpi": device["dpi"],
        "ram": device["ram"],
        "build": device["build"]
    }

def encrypt_data(data_bytes):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded)

def get_eat_token_from_url(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get("eat", [None])[0]

def get_access_token_from_eat(eat_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        resp = requests.get(url, allow_redirects=False, timeout=10, verify=False)
        
        if resp.status_code == 302 and "Location" in resp.headers:
            location = resp.headers["Location"]
            parsed = urlparse(location)
            params = parse_qs(parsed.query)
            
            access_token = params.get("access_token", [None])[0]
            account_id = params.get("account_id", [None])[0]
            nickname = params.get("nickname", [None])[0]
            region = params.get("region", [None])[0]
            
            return access_token, account_id, nickname, region
        
        return None, None, None, None
    except:
        return None, None, None, None

def get_openid_method_1(uid):
    try:
        url = "https://topup.pk/api/auth/player_id_login"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36",
            "X-Requested-With": "mark.via.gp",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        resp = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        data = resp.json()
        return data.get("open_id")
    except:
        return None

def get_openid_method_2(uid):
    try:
        url = "https://api.garena.com/auth/player_id_login"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
        }
        payload = {"app_id": 100067, "login_id": str(uid)}
        resp = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        data = resp.json()
        return data.get("open_id")
    except:
        return None

def get_openid_from_uid(uid):
    open_id = get_openid_method_1(uid)
    if open_id:
        return open_id
    
    open_id = get_openid_method_2(uid)
    if open_id:
        return open_id
    
    if len(str(uid)) >= 10:
        return str(uid)
    
    return None

def perform_major_login(access_token, open_id):
    try:
        import my_pb2
        device = get_random_device()
        
        game_data = my_pb2.GameData()
        game_data.timestamp = "2025-01-15 10:30:45"
        game_data.game_name = "free fire"
        game_data.game_version = 1
        game_data.version_code = "1.121.0"
        game_data.os_info = f"Android OS {device['android']} / API-{device['api']} ({device['build']})"
        game_data.device_type = "Handheld"
        game_data.network_provider = "Verizon Wireless"
        game_data.connection_type = "WIFI"
        game_data.screen_width = int(device['width'])
        game_data.screen_height = int(device['height'])
        game_data.dpi = device['dpi']
        game_data.cpu_info = device['cpu']
        game_data.total_ram = int(device['ram'])
        game_data.gpu_name = device['gpu']
        game_data.gpu_version = "OpenGL ES 3.2"
        game_data.user_id = f"Google|{random.randint(1000000000000, 9999999999999)}"
        game_data.ip_address = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        game_data.language = "en"
        game_data.open_id = open_id
        game_data.access_token = access_token
        game_data.platform_type = 8
        game_data.field_99 = "8"
        game_data.field_100 = "8"
        game_data.device_form_factor = "Phone"
        game_data.device_model = device['model']

        serialized = game_data.SerializeToString()
        encrypted = encrypt_data(serialized)
        hex_encrypted = binascii.hexlify(encrypted).decode()
        edata = bytes.fromhex(hex_encrypted)
        
        headers = {
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {device['android']}; {device['model']})",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/octet-stream",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEFIRE_VERSION
        }
        
        resp = requests.post(MAJOR_LOGIN_URL, data=edata, headers=headers, timeout=15, verify=False)
        
        if resp.status_code == 200:
            try:
                import output_pb2
                msg = output_pb2.Garena_420()
                msg.ParseFromString(resp.content)
                for field in msg.DESCRIPTOR.fields:
                    if field.name == "token":
                        return getattr(msg, field.name)
            except:
                pass
    except Exception as e:
        pass
    return None

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Eat Token to Access Token Converter",
        "version": "OB54",
        "credit": "@SHAPPNO_CODEX",
        "status": "Running on Vercel ✅",
        "endpoint": "/access_token?eat_token=YOUR_EAT_TOKEN"
    })

@app.route("/access_token", methods=["GET"])
def get_token_info():
    eat_input = request.args.get("eat_token")
    if not eat_input:
        return jsonify({"error": "Missing eat_token parameter"}), 400

    if eat_input.startswith("http"):
        eat_token = get_eat_token_from_url(eat_input)
        if not eat_token:
            return jsonify({"error": "Eat token not found in URL"}), 400
    else:
        eat_token = eat_input

    access_token, account_id, nickname, region = get_access_token_from_eat(eat_token)
    
    if not access_token:
        return jsonify({
            "status": "error",
            "message": "Invalid eat token or expired"
        }), 400

    open_id = get_openid_from_uid(account_id)
    if not open_id:
        return jsonify({
            "status": "error",
            "message": "Failed to get OpenID"
        }), 400

    jwt_token = perform_major_login(access_token, open_id)

    return jsonify({
        "status": "success",
        "eat_token": eat_token,
        "account_id": account_id,
        "account_nickname": nickname,
        "open_id": open_id,
        "access_token": access_token,
        "region": region,
        "generated_jwt": jwt_token,
        "version": "OB54",
        "credit": "@SHAPPNO_CODEX"
    })

# ========== VERCEL HANDLER ==========
def handler(request, context):
    return app(request, context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)