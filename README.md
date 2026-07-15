# SmartFOD

AI-Powered Foreign Object Detection Assistant — Core MVP for the SIAE Aviation Safety Competition 2026 proposal.

Compares before/after photos of a maintenance work area using Claude's vision capability, flags potential Foreign Object Debris (FOD), and generates a digital, PDF-exportable FOD Clearance Record linked to a job card.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Your Anthropic API key is already in `.env` (git-ignored). If you need to reset it, copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`.

## Run

```bash
streamlit run app.py
```

## Workflow

1. **New Scan** — enter job card number + task description, upload a "before" photo and an "after" photo.
2. Click **Run FOD Scan** — Claude compares the two images and flags any new items (tools, fasteners, rags, hardware) with a risk level.
3. Enter technician name and **Sign Off & Save Record** — persists the record to `data/clearance_log.json` and saved images to `data/images/`.
4. **Download Clearance Record (PDF)** — printable certificate with job card, findings, and photos.
5. **History** tab — browse and re-download past clearance records.

## Deploying to Streamlit Community Cloud

1. Push this folder to a GitHub repo (`.env` and `data/` are git-ignored, so your key and local records won't be committed).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **New app**, and point it at this repo with main file `app.py`.
3. In the app's **Settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "your-key-here"
   ```
   (see `.streamlit/secrets.toml.example` for the format — `app.py` automatically falls back to `st.secrets` when `ANTHROPIC_API_KEY` isn't in the environment).
4. Deploy — you'll get a public `https://*.streamlit.app` URL, usable from any browser including mobile.

Note: `data/` (the JSON log + saved images) is git-ignored and lives only on the deployed container's disk — it will reset on redeploys/restarts. Fine for demos; for persistent storage across redeploys you'd want an external database or object storage, which is out of scope for this MVP.

## Not yet built (deferred from the full proposal)

- FOD risk dashboard / trend charts (plotly)
- Offline-ready photo capture with queued AI analysis
- Replit deployment config

## Project Structure

```
app.py              Streamlit entrypoint
fod/vision.py        Anthropic API vision comparison
fod/records.py       JSON-backed session log
fod/pdf.py           ReportLab clearance record PDF generator
data/                Runtime session log + images (git-ignored)
```
