import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Escopo do Google Drive (para ler e escrever)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json", SCOPES
)

creds = flow.run_local_server(port=0)

# Salva o token para reutilizar
with open("token.json", "w") as token_file:
    token_file.write(creds.to_json())

print("Token gerado com sucesso!")
