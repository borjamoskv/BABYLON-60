# C5-REAL EXERGY CERTIFIED
import os
import sys
import time
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CORTEX_DIR = Path(__file__).parent
CREDENTIALS_PATH = CORTEX_DIR / 'credentials.json'
TOKEN_PATH = CORTEX_DIR / 'token.json'

def authenticate_gmail():
    """Authenticates with Gmail API and returns the service object."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(f"[ERROR] No se encontró el archivo {CREDENTIALS_PATH}")
                print("Por favor, obtén tus credenciales OAuth 2.0 desde Google Cloud Console.")
                print("Guárdalas como 'credentials.json' en la carpeta cortex_mail/ y vuelve a ejecutar.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def poll_inbox():
    """L1 Sensor: Polling loop to fetch new emails and filter Anergia."""
    try:
        service = authenticate_gmail()
        print("[NODO L1] Córtex-Mail Sensor activado. Escuchando borjamoskv@gmail.com...")

        # Future implementation will go here
        # 1. Fetch UNREAD emails
        # 2. Filter out CI failures (mark as read or trash)
        # 3. Route high-exergy emails to agent handler

    except HttpError as error:
        print(f'[NODO L1 ERROR] Fricción termodinámica en la API: {error}')

if __name__ == '__main__':
    poll_inbox()
