# Render Deployment

This repo is prepared for a single free Render web service that:

- builds the React frontend
- serves it from the FastAPI backend
- keeps uploads and embeddings in temporary storage
- uses a hosted Hugging Face Inference Providers chat model in production

## Free Tier Tradeoff

The `render.yaml` is now configured for Render's `free` plan. That means:

- the app deploys without a paid persistent disk
- server-local files can disappear after a restart, redeploy, or cold start
- browser-saved documents and chat history persist in the user's browser on the same device
- uploaded PDFs are re-used from browser storage during future queries, so the app no longer depends on server-local PDF persistence for normal single-user use

If you want team-wide shared persistence later, switch to a paid plan with a disk or move files to external object storage/database storage.

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

## Token Scope

Use a Hugging Face fine-grained token with permission to make inference calls for the selected model. If the deployed app shows authentication or permission errors, rotate the token and make sure inference access is enabled for the model you chose.

## Important Settings

- Health check path: `/api/health`
- Frontend root: `/`
- API base path: `/api`
- Upload storage: `/tmp/rajeshgpt/uploads`
- Embeddings storage: `/tmp/rajeshgpt/embeddings`
- Default chat model: `openai/gpt-oss-20b:cheapest`

## Expected Result

After deploy:

- `/` serves the React UI
- `/api/*` serves the backend endpoints
- direct browser refreshes on frontend routes keep working
- uploaded files and chat history stay available in the same browser across free-tier restarts
- document-backed queries work by sending browser-cached document chunks back to the API

## Notes

- Free Render services can sleep after inactivity, so the first request may be slow.
- Browser persistence is per browser/profile, not shared across devices.
- If you need durable shared uploads, use a paid plan with a persistent disk or move files to external object storage.
