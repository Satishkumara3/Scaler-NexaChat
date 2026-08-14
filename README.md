# Scaler Chat — Signal-Inspired Messaging Platform

> A real-time secure messaging platform built with Next.js, FastAPI, SQLite, and WebSockets.

---

## 🗂️ Project Structure

```
Scaler_AI_Chat_Application/
├── backend/      FastAPI + SQLite + WebSockets
└── frontend/     Next.js 16 + TypeScript
```

---

## ⚡ Quick Start

### Prerequisites
- **Python 3.11+**  (`python --version`)
- **Node.js 18+** (`node --version`)
- **npm 9+** (`npm --version`)

---

### 1. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
copy .env.example .env     # Windows
cp .env.example .env       # macOS/Linux

# Start the server
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**  
Swagger UI: **http://localhost:8000/docs**  
Health check: **http://localhost:8000/health**

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies (already done if cloning fresh)
npm install

# Copy environment config
copy .env.example .env.local   # Windows
cp .env.example .env.local     # macOS/Linux

# Start the dev server
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## 🔎 Verification Checklist

After starting both servers:

- [ ] `http://localhost:8000` → `{"message": "Scaler Chat API is running 🚀"}`
- [ ] `http://localhost:8000/health` → `{"status": "ok", "database": {...}}`
- [ ] `http://localhost:3000` → Scaler Chat landing page
- [ ] Frontend page has a link to the backend health endpoint

---

## 🧪 Running Tests

```bash
cd backend

# Activate venv first, then:
pytest -v
```

---

## 🧹 Useful Commands

### Backend
| Command | Description |
|---|---|
| `uvicorn main:app --reload` | Start with hot-reload |
| `pytest -v` | Run all tests |
| `python -c "import secrets; print(secrets.token_hex(32))"` | Generate SECRET_KEY |

### Frontend
| Command | Description |
|---|---|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run lint` | ESLint check |

---

## 🏗️ Implementation Phases

| Phase | Status | Description |
|---|---|---|
| **1** | ✅ Done | Foundation — project scaffold, DB init, health check, WS scaffold, API client |
| **2** | ✅ Done | Auth (register, OTP, login/logout), Contacts, Conversations, Messages (HTTP) |
| **3** | ✅ Done | Real-time WebSocket — direct message delivery, presence, and session sync |
| **4** | ✅ Done | Receipts and Typing — message delivery/read receipts, typing indicators |
| **5** | ✅ Done | Group conversations — admin controls, member management, group messaging |
| **6** | ✅ Done | UI/UX Polish — Signal-inspired dark/glassmorphic interface and responsiveness |
| **7A** | ✅ Done | Message Attachments — image and file uploads with secure filesystem storage |
| **7B** | ✅ Done | Message Replies & Reactions — nested replies, emoji reactions and WS broadcast |
| **8** | ✅ Done | QA & Stabilization — thorough test-suite stabilization (59 tests), security audit |
| **9** | ✅ Done | Submission Preparation — README, documentation, and deployment guides |

---

## ✨ Features

* **Real-time Messaging**: Fast WebSocket dispatch for instant text and attachment messaging.
* **Authentication**: Secure JWT-based HttpOnly session cookies.
* **Groups**: Member invites, admin roles, and real-time member addition/removal broadcasts.
* **Rich Interactions**: Typings indicators, delivery/read receipts, replies, and emoji reactions.
* **File Attachments**: Upload and securely download image/pdf attachments (max 10 MB).
* **Modern Interface**: Tailored dark-mode glassmorphic interface inspired by Signal. 

---

## 🚀 Deployment Guide

### Backend (Docker/Vercel/Render)
1. **Render/Railway**: 
   * Connect your GitHub repository to Render/Railway.
   * Provide the Build command: `pip install -r requirements.txt`
   * Provide the Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   * Set environment variables in the dashboard: `SECRET_KEY`, `CORS_ORIGINS="https://your-frontend.vercel.app"`.
   * Note: SQLite writes to disk; for persistent data across deployments, you must map a persistent volume to the root directory where `dev.db` and the `/uploads` folder reside, or migrate your SQLAlchemy models to a managed PostgreSQL cluster in production.

### Frontend (Vercel/Netlify)
1. **Vercel**:
   * Connect your repository and select the `frontend/` directory as the Root Directory.
   * Framework Preset: Next.js.
   * Environment Variables: Set `NEXT_PUBLIC_API_URL` to your deployed backend URL.
   * Deploy!

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Zustand, SWR, Axios |
| Backend | Python, FastAPI, uvicorn, aiosqlite, Pydantic v2 |
| Database | SQLite (via aiosqlite) |
| Real-time | WebSockets (FastAPI native) |
| Auth | JWT in HttpOnly session cookies |

---

## 📁 Architecture

See [architecture_plan.md](../architecture_plan.md) for full design documentation.
