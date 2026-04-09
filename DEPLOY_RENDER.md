# Render Deployment

This repo is prepared for a single free Render web service that:

- builds the React frontend
- serves it from the FastAPI backend
- keeps uploads and embeddings in temporary storage
- uses a hosted Hugging Face model in production

## Free Tier Tradeoff

The `render.yaml` is now configured for Render's `free` plan. That means:

- the app deploys without a paid persistent disk
- uploaded PDFs and in-memory document state are temporary
- files can disappear after a restart, redeploy, or cold start

If you want document persistence later, switch the service to a paid plan and mount a disk again.

## Why Hugging Face instead of Ollama on Render

The local Ollama setup works on this machine only with smaller models. On Render, a hosted Hugging Face model is the more practical production path because:

- Render web services do not include your local Ollama runtime
- local models need more RAM and storage than this free setup should assume
- hosted inference keeps the web service lighter

## Files Used

- `Dockerfile`
- `render.yaml`
- `backend/app/main.py`

## Deploy Steps

1. Push this code to your GitHub repo.
2. In Render, choose `New +` -> `Blueprint`.
3. Connect the GitHub repo that contains this `render.yaml`.
4. Render will create the web service automatically.
5. In the service environment variables, set `HUGGINGFACE_API_KEY`.
6. Deploy.

## Important Settings

- Health check path: `/api/health`
- Frontend root: `/`
- API base path: `/api`
- Upload storage: `/tmp/rajeshgpt/uploads`
- Embeddings storage: `/tmp/rajeshgpt/embeddings`

## Expected Result

After deploy:

- `/` serves the React UI
- `/api/*` serves the backend endpoints
- direct browser refreshes on frontend routes keep working
- uploaded files work during the current container lifetime

## Notes

- Free Render services can sleep after inactivity, so the first request may be slow.
- If you need durable uploads, use a paid plan with a persistent disk or move files to external object storage.
