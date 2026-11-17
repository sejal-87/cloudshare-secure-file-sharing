# ☁️ CloudShare – Secure Cloud-Based File Sharing System

A secure, end-to-end encrypted cloud file-sharing web application built with **Python** and **Streamlit**. CloudShare allows authenticated users to encrypt files using **Fernet AES-128 cryptography**, store them in a protected cloud vault, share them via unique **UUID access tokens** with optional password protection, and monitor activity through real-time security audit logs.

---

## 🚀 Key Features

* **🔐 User Authentication:** Secure registration and login powered by **SHA-256 cryptographic password hashing** and session state management.
* **🛡️ End-to-End File Encryption:** Automatically encrypts uploaded files (`PDF`, `DOCX`, `PNG`, `JPG`, `TXT`, `ZIP`) using **Fernet AES-128** symmetric encryption before writing to the cloud vault.
* **🔗 Token-Based Secure Sharing:** Generates unique 8-character **UUID Share IDs** and secure URIs (`cloudshare://secure/<id>`) for controlled file distribution.
* **🔑 Optional Share Passwords:** Supports two-layer verification requiring both a valid Share ID and a hashed share password before on-demand decryption.
* **📊 Real-Time Security & Access Audit Logs:** Tracks every account registration, login, encrypted upload, shared download, and file deletion with exact timestamps.

---

## 🛠️ Technology Stack

* **Frontend & Web Framework:** Streamlit
* **Backend Language:** Python 3.13
* **Cryptography & Security:** `cryptography` (Fernet AES-128), `hashlib` (SHA-256), `uuid`
* **Metadata & Storage:** JSON Metadata Registry (`cloud_metadata_db.json`) & Encrypted Storage Vault (`cloud_storage_vault`)

---

## ⚙️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd cloudshare-secure-file-sharing
   ```

2. **Install required dependencies:**
   ```bash
   pip install streamlit cryptography
   ```

3. **Launch the application:**
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard:** Open your browser at `http://localhost:8501`.

---

## 🔒 Security Architecture

* **Zero Plain-Text Passwords:** Both account passwords and file-share passwords are converted into irreversible SHA-256 digests.
* **Encryption at Rest:** All stored files remain encrypted as `.enc` binary blobs inside the cloud vault and are decrypted in memory only after access verification.
* **Key Isolation:** Master encryption keys (`master_encryption.key`) and private vault contents are excluded from version control via `.gitignore`.
