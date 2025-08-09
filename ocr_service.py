from flask import Flask, request, jsonify
import requests
from utils import decode_base64_image
from io import BytesIO
import os

OCR_SPACE_API_KEY = os.getenv('OCR_SPACE_API_KEY', 'TU_API_OCR_SPACE')

app = Flask(__name__)

def translate_text(text, target="en"):
    # Ejemplo: traduce usando Google Translate API REST o similar (puedes cambiar por DeepL)
    # Aquí es solo un mock (retorna igual). Integra una API real si lo deseas.
    return text

@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.get_json()
    img_b64 = data.get('image', '')
    prompt = data.get('prompt', '')

    # Utiliza OCR.space
    img = decode_base64_image(img_b64)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    files = {'file': ('image.png', buf, 'image/png')}
    res = requests.post(
        'https://api.ocr.space/parse/image',
        files=files,
        data={"apikey": OCR_API_KEY, "language": "spa", "OCREngine": 2},
    )
    if res.ok:
        result = res.json()
        parsed = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
        # Clasificación simple
        doc_type = "texto simple"
        if "Total" in parsed or "RUT" in parsed: doc_type = "documento/factura"
        if "=" in parsed or "x" in parsed or "y" in parsed: doc_type = "expresión matemática"
        # Detectar tablas (muy simple)
        table_data = None
        if "\t" in parsed or ("|" in parsed and "-" in parsed):
            table_data = [row.split() for row in parsed.strip().split('\n') if row]
        # Traducción automática
        translation = translate_text(parsed, target="en")
        response = {
            "text": parsed.strip(),
            "type": doc_type,
            "translation": translation,
            "table": table_data
        }
        return jsonify(response)
    else:
        return jsonify({"text": "No se pudo leer el texto de la imagen."}), 400

if __name__ == "__main__":
    app.run(port=5001, debug=True)
