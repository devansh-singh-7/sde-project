# Deploy On Vercel (Frontend + FastAPI Backend)

This repository is configured as a Vercel monorepo using `experimentalServices`.

## 1) Push repository to GitHub

Push your current branch to GitHub.

## 2) Import project in Vercel

1. Open Vercel dashboard.
2. Click **Add New Project**.
3. Select this repository.
4. Keep root directory as repository root.

Vercel will read root `vercel.json` and deploy:

- `frontend` service from `frontend`
- `backend` service from `backend`

## 3) Configure Environment Variables in Vercel

Set these for the **backend** service:

- `SECRET_KEY`
- `DATABASE_URL` (use MongoDB Atlas or another public MongoDB instance)
- `REDIS_URL` (use hosted Redis)
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (optional, defaults to app value)
- `OPENAI_API_KEY` (required if audio/video transcription path is used)
- `AWS_BUCKET_NAME` (optional)
- `AWS_ACCESS_KEY_ID` (optional)
- `AWS_SECRET_ACCESS_KEY` (optional)
- `AWS_REGION` (optional)

Optional backend vars:

- `MAX_FILE_SIZE_MB`

Set this for the **frontend** service (optional override):

- `VITE_API_BASE_URL=/_/backend/api/v1`

If not set, frontend already defaults to `/_/backend/api/v1`.

## 4) Deploy

Trigger deploy in Vercel. Once complete:

- frontend routes are at `/`
- backend routes are at `/_/backend`
- API routes are at `/_/backend/api/v1/...`

## 5) Important runtime notes

- Vercel serverless filesystem is ephemeral. Files in `/tmp/uploads` are not durable between invocations.
- Local FAISS index files are also ephemeral in serverless.
- For production durability, store uploaded files and vector indices in external storage/services.
- Long-running transcription tasks may exceed serverless limits for very large media.