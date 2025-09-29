import sys
import os, shutil
import json
from pathlib import Path
import random
import datetime
from fastapi.testclient import TestClient
from main import app
from api.ingestion.download_images import main as download_img
import pandas as pd

# TODO : passer l'ingestion dans un container dédié, ne dois pas être dans la Gateway

# Configuration propre du PYTHONPATH (une seule fois, au début du fichier)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test.config.config import config
from test.config.test_settings import test_settings

client = TestClient(app)

# Générer un entier aléatoire entre config.RANDOM_RANGE_START et config.RANDOM_RANGE_END
RND = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)
USERNAME = f"{RND}-flow-user"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
PASSWORD = USERNAME

# Drive download 
IMAGE_FOLDER_ID = "1x5VqNLLOC4RDkfZjm-p4W29WfzB9hywh"
DRIVE_KEY = os.getenv("DRIVE_KEY", "api/ingestion/rakutenmlops.json")
IMAGES_LIST = os.getenv("IMAGES_LIST", "api/ingestion/liste.txt")
IMAGES_DEST = os.getenv("IMAGES_DEST", "api/ingestion/images_temp")
LIMIT = int(os.getenv("LIMIT", "21"))
STATE_PATH = Path("api/ingestion/offset_state.json")

# Google Sheet
FILE_ID = "1g9-0u845FJOPWaj1HlfvptNxDzhzPbsMYnaYOtn0uFY"
GID = 1942072585
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid={GID}"



def _signup_and_login():
    # Signup
    r = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
        json={"username": USERNAME, "email": EMAIL, "password": PASSWORD},
    )
    assert r.status_code == 200, f"Signup a échoué: {r.status_code} {r.text}"

    # Login
    r = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": USERNAME, "password": PASSWORD},
    )
    assert r.status_code == 200, f"Login a échoué: {r.status_code} {r.text}"

    token = r.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": token,
    }
    return headers

def _create_ad(img, designation, description, cat_code, cat_label, headers):
    with open(img, "rb") as f:
        files = {"file": (f.name, f, "image/jpeg")}
        data = {
            "designation": designation,
            "description": description,
            "category_code": cat_code,
            "category_label": cat_label,
        }
        response = client.post(
            f"{test_settings.PROTECTED_ENDPOINT_URL}/create_ad",
            headers=headers,
            data=data,
            files=files,
        )
    assert response.status_code == 200, f"Create ad failed: {response.status_code} {response.text}"
    payload = response.json()
    return payload["ad"]["id"], payload

def _get_dataframe(url):
    """ Download google sheet in csv 
        Return a datframe
    """
    df = pd.read_csv(url, index_col=0)
    return df

def _create_images_list(df, file_path):
    """ Create images list in a text file """
    image_names = df["image_name"]
    image_names.to_csv(file_path, 
                       index=False, 
                       header=False, 
                       encoding="utf-8",
                       lineterminator="\n")
    return len(image_names)
    
# Images download functions 
def load_state():
    """ Load json file to indicate cursor """
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"offset": 0}

def save_state(state):
    """ Save state in json file """
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))

def remaining_lines(names_file, offset):
    """ Helping not depass end of file """
    with open(names_file, "r", encoding="utf-8") as f:
        total = sum(1 for line in f if line.strip())
    return max(0, total - offset)
    
def run_batch(limit):
    """ Download images with state """
    state = load_state()
    offset = int(state.get("offset", 0))
    left = remaining_lines(IMAGES_LIST, offset)
    if left <= 0:
        print("Rien à faire: offset >= nb de lignes.")
        return

    limit_effective = min(limit, left)

    argv = [
        "--service-account", DRIVE_KEY,
        "--folder-id", IMAGE_FOLDER_ID,
        "--names-file", IMAGES_LIST,
        "--dest-dir", IMAGES_DEST,
        "--offset", str(offset),
        "--limit", str(limit_effective),
    ]
    # Execute 
    print("Try to donwload images...")
    ret = download_img(argv)

    # Increment state
    state["offset"] = offset + limit_effective
    state["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    save_state(state)


def main():
    """
    ### Phase 1 : Download dataframe (csv of google sheet)
    ### Phase 2 : Create images list to download
    ### Phase 3 : Download images locally
    ### Phase 4 : Push images in Minio and ad in PostgreSQL by gateway endpoint "/create_ad"
 
    """
    # Signup and connect
    headers = _signup_and_login()

    # Download dataframe
    df = _get_dataframe(SHEET_URL)

    # Create images list file
    limit = _create_images_list(df, IMAGES_LIST)
        
    # Download images locally
    run_batch(limit)

    # Create ad
    for _, row in df.iterrows():
        image = row["image_name"]
        img = os.path.join(IMAGES_DEST, str(image))
        designation = row["designation"]
        description = row['description']
        cat_code = row["cat_code"]
        cat_label = row["cat_label"]
        ad_id, created = _create_ad(img, designation, description, cat_code, cat_label, headers)
        
    # Delete images in images_temp
    shutil.rmtree(IMAGES_DEST, ignore_errors=True)

if __name__ == "__main__":
    import sys
    sys.exit(main())
