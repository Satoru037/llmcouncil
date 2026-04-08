# 🏛️ LLM Council

**LLM Council** is a "Wisdom of Crowds" application for Large Language Models. It simulates a panel of AI experts (personas) who answer your question, peer-review each other's responses, and then synthesize a final, high-quality answer.


---

## ✨ Key Features

*   **Multi-Model Simulation:** Queries the Gemini API multiple times with different personas to diversity viewpoints.
*   **Automated Peer Review:** Each "model" critiques the others to catch hallucinations and bias.
*   **Sovereign Synthesis:** A "Chairman" model aggregates the reviews into a final consensus answer.
*   **Responsive UI:** Fully adaptive design for Desktop, Tablet, and Mobile.
*   **Session Persistence:** Automatically saves your conversations to local storage.
*   **Export & Management:** Delete sessions, view history, and export findings.

---

## 🛠️ Project Structure

The project is divided into two main parts:

*   **`client/`**: The frontend application (React, TypeScript, Vite, Tailwind CSS).
*   **`server/`**: The backend API (Python, FastAPI, Gemini SDK).

---

## 🚀 Quick Start (Windows)

We have included automated scripts to make setup a breeze.

### 1. Prerequisite
You must have **Node.js** and **Python** installed on your machine.

### 2. Setup
Double-click **`setup.bat`**.
*   This will create a Python virtual environment (`server/venv`).
*   It will install all Python dependencies.
*   It will install all Frontend dependencies (`node_modules`).

### 3. API Key Configuration
Create a file named `.env` inside the `server/` folder and add your Google Gemini API key:

Fetch the API key from: https://aistudio.google.com/app/api-keys
```ini
GEMINI_API_KEY=AIzaSy...YourKeyHere...
GEMINI_MODEL=gemini-2.5-pro
```
Fetch the custom key for Gemini 3 Pro Preview from: https://console.cloud.google.com/vertex-ai/studio/settings/api-keys?project={projectID}

```ini
GEMINI_CUSTOM_ENDPOINT=https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-3-pro-preview:streamGenerateContent
GEMINI_CUSTOM_KEY=...
```

### 4. Logging
*   **Console:** Logs are streamed to standard output.
*   **File:** Logs are also saved to `server/logs/app.log` for your records.
*   **Configuration:** Change `LOG_LEVEL` in `.env` to `DEBUG` for more detail.

### 5. Run
Double-click **`run_dev.bat`**.
*   This opens two terminal windows (one for Backend, one for Frontend).
*   Access the app at: **http://localhost:5173**

---

## 🔧 Manual Setup 

If you prefer to run commands manually:

### Backend
```bash
cd server
python -m venv venv
# Windows:
.\venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd client
npm install
npm run dev
```


