# AI Q&A Application

A full-stack application that allows users to upload documents and multimedia files, process them, and ask questions about their content using AI.

## Architecture

This project is structured as a monorepo containing a React frontend and a FastAPI backend.

- **Frontend:** React 19, TypeScript, Vite, Tailwind V4, React Query
- **Backend:** Python, FastAPI, MongoDB (Motor/Beanie ORM), Redis
- **AI Integration:** Google Gemini API for document intelligence and chat
- **File Processing:** Document ingestion (`pdfplumber`) and audio handling (`pydub`)

## Prerequisites

- Node.js (v18+)
- Python (3.10+)
- MongoDB instance (local or Atlas)
- Redis server
- Google Gemini API Key

## Getting Started

### 1. Environment Variables

Create a `.env` file in the root of the project with the following required values:

```env
# Application
PROJECT_NAME="AI Q&A App"
SECRET_KEY="generate-a-secure-random-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL="mongodb+srv://..."
MONGO_USER="user"
MONGO_PASSWORD="password"
MONGO_DB="ai_qa_db"

# Cache/Rate Limiting
REDIS_URL="redis://localhost:6379/0"

# AI Models
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL="gemini-2.5-flash"
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```
The backend API will run on `http://127.0.0.1:8000`. API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
The frontend application will be available at `http://localhost:5173`. Any API calls to `/api/v1/*` are automatically proxy-rewritten to the FastAPI backend.

## Deployment

This repository is pre-configured for deployment on Vercel as a monorepo. The configuration (`vercel.json`) dynamically routes traffic to the Vite static build or the Python Serverless Function.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

When deploying on Vercel, ensure you add all environment variables in the Vercel dashboard. The application will route file uploads to Vercel's temporary `/tmp/uploads` directory automatically.