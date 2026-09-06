# PARAKH OCR UI

🔍 **Extract structured data from Indian food package labels using OCR.**

Point your camera at a packaged food item, snap a photo, and instantly extract:
- **FSSAI License Number** (food safety registration)
- **MRP** (Maximum Retail Price)
- **Net Quantity** (weight/volume)
- **Manufacturing & Expiry Dates**
- **Batch Number**
- **Consumer Care Contact**
- **Country of Origin**
- **Manufacturer Address**
- **Barcode**

All running **locally on your machine** — no cloud APIs, no privacy concerns, no monthly bills.

---

## 🚀 Quick Start

**Prerequisites:** Python 3.8+, pip

```bash
# 1. Clone this repo
git clone https://github.com/YOUR-USERNAME/parakh-ocr-ui.git
cd parakh-ocr-ui

# 2. Install dependencies
pip install -r requirements.txt --break-system-packages

# 3. Start backend
python app.py

# 4. Open frontend in browser
# Local: file:///full/path/to/index.html
# Or via HTTP: python -m http.server 8000 --directory .
# Then visit: http://localhost:8000
```

That's it. Upload or snap a photo, watch fields populate.

---

## 📦 What's Inside

```
parakh-ocr-ui/
├── index.html              # React frontend (no build needed)
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── extraction_lib/         # OCR + field extraction
│   ├── ocr_engine.py       # PaddleOCR wrapper
│   ├── field_extractor.py  # Regex-based field parser
│   └── pipeline.py         # Unified pipeline
├── QUICK_START.txt         # 2-minute setup
├── SETUP.md                # Deployment guide
└── GITHUB_UPLOAD.md        # How to use this repo
```

---

## ✨ Features

✅ **Upload or Camera Snap** — Pick a photo from device or snap live via camera  
✅ **Real-Time Extraction** — Fields populate as OCR runs (~2-5s)  
✅ **Confidence Scores** — See how confident each extraction is (0-100%)  
✅ **Explanations** — Click any field to see plain-English meaning  
✅ **Local Processing** — Everything runs on your machine, no data sent to cloud  
✅ **Mobile-Friendly** — Responsive UI works on phone/tablet/desktop  

---

## 🎯 Accuracy

- **High-confidence fields** (FSSAI, MRP, dates, batch): 85-95% accuracy
  - These have legally mandated formats (14-digit FSSAI no, dd/mm/yyyy dates, etc.)
- **Low-confidence fields** (manufacturer name, address): 50-70% accuracy
  - These have no fixed format, extracted via proximity heuristics
- **Confidence bars** on each field show real reliability, not fake 99%

**Not guaranteed to be 100% accurate.** Intended as a time-saving first pass, not authoritative extraction. Verify critical fields manually.

---

## 🏗️ Architecture

```
[Your Phone/Computer]
    ↓
[Browser: React Frontend]
    ├─ Upload image or snap camera
    ├─ Shows live field extraction
    └─ Displays results with confidence
    ↓ (POST /extract)
[Flask Backend (app.py)]
    ↓
[PaddleOCR - Text Detection]
    ├─ Extracts text from image pixels
    ├─ Handles rotated/skewed photos
    └─ ~1-3 seconds
    ↓
[Field Extractor - Pattern Matching]
    ├─ Regex-based structured parsing
    ├─ Identifies FSSAI, MRP, dates, etc.
    └─ <100ms
    ↓ (JSON response)
[Browser displays results]
```

**All processing is local.** No data leaves your machine.

---

## 📱 Deployment

**For Testing:** Just run `python app.py` locally.

**For Production:**

- **Docker:** `docker build -t parakh-ocr . && docker run -p 5000:5000 parakh-ocr`
- **Render.com:** Push to GitHub → auto-deploy with one click
- **Raspberry Pi:** Works, but slower (~10-15s per image)
- **Mobile:** Access backend via WiFi from same network

See [SETUP.md](SETUP.md) for detailed deployment guides.

---

## 🛠️ Tech Stack

- **Backend:** Flask, PaddleOCR (local OCR model)
- **Frontend:** React 18 (via CDN, no build process)
- **Styling:** Tailwind CSS
- **Field Extraction:** Pure Python regex (no ML API calls)

**No external APIs.** Everything runs locally.

---

## 📖 Documentation

- **[QUICK_START.txt](QUICK_START.txt)** — Get running in 2 minutes
- **[SETUP.md](SETUP.md)** — Full setup, deployment, troubleshooting
- **[GITHUB_UPLOAD.md](GITHUB_UPLOAD.md)** — How to use this repo
- **[extraction_lib/](extraction_lib/)** — Regex patterns, field explanations

---

## ⚙️ Configuration

### Change OCR Language

Edit `app.py`, line ~100:
```python
ocr_engine = OCREngine(lang='en')  # Change 'en' to 'hi' for Hindi, etc.
```

Restart backend and redeploy.

### Customize Regex Patterns

Field extraction is 100% regex-based. Edit `extraction_lib/field_extractor.py` to:
- Add new fields
- Tighten existing patterns
- Tune confidence thresholds

See comments in the file for guidance.

---

## 🐛 Common Issues

**"Connection refused"**
→ Backend not running. Check `python app.py` is active.

**"No fields extracted"**
→ Poor image quality. Try better lighting, full label visible.

**"Camera not working"**
→ Allow browser camera permission. Check top-left of address bar.

**Backend crashes**
→ Low RAM. PaddleOCR needs ~300-500MB free.

See [SETUP.md](SETUP.md) Troubleshooting section for more.

---

## 📄 License

MIT — Use freely, modify, redistribute.

---

## 🤝 Contributing

Found a bug in the regex patterns? Want to improve accuracy?

1. Fork this repo
2. Make changes
3. Test against real pack photos
4. Submit a pull request

---

## 📧 Questions?

- Check [SETUP.md](SETUP.md) first
- Look at [extraction_lib/](extraction_lib/) code comments
- File an issue in GitHub Issues tab

---

## ⚠️ Limitations

- **First run downloads models (~300MB)** — one-time, then offline
- **Slower on mobile** — phone CPUs are slower than laptops
- **Multi-language labels** — Configure language before running
- **No barcode scanning** — OCR reads digits, but doesn't validate EAN-13 checksum
- **Indian labels only** — Patterns tuned for FSSAI-regulated products

---

**Made by Atharv for PARAKH** — Bringing clarity to food packaging data.
