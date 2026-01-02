# DocDiff MVP (2-day demo starter)

Minimal, no-fluff starter to compare two PDFs (before/after) and surface:
- Text diffs (line-level)
- Coarse style diffs (font/size distribution changes)
- Visual page-level diffs (SSIM score)

> Scope: **native PDFs**. OCR, semantic NLI, and DOCX are out-of-scope for this MVP but the backend is structured to add them later.

---

## Prereqs
- Python 3.10+ (3.11 recommended)
- Node.js 18+
- macOS/Linux/WSL is fine. Windows works too.

## Setup — Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
./run.sh  # or: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Server starts on http://localhost:8000

Health check:
```bash
curl http://localhost:8000/health
```

## Setup — Frontend
```bash
cd frontend
cp .env.example .env  # adjust backend URL if needed
npm install
npm run dev
```
App opens on http://localhost:5173

## Using the app
1. Open the frontend, upload **Before** and **After** PDFs.
2. Click **Compare**.
3. Read diffs: text changes, style distribution deltas, and a per-page visual-change signal (SSIM).

## API (quick test without UI)
```bash
curl -X POST http://localhost:8000/compare       -F "before_file=@/path/to/before.pdf"       -F "after_file=@/path/to/after.pdf"
```

## What’s next after MVP
- **Better style diff**: token-level runs grouped into spans; detect bold/italic shifts per line.
- **Graphics diff**: extract images & pHash change.
- **Layout diff**: block bounding boxes and movement vectors.
- **Semantics**: NLI model + rules for policy fields; confidence gating.
- **OCR**: dual OCR pipeline for scans (PaddleOCR + Tesseract); coord-level tokens.

## Notes
- For large PDFs, SSIM uses a downscaled grayscale comparison per page (threshold 0.995).
- Font/size diff is intentionally coarse for demo clarity. It will flag “font universe changed on this page” rather than every span.
- The code is cleanly split so you can extend without refactors.
