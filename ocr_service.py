# -*- coding: utf-8 -*-
import os
from io import BytesIO
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils import decode_base64_image

OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")

app = Flask(__name__)
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/ocr", methods=["POST"])
def ocr():
    """
    Body: { "image": "data:image/png;base64,...", "prompt": "opcional" }
    """
    if not OCR_SPACE_API_KEY:
        return jsonify({"error": "Falta OCR_SPACE_API_KEY en el entorno"}), 500

    data = request.get_json(force=True, silent=True) or {}
    img_b64 = data.get("image", "")
    if not img_b64:
        return jsonify({"error": "Debes enviar 'image' (base64)"}), 400

    try:
        img = decode_base64_image(img_b64)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        files = {"file": ("image.png", buf, "image/png")}
        res = requests.post(
            "https://api.ocr.space/parse/image",
            files=files,
            data={"apikey": OCR_SPACE_API_KEY, "language": "spa", "OCREngine": 2},
            timeout=60
        )
        if not res.ok:
            return jsonify({"error": "No se pudo leer la imagen."}), 400

        result = res.json()
        parsed = result.get("ParsedResults", [{}])[0].get("ParsedText", "")

        doc_type = "texto simple"
        if "Total" in parsed or "RUT" in parsed:
            doc_type = "documento/factura"
        if any(s in parsed for s in ["=", "x", "y"]):
            doc_type = "expresión matemática"

        translation = parsed[::-1]  # MOCK de traducción

        return jsonify({
            "text": parsed.strip(),
            "type": doc_type,
            "translation": translation
        })
    except Exception as e:
        return jsonify({"error": f"Fallo OCR: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
