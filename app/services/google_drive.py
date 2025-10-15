import googleapiclient.discovery
from google.oauth2 import service_account

# Dados fornecidos por você
CLIENT_EMAIL = "uploader-drive@documentosfinance.iam.gserviceaccount.com"
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDAmiGflQ9CcWkA
... (restante da chave que você enviou)
-----END PRIVATE KEY-----
"""

# Criar credenciais
credentials = service_account.Credentials.from_service_account_info({
    "type": "service_account",
    "client_email": CLIENT_EMAIL,
    "private_key": PRIVATE_KEY,
    "token_uri": "https://oauth2.googleapis.com/token",
})

service = googleapiclient.discovery.build("drive", "v3", credentials=credentials)

# Função para fazer upload para Google Drive
def upload_to_drive(file_bytes, filename, parent_folder_id):
    file_metadata = {
        "name": filename,
        "parents": [parent_folder_id]
    }

    media = googleapiclient.http.MediaIoBaseUpload(file_bytes, mimetype="application/pdf")

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink, webContentLink"
    ).execute()

    return uploaded.get("webViewLink")  # ou webContentLink para download direto
