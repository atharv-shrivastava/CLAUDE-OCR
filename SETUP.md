# PARAKH OCR UI - Setup & Deployment Guide

Full local OCR pipeline with React frontend. Upload or snap a photo of an Indian food pack label, extract fields in real-time.

## Quick Start (Local Development)

### 1. Install Backend Dependencies

```bash
# Navigate to the project directory
cd parakh-ocr-ui

# Install Python dependencies
pip install -r requirements.txt --break-system-packages
```

(First run downloads PaddleOCR models ~100-300MB, one-time only.)

### 2. Start the Flask Backend

```bash
python app.py
```

You'll see:
```
Initializing OCR engine (downloading models on first run, may take a minute)...
OCR engine ready
 * Running on http://0.0.0.0:5000
```

### 3. Open the Frontend

In any modern browser, open:
```
file:///path/to/parakh-ocr-ui/index.html
```

Or serve it via HTTP for mobile access:
```bash
# Python 3.10+
python -m http.server 8000 --directory /path/to/parakh-ocr-ui
# Then open: http://localhost:8000
```

---

## File Structure

```
parakh-ocr-ui/
├── app.py                 # Flask backend (main entry point)
├── index.html             # React frontend (opens in browser)
├── frontend.jsx           # React source (for reference only)
├── requirements.txt       # Python dependencies
├── extraction_lib/        # OCR + field extraction modules
│   ├── ocr_engine.py
│   ├── field_extractor.py
│   └── pipeline.py
├── SETUP.md              # This file
└── README.md             # Technical overview
```

---

## How It Works

1. **Upload or Camera Snap**
   - Click "Upload Image" to select a file from your phone/computer
   - Or tap "Camera" to snap a photo directly

2. **Backend Processing**
   - Image is sent to Flask backend (`POST /extract`)
   - PaddleOCR extracts text from the image (runs entirely locally, ~2-5 seconds)
   - Field extractor parses 11 structured fields (FSSAI, MRP, dates, batch no, etc.)

3. **Frontend Display**
   - Each extracted field shows:
     - **Value**: What was found (e.g., "₹20")
     - **Raw**: Exact OCR text (e.g., "MRP ₹20 incl of all taxes")
     - **Confidence**: 0-100% quality score
     - **Evidence**: Why we picked it
     - **Meaning**: Plain-English explanation (click "What does this mean?")

---

## Deployment Options

### Option A: Local Computer (Fastest for Testing)

Just follow the Quick Start above. Works on Windows/Mac/Linux.

### Option B: Raspberry Pi or ARM Server

Same setup. Note: PaddleOCR is CPU-intensive — expect ~10-15 seconds per image on Pi4 (vs ~2-5s on modern laptop). For production, consider:
- Running headless (backend only), access via mobile from the same WiFi
- Batch processing images (send multiple, process queue)

### Option C: Docker Container (Production)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

Build & run:
```bash
docker build -t parakh-ocr .
docker run -p 5000:5000 parakh-ocr
```

Then open `http://<your-server-ip>:5000` in a browser on your phone or computer.

### Option D: Cloud Deployment (AWS/GCP/Render)

- **Render.com** (free tier): Upload the Docker image, set PORT env var to 5000
- **Railway.app**: Similar to Render, supports Python natively
- **AWS Lambda + API Gateway**: Overkill, cold-start latency sucks for 5s OCR

Note: Free tiers have limited RAM. PaddleOCR uses ~300-500MB at runtime, so you need at least 512MB available.

---

## Configuration

### Backend API URL

Frontend defaults to `http://localhost:5000`. If your backend is elsewhere:
1. Open `index.html` in browser
2. Enter your backend URL in the "Backend API URL" field at the top
3. It's saved to browser localStorage, won't ask again

### OCR Language

Default is English (`lang='en'`). Indian packs often mix Hindi/regional scripts.

To add Hindi support:
1. Edit `app.py`, change line:
   ```python
   ocr_engine = OCREngine(lang='hi')  # or 'en' / 'hi' / 'pa' / etc.
   ```
2. Restart backend

For multi-language (English + Hindi), run two OCR passes and merge results — see extraction_lib/ocr_engine.py comments.

### API Endpoints

**POST /extract**
- Upload an image file
- Returns: `{success, ocr_text, fields}`
- Max file: 16MB

**POST /extract/text**
- Debug only: pass raw OCR text, get fields
- Useful for testing regex without image

**GET /health**
- Returns: `{status: "ok"}`

---

## Troubleshooting

### "Could not access camera"
- Browser permissions: Allow camera access when prompted
- HTTPS required: Use `https://` if on non-localhost (or `file://` for local HTML)
- Not supported: Camera doesn't work in some private browsing modes

### "No fields extracted"
- Poor image quality: Try better lighting, less glare
- Label isn't fully visible: Make sure pack back/front faces camera
- Wrong language: If label is in Hindi/regional script, need to restart backend with `lang='hi'`

### Backend crashes with "OutOfMemory"
- PaddleOCR needs ~300-500MB free RAM
- Close other apps
- Or consider pre-resizing large images (>5MB) before upload

### "Connection refused"
- Backend not running: Check `python app.py` output
- Wrong API URL: Verify in frontend settings (top of page)
- Firewall blocking: If on mobile, make sure phone and backend are on same WiFi

---

## Performance

Typical latencies (local laptop):
- Small image (<1MB): 2-3 seconds
- Large image (5MB+): 4-8 seconds

Breakdown:
- Image upload: <1s
- OCR (text detection): 1-3s
- Field extraction (regex): <100ms
- API response: ~50ms

---

## Next Steps / Future Improvements

- [ ] **Batch processing**: Accept multiple packs, process queue
- [ ] **Multi-language auto-detect**: Auto-switch OCR lang per image
- [ ] **Barcode scan validation**: Compare OCR barcode against actual EAN checksum
- [ ] **Image preprocessing**: Auto-rotate, de-skew, sharpen before OCR
- [ ] **Mobile app**: Native React Native app (if you want installable .apk)
- [ ] **Database integration**: Save extractions to PostgreSQL (PARAKH's DB)
- [ ] **Webhook callbacks**: POST results to PARAKH backend when done

---

## Support

- **Backend issues**: Check `app.py` logs
- **Frontend issues**: Browser console (`F12` → Console tab)
- **OCR accuracy**: See README.md in extraction_lib for regex tweaks
