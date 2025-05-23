import streamlit as st
import os
import pickle
import requests
import json
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

st.title("🦠 Coral Disease Image Gallery")

# Define scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

@st.cache_resource

def get_drive_service():
    """
    Authenticates with a Google Service Account using credentials stored
    in Streamlit secrets and returns a Google Drive API service object.

    This function is cached to prevent re-authentication on every rerun.
    """
    try:
        # Load credentials from the service account JSON string stored in Streamlit secrets.
        # The secret named "GOOGLE_CREDENTIALS" should contain the entire
        # content of your service account JSON file, formatted as a multi-line string
        # in your .streamlit/secrets.toml file like this:
        # GOOGLE_CREDENTIALS = """
        # {
        #   "type": "service_account",
        #   "project_id": "...",
        #   ...
        # }
        # """
        creds_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
        
        service = build('drive', 'v3', credentials=creds)
        return service
    except KeyError:
        st.error(
            "Google Cloud credentials not found in Streamlit secrets. "
            "Please ensure you've added GOOGLE_CREDENTIALS to your secrets.toml file."
        )
        st.stop() # Stop the app if secrets are missing
    except json.JSONDecodeError as e:
        st.error(f"Error decoding Google Cloud credentials JSON: {e}. "
                 "Please check the format of your GOOGLE_CREDENTIALS secret.")
        st.stop()
    except Exception as e:
        st.error(f"An unexpected error occurred during Google Drive authentication: {e}")
        st.stop()

def get_subfolder_id(parent_folder_id, target_folder_name):
    """Return folder ID of subfolder with the given name"""
    service = get_drive_service()
    query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    for folder in folders:
        if folder['name'].strip().lower() == target_folder_name.strip().lower():
            return folder['id']
    return None

def list_image_files(folder_id):
    """List image files inside a folder"""
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
    results = service.files().list(q=query, pageSize=100, fields="files(id, name)").execute()
    return results.get('files', [])

# Parent folder ID (your shared folder)
main_folder_id = "1Tj9RBvhpK_0VBPaFLlUr5kVyc7a2Xzqo"

# Category folders to display
categories = ["Black Band Disease", "White Band Disease"]

# Display each category
for category in categories:
    st.header(f"📂 {category}")
    folder_id = get_subfolder_id(main_folder_id, category)
    if folder_id:
        image_files = list_image_files(folder_id)
        if image_files:
            for file in image_files:
                img_url = f"https://drive.google.com/uc?export=view&id={file['id']}"
                st.markdown(f"[🔗 {file['name']}]({img_url})")  # Optional: show clickable link
                try:
                    response = requests.get(img_url)
                    image = Image.open(BytesIO(response.content))
                    st.image(image, caption=file["name"], use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load image: {file['name']} — {e}")
        else:
            st.warning(f"No images found in '{category}' folder.")
    else:
        st.error(f"Folder '{category}' not found.")
