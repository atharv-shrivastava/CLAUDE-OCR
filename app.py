"""
Flask backend for PARAKH OCR module.
Exposes the Python OCR + field extraction pipeline as a REST API.
"""

import os
import tempfile
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add extraction_lib to path so we can import our OCR modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'extraction_lib'))

from ocr_engine import OCREngine
from field_extractor import extract_all_fields

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize OCR engine once, reuse across requests
ocr_engine = None


def init_ocr():
    global ocr_engine
    if ocr_engine is None:
        print("Initializing OCR engine (downloading models on first run, may take a minute)...")
        ocr_engine = OCREngine(lang='en')
        print("OCR engine ready")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


FIELD_EXPLANATIONS = {
    "fssai_number": (
        "This is the food business's license number issued by FSSAI "
        "(Food Safety and Standards Authority of India). Every packaged "
        "food sold in India is legally required to print this 14-digit "
        "number. You can look it up on the FSSAI portal to verify who's "
        "actually licensed to sell this product."
    ),
    "mrp": (
        "Maximum Retail Price — the highest price the seller is legally "
        "allowed to charge you for this item, inclusive of all taxes. "
        "Selling above this is a violation."
    ),
    "net_quantity": (
        "The actual amount of product inside the pack (by weight or "
        "volume), not counting the packaging itself."
    ),
    "mfg_date": (
        "The date the product was manufactured or packed. Used together "
        "with the expiry/best-before info to judge freshness."
    ),
    "expiry_date": (
        "Either a fixed 'use by' date, or a shelf-life duration counted "
        "from the manufacturing date (e.g. '6 months from mfg'). If it's "
        "a duration, you need the mfg_date too to know the actual cutoff."
    ),
    "batch_number": (
        "An internal production-batch code. Mainly useful for recalls — "
        "if a batch is found unsafe, this number identifies which units "
        "are affected."
    ),
    "consumer_care_phone": (
        "Phone number to contact if there's a complaint or safety issue "
        "with the product."
    ),
    "consumer_care_email": (
        "Email address for the same purpose as consumer care phone."
    ),
    "country_of_origin": (
        "Where the product was actually made — required disclosure, "
        "especially relevant for imported goods."
    ),
    "barcode_candidate": (
        "A 12-13 digit number that looks like a barcode (EAN-13/UPC-A). "
        "Flagged as a candidate only — OCR reads printed digits, it "
        "doesn't scan the actual barcode, so this should be cross-checked "
        "against a real barcode scan if accuracy matters."
    ),
    "manufacturer_block": (
        "Name and address of whoever manufactured, packed, or imported "
        "the product — legally required so the responsible party is "
        "traceable."
    ),
}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/extract', methods=['POST'])
def extract():
    """
    POST /extract
    Takes an image file, extracts OCR text, parses fields.
    Returns: {
        "success": bool,
        "error": str (only if success=false),
        "ocr_text": str,
        "fields": {
            "field_name": {
                "value": <value or null>,
                "raw": <raw OCR string>,
                "confidence": <0-1>,
                "evidence": <why we picked it>,
                "meaning": <plain English explanation if value exists>
            }
        }
    }
    """
    try:
        # Check if an image file was provided
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided. Send a 'file' form field with an image."
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "File has no name."
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        # Save uploaded file to temp directory
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Run OCR
        ocr_result = ocr_engine.extract(filepath)
        fields = extract_all_fields(ocr_result.full_text)

        # Attach meanings to fields that matched
        for name, data in fields.items():
            if data['value'] is not None:
                data['meaning'] = FIELD_EXPLANATIONS.get(name, "")

        # Clean up temp file
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify({
            "success": True,
            "ocr_text": ocr_result.full_text,
            "fields": fields,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/extract/text', methods=['POST'])
def extract_text():
    """
    POST /extract/text (for testing without an image)
    Takes raw text via 'text' form field or JSON body.
    Returns the same field structure as /extract.
    """
    try:
        text = None
        if request.is_json:
            text = request.json.get('text', '')
        else:
            text = request.form.get('text', '')

        if not text:
            return jsonify({
                "success": False,
                "error": "No text provided."
            }), 400

        fields = extract_all_fields(text)
        for name, data in fields.items():
            if data['value'] is not None:
                data['meaning'] = FIELD_EXPLANATIONS.get(name, "")

        return jsonify({
            "success": True,
            "ocr_text": text,
            "fields": fields,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    init_ocr()
    # Run on 0.0.0.0:5000 so it's accessible from frontend
    app.run(debug=False, host='0.0.0.0', port=5000)
