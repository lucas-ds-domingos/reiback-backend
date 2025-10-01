import requests, os
from dotenv import load_dotenv

load_dotenv()

BASE = "https://secure.d4sign.com.br/api/v1"
TOKEN = os.getenv("D4SIGN_TOKEN_API")
CRYPT = os.getenv("D4SIGN_CRYPT_KEY")

url = f"{BASE}/safes?tokenAPI={TOKEN}"
headers = {"CryptKey": CRYPT, "Accept": "application/json"}

resp = requests.get(url, headers=headers)
print("Status:", resp.status_code)
print("Resp:", resp.text)
