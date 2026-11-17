import streamlit as st
import os
import json
import hashlib
import uuid
import time
from datetime import datetime
from cryptography.fernet import Fernet

st.set_page_config(
    page_title="CloudShare - Secure File Sharing", layout="wide")

# --- SETUP CLOUD STORAGE & DATABASE DIRECTORIES ---
CLOUD_DIR = "cloud_storage_vault"
DB_FILE = "cloud_metadata_db.json"
KEY_FILE = "master_encryption.key"

os.makedirs(CLOUD_DIR, exist_ok=True)

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as kf:
        kf.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as kf:
    cipher = Fernet(kf.read())


def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "files": {}, "logs": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def log_event(db, user, action, filename):
    db["logs"].insert(0, {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User": user,
        "Action": action,
        "File": filename
    })


db = load_db()

# --- SESSION STATE ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

st.title("☁️ CloudShare – Secure Cloud-Based File Sharing System")
st.markdown(
    "End-to-End Encrypted Cloud Storage, Access Control & Token-Based Secure File Sharing")

# --- SIDEBAR: AUTHENTICATION & SHARED LINK ACCESS ---
menu = st.sidebar.radio("Navigation", [
                        "🔐 Login / Register", "📂 Cloud Dashboard", "🔗 Access Shared Link"])

# 1. LOGIN / REGISTER PAGE
if menu == "🔐 Login / Register":
    if st.session_state.logged_in_user:
        st.success(f"Logged in as **{st.session_state.logged_in_user}**")
        if st.button("Logout"):
            st.session_state.logged_in_user = None
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        with tab1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Login"):
                if u in db["users"] and db["users"][u] == hash_password(p):
                    st.session_state.logged_in_user = u
                    log_event(db, u, "User Login", "-")
                    save_db(db)
                    st.success(
                        "Login successful! Switch to 'Cloud Dashboard' on the left.")
                else:
                    st.error("Invalid username or password.")
        with tab2:
            nu = st.text_input("Choose Username", key="reg_u")
            np = st.text_input("Choose Password", type="password", key="reg_p")
            if st.button("Register"):
                if nu and np:
                    if nu in db["users"]:
                        st.warning("Username already exists.")
                    else:
                        db["users"][nu] = hash_password(np)
                        log_event(db, nu, "Account Registered", "-")
                        save_db(db)
                        st.success("Account created! You can now log in.")
                else:
                    st.warning("Please enter both username and password.")

# 2. CLOUD DASHBOARD
elif menu == "📂 Cloud Dashboard":
    if not st.session_state.logged_in_user:
        st.warning("Please log in first from the 'Login / Register' tab.")
    else:
        user = st.session_state.logged_in_user
        st.subheader(f"Welcome, {user} 👋")

        # Upload Section
        st.markdown("### ⬆️ Upload & Encrypt File to Cloud")
        uploaded_file = st.file_uploader(
            "Select a file (PDF, DOCX, PNG, JPG, TXT, ZIP)")
        share_pwd = st.text_input(
            "Optional Share Password (leave blank for token-only access)", type="password")

        if uploaded_file and st.button("Encrypt & Upload to Cloud"):
            file_id = str(uuid.uuid4())[:8]
            encrypted_bytes = cipher.encrypt(uploaded_file.read())
            cloud_path = os.path.join(
                CLOUD_DIR, f"{file_id}_{uploaded_file.name}.enc")

            with open(cloud_path, "wb") as f:
                f.write(encrypted_bytes)

            db["files"][file_id] = {
                "filename": uploaded_file.name,
                "owner": user,
                "size_kb": round(len(encrypted_bytes) / 1024, 2),
                "cloud_path": cloud_path,
                "share_token": f"cloudshare://secure/{file_id}",
                "share_password": hash_password(share_pwd) if share_pwd else None,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            log_event(db, user, "Encrypted Upload", uploaded_file.name)
            save_db(db)
            st.success(
                f"✅ File encrypted with AES-128 & uploaded! Share ID: **{file_id}**")

        # Manage Uploaded Files
        st.markdown("### 🗄️ Your Cloud Files & Secure Share Links")
        user_files = {fid: info for fid,
                      info in db["files"].items() if info["owner"] == user}

        if user_files:
            for fid, info in user_files.items():
                with st.expander(f"📄 {info['filename']} ({info['size_kb']} KB) — Share ID: {fid}"):
                    st.write(f"**Uploaded:** {info['uploaded_at']}")
                    st.code(
                        f"Share ID: {fid}  |  Secure URI: {info['share_token']}")

                    with open(info["cloud_path"], "rb") as ef:
                        decrypted_data = cipher.decrypt(ef.read())

                    col1, col2 = st.columns(2)
                    col1.download_button(
                        "⬇️ Decrypt & Download", decrypted_data, file_name=info["filename"], key=f"dl_{fid}")
                    if col2.button("🗑️ Delete from Cloud", key=f"del_{fid}"):
                        os.remove(info["cloud_path"])
                        del db["files"][fid]
                        log_event(db, user, "Deleted File", info["filename"])
                        save_db(db)
                        st.rerun()
        else:
            st.info("No files uploaded yet.")

        # Audit Logs
        st.markdown("### 🛡️ Security & Access Audit Logs")
        if db["logs"]:
            st.dataframe(db["logs"], use_container_width=True)

# 3. ACCESS SHARED LINK
elif menu == "🔗 Access Shared Link":
    st.subheader("🔗 Retrieve & Decrypt Shared Cloud File")
    token_input = st.text_input("Enter File Share ID (e.g., a1b2c3d4)")
    pwd_input = st.text_input(
        "Enter Share Password (if required)", type="password")

    if st.button("Verify & Decrypt File"):
        clean_id = token_input.replace("cloudshare://secure/", "").strip()
        if clean_id in db["files"]:
            file_info = db["files"][clean_id]
            req_pwd = file_info["share_password"]

            if req_pwd and hash_password(pwd_input) != req_pwd:
                st.error("❌ Incorrect share password! Access denied.")
            else:
                with open(file_info["cloud_path"], "rb") as ef:
                    decrypted_bytes = cipher.decrypt(ef.read())
                log_event(db, "Shared_Link_Guest",
                          "Downloaded Shared File", file_info["filename"])
                save_db(db)
                st.success(
                    f"✅ Access Granted! File **{file_info['filename']}** decrypted.")
                st.download_button("📥 Download Decrypted File",
                                   decrypted_bytes, file_name=file_info["filename"])
        else:
            st.error("❌ Invalid or expired Share ID.")
