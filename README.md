<!-- @format -->

# 🏛️ LLM Council

**LLM Council** is a "Wisdom of Crowds" application for Large Language Models. It simulates a panel of AI experts (personas) who answer your question, peer-review each other's responses, and then synthesize a final, high-quality answer.

---

## ✨ Key Features

- **Multi-Model Simulation:** Queries the Gemini API multiple times with different personas to diversity viewpoints.
- **Automated Peer Review:** Each "model" critiques the others to catch hallucinations and bias.
- **Sovereign Synthesis:** A "Chairman" model aggregates the reviews into a final consensus answer.
- **Responsive UI:** Fully adaptive design for Desktop, Tablet, and Mobile.
- **Session Persistence:** Saves conversations in Turso (production) with automatic local SQLite fallback for development.
- **Export & Management:** Delete sessions, view history, and export findings.

---

## 🛠️ Project Structure

The project is divided into two main parts:

- **`client/`**: The frontend application (React, TypeScript, Vite, Tailwind CSS).
- **`server/`**: The backend API (Python, FastAPI, Gemini SDK).

---

## 🚀 Quick Start (Windows)

We have included automated scripts to make setup a breeze.

### 1. Prerequisite

You must have **Node.js** and **Python** installed on your machine.

### 2. Setup

Double-click **`setup.bat`**.

- This will create a Python virtual environment (`server/venv`).
- It will install all Python dependencies.
- It will install all Frontend dependencies (`node_modules`).

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

- **Console:** Logs are streamed to standard output.
- **File:** Logs are also saved to `server/logs/app.log` for your records.
- **Configuration:** Change `LOG_LEVEL` in `.env` to `DEBUG` for more detail.

### 5. Run

Double-click **`run_dev.bat`**.

- This opens two terminal windows (one for Backend, one for Frontend).
- Access the app at: **http://localhost:5173**

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

---

## Deployment (Render + Vercel)

This project is set up to run with:

- **Backend on Render** (FastAPI)
- **Frontend on Vercel** (Vite/React)
- **Vercel proxy rewrite** for `/api/*` requests to Render

### 1) Deploy Backend on Render

1. Create a new **Web Service** on Render from this repository.
2. Set these service options:

- Language: `Python 3`
- Branch: `main`
- Root Directory: `server`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. Add environment variables in Render:

```ini
GEMINI_API_KEY=...
GEMINI_CUSTOM_KEY=...
GEMINI_CUSTOM_ENDPOINT=...
GEMINI_MODEL=gemini-3.1-pro-preview
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
TURSO_DATABASE_URL=libsql://your-db-name-your-org.turso.io
TURSO_AUTH_TOKEN=...
```

Optional fallback for local SQLite (dev/testing only):

```ini
SESSIONS_DB_PATH=/opt/render/project/src/server/data/sessions.db
```

4. Deploy the Render service and copy the generated URL, for example:

`https://your-render-service.onrender.com`

Note: Render free tier does not include persistent disk. Use Turso variables above for durable data across restarts/redeploys.

### 1.1) Create Turso Database (for persistent sessions)

1. Create a database in Turso dashboard.
2. Open the database and copy the **Database URL** from the **Connect** section.
3. Click **Create Token** and create a **Read & Write** token.
4. Add both values to Render as:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

### 2) Deploy Frontend on Vercel

1. Import the same GitHub repository in Vercel.
2. Configure project:

- Root Directory: `client`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`

### 3) Configure Vercel Rewrite Target

The file `client/vercel.json` controls API proxying.

Current rule:

```json
{
	"rewrites": [
		{
			"source": "/api/(.*)",
			"destination": "https://YOUR-RENDER-HOST/api/$1"
		}
	]
}
```

Update `destination` to your Render public URL, commit, and redeploy Vercel.

### 4) Verify Deployment

1. Open frontend: `https://your-vercel-domain.vercel.app`
