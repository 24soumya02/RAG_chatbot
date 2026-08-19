# Chat Assistant + Price Comparison with LangChain and Hugging Face

A Streamlit app that works as a normal chat assistant and as a price comparison tool. When the **Price comparison** toggle in the sidebar is off, the app just chats with conversation memory. When it's on, queries are answered with live web prices from DuckDuckGo, turned into a markdown comparison table across platforms and stores. Chat history is shown in the left sidebar.

## Setup

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set your Hugging Face token (create one at https://huggingface.co/settings/tokens):

```
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

The token is read from `.env` only — there is no token field in the UI.

## Run

The app runs on port **8500** (Streamlit's default is 8501):

```powershell
streamlit run app.py
```

The port is set in `.streamlit/config.toml`. You can override it on the command line:

```powershell
streamlit run app.py --server.port 8501
```

## Run with Docker

Build and run the image (pass your token via `--env-file`):

```powershell
docker build -t rag-chatbot .
docker run -p 8500:8500 --env-file .env rag-chatbot
```

Then open http://localhost:8500. To run in the background, add `-d` to the `docker run` command.

## Deploy to Streamlit Community Cloud

Streamlit Community Cloud (free) is the recommended host — it supports Streamlit's WebSockets and session state out of the box, and needs no Dockerfile.

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and click **Create app** → **Deploy a public app from GitHub**.
3. Pick the repo, branch (`main`), and main file (`app.py`), then click **Deploy**.
4. Set your secrets under **Settings → Secrets** in the app dashboard:
   ```
   HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
   ```
   You can also set `HF_MODEL_ID` and `HF_BASE_URL` there if you need to override the defaults.

The token is only read from environment variables — there is no token field in the UI.

## Deploy to Vercel

Streamlit normally needs a long-running server with WebSockets, which Vercel's serverless functions are not built for. This repo includes a working wrapper (`api/index.py` + `vercel.json`) that starts Streamlit inside a Vercel Python function and proxies HTTP + WebSocket traffic to it. It works for demos but has real limitations (see below).

1. Push this repo to GitHub.
2. Open your Vercel team's new-project page (e.g. `https://vercel.com/new`) and click **Import** on the GitHub repo.
3. Framework Preset should be **Other** (if Vercel complains it cannot find an `app` in the root `app.py`, this is the fix). Leave the build command empty.
4. Set environment variables under **Settings → Environment Variables**:
   ```
   HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
   ```
   Optionally add `HF_MODEL_ID` and `HF_BASE_URL` to override defaults.
5. Deploy. First load after a cold start can take 30–60s while Streamlit boots.

Required files for Vercel:

```
├── app.py            # the Streamlit app
├── requirements.txt  # deps (incl. fastapi, httpx, websockets for the wrapper)
├── vercel.json       # routes all traffic to the function
└── api/
    └── index.py      # FastAPI ASGI app that spawns Streamlit + proxies requests
```

### Vercel limitations (read before deploying)

- **Cold starts**: each time Vercel spins up a fresh instance, the whole Streamlit + LangChain stack must boot before the page loads — this can take a minute.
- **Session state is not guaranteed**: chat history lives in the function's memory; if Vercel routes you to a new instance or the function idles out, the conversation resets.
- **Timeouts**: price searches and Hugging Face LLM calls must finish within the function's max duration (300s here, and less on the Hobby plan). Slow LLM responses may time out.
- **WebSockets** must be enabled (Fluid compute) — this is the default for projects created on/after April 23, 2025.
- For a more reliable free host, prefer **Streamlit Community Cloud** (above) or Render/Railway with the included Dockerfile.

## How it works

1. With the **Price comparison** toggle off, messages are handled as a normal chatbot with conversation history.
2. With the toggle on, you type a product, e.g. `iPhone 15 128GB`:
   1. The app searches DuckDuckGo for `<product> price` (no API key needed).
   2. The model extracts prices from the results and returns a comparison table sorted from cheapest to most expensive, with a "Best pick:" recommendation.

## Notes

- Prices come from web search snippets, so accuracy depends on what the search engine returns.
- The app calls Hugging Face's free serverless inference via the OpenAI-compatible endpoint (`https://router.huggingface.co/v1`); it is rate-limited.
- Uses Python 3.12 (the LangChain 0.3 stack does not support Python 3.14 yet).
- If `Qwen/Qwen2.5-7B-Instruct` is gated/blocked, switch `HF_MODEL_ID` in `.env` to `mistralai/Mistral-7B-Instruct-v0.3` (no gating).
