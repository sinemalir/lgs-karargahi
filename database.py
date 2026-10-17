import os
import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from pathlib import Path

desktop_path = Path.home() / "Desktop"
env_path = desktop_path / ".env"
cred_path = desktop_path / "firebase_credentials.json"
local_db_path = Path(__file__).parent / "local_db.json"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

db = None
try:
    if not firebase_admin._apps:
        if cred_path.exists():
            cred = credentials.Certificate(str(cred_path))
            bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "lgs27-c1f3e.firebasestorage.app")
            firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})
        elif "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif "FIREBASE_CREDENTIALS_JSON" in st.secrets:
            cred_dict = json.loads(st.secrets["FIREBASE_CREDENTIALS_JSON"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
    if firebase_admin._apps:
        db = firestore.client()
except Exception as e:
    print(f"Firebase başlatma uyarısı (Yerel yedek kullanılacak): {e}")
    db = None

def _read_local_db():
    if local_db_path.exists():
        try:
            return json.loads(local_db_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _write_local_db(content):
    try:
        local_db_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def get_user_data(username, collection_name):
    if db is not None:
        try:
            docs = db.collection("users").document(username).collection(collection_name).stream()
            return {doc.id: doc.to_dict() for doc in docs}
        except Exception as e:
            print(f"Veri çekme hatası: {e}")
    # Yerel JSON yedek
    local_data = _read_local_db()
    return local_data.get(username, {}).get(collection_name, {})

def save_user_data(username, collection_name, doc_id, data):
    if db is not None:
        try:
            db.collection("users").document(username).collection(collection_name).document(doc_id).set(data)
            return True
        except Exception as e:
            print(f"Veri kaydetme hatası: {e}")
    # Yerel JSON yedek
    local_data = _read_local_db()
    local_data.setdefault(username, {}).setdefault(collection_name, {})[doc_id] = data
    _write_local_db(local_data)
    return True
