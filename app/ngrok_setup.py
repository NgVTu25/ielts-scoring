from pyngrok import ngrok
import os

def start_ngrok(port=8000):
    auth_token = os.getenv("NGROK_AUTHTOKEN")
    if not auth_token:
        print("⚠️ NGROK_AUTHTOKEN not found. Please set it before running.")
        return None

    ngrok.set_auth_token(auth_token)
    public_url = ngrok.connect(port).public_url
    print(f"🚀 Ngrok tunnel started: {public_url}")
    return public_url
