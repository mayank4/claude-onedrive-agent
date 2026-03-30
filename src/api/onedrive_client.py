import os
import json
import requests
from dotenv import load_dotenv
import msal

load_dotenv()

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read", "Files.Read"]

app = msal.ConfidentialClientApplication(
    CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
)

def get_auth_url():
    return app.get_authorization_request_url(SCOPES, redirect_uri=REDIRECT_URI)

def acquire_token_by_authorization_code(code: str):
    result = app.acquire_token_by_authorization_code(
        code, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    if "access_token" not in result:
        raise Exception(f"Error acquiring token: {result}")
    return result

def search_onedrive(access_token: str, query: str):
    """
    Try a proper search call. If Graph returns an error (400, etc.),
    log it and fall back to listing files instead of crashing.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Preferred: search in root
    search_url = "https://graph.microsoft.com/v1.0/me/drive/root/search(q='{q}')".format(q=query)

    resp = requests.get(search_url, headers=headers)

    if not resp.ok:
        print("GRAPH SEARCH ERROR:", resp.status_code, resp.text)

        # Fallback: just list files in root so the app keeps working
        list_url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        resp2 = requests.get(list_url, headers=headers)

        if not resp2.ok:
            print("GRAPH LIST ERROR:", resp2.status_code, resp2.text)
            return []  # give up gracefully

        data = resp2.json()
        return data.get("value", [])

    data = resp.json()
    return data.get("value", [])

def download_file_content(access_token: str, item_id: str) -> bytes:
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.content
