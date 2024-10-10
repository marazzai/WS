from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# Cache per risorse statiche (immagini e font)
base_image = None
fonts_cache = {}

def get_base_image():
    """Carica e memorizza in cache l'immagine di base."""
    global base_image
    if base_image is None:
        base_image = Image.open("static/image.webp").convert("RGBA")
    return base_image.copy()

def get_font(name, size):
    """Carica e memorizza in cache i font."""
    key = f"{name}-{size}"
    if key not in fonts_cache:
        fonts_cache[key] = ImageFont.truetype(f"fonts/{name}.otf", size)
    return fonts_cache[key]

def calcola_data_scadenza(rendimento):
    """Calcola la data di scadenza in base al rendimento selezionato (14 o 21 giorni)."""
    giorni = 14 if '14gg' in rendimento else 21
    data_attuale = datetime.now()
    data_scadenza = data_attuale + timedelta(days=giorni)
    return data_scadenza.strftime("%d/%m/%Y")

def genera_codice_riferimento():
    """Genera un codice di riferimento unico basato sulla data e ora attuale."""
    now = datetime.now()
    return now.strftime("%d%m%Y%H%M")

# Funzione per caricare l'immagine su ImgBB
def carica_su_imgbb(image_data, api_key):
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": image_data,
        "expiration": "0"  # Nessuna scadenza
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()["data"]["url"]
    else:
        return None

# Home route con un form HTML per ricevere i dati
@app.route("/")
def home():
    return '''
        <h1>Generatore di Immagini Personalizzabile</h1>
        <form action="/genera_immagine" method="get">
            Nome: <input type="text" name="nome" value="Williams Jackob"><br><br>
            Importo: <input type="text" name="importo" value="40.000,00 $"><br><br>
            
            <label>Rendimento Promesso:</label><br>
            <input type="radio" id="basso_14gg" name="rendimento" value="BASSO 14gg (25%)" checked>
            <label for="basso_14gg">BASSO 14gg (25%)</label><br>
            <input type="radio" id="basso_21gg" name="rendimento" value="BASSO 21gg (37%)">
            <label for="basso_21gg">BASSO 21gg (37%)</label><br>
            <input type="radio" id="alto_14gg" name="rendimento" value="ALTO 14gg (variabile dal 23% al 30%)">
            <label for="alto_14gg">ALTO 14gg (variabile dal 23% al 30%)</label><br>
            <input type="radio" id="alto_21gg" name="rendimento" value="ALTO 21gg (variabile dal 34% al 45%)">
            <label for="alto_21gg">ALTO 21gg (variabile dal 34% al 45%)</label><br><br>

            <input type="submit" value="Genera Immagine">
        </form>
    '''

# Route per generare l'immagine personalizzata
@app.route("/genera_immagine")
def genera_immagine():
    # Ottieni i parametri dal form
    nome = request.args.get("nome", "Williams Jackob").replace(" ", "_")
    importo = request.args.get("importo", "40.000,00 $")
    rendimento_selezionato = request.args.get("rendimento", "BASSO 14gg (25%)")
    
    # Calcola la data di scadenza in base alla selezione
    data_scadenza = calcola_data_scadenza(rendimento_selezionato)
    
    # Genera il codice di riferimento
    codice_riferimento = genera_codice_riferimento()

    # Usa l'immagine e i font dalla cache
    image = get_base_image()
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Font cachati
    font_above = get_font("lumios_typewriter_tape", 326)
    font_below = get_font("lumios_typewriter_tape", 326)
    font_center = get_font("lumios_typewriter_new", 81)

    # Colori e trasparenza
    color_above = (134, 81, 0, int(28 * 2.55))
    color_below = (31, 59, 0, int(63 * 2.55))
    color_center = (43, 43, 43, 255)

    # Testo centrale personalizzato
    text_center = [
        (f"Titolare: {nome.replace('_', ' ')}", 871.07, 694.60),
        (f"Importo Investito: {importo}", 871.07, 806.92),
        (f"Rendimento Promesso: {rendimento_selezionato}", 871.07, 919.24),  # Inserisci il rendimento selezionato
        (f"Data di Scadenza: {data_scadenza}", 871.07, 1031.56),
        (f"Codice di Riferimento Unico: {codice_riferimento}", 871.07, 1143.87)
    ]

    # Posizione del testo sopra (con opacità al 28%)
    draw.text((2980.39, 588.83), codice_riferimento, font=font_above, fill=color_above, anchor="rd")

    # Testo centrale, con i valori personalizzati
    for line, x, y in text_center:
        draw.text((x, y), line, font=font_center, fill=color_center)

    # Posizione del testo sotto (con opacità al 63%)
    draw.text((-50.57, 1494.53), codice_riferimento, font=font_below, fill=color_below, anchor="la")

    # Combina il layer di testo con l'immagine di base
    final_image = Image.alpha_composite(image, txt_layer)

    # Riduci le dimensioni dell'immagine (es. 50% della risoluzione originale)
    new_size = (int(final_image.width * 0.5), int(final_image.height * 0.5))
    final_image = final_image.resize(new_size, Image.ANTIALIAS)

    # Salva l'immagine su un buffer
    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)

    # Codifica l'immagine in base64 per l'upload su ImgBB
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Carica l'immagine su ImgBB
    imgbb_url = carica_su_imgbb(image_data, "273e469a570fb0c36647319b42b36e7f")

    if imgbb_url:
        return jsonify({"imgbb_url": imgbb_url})
    else:
        return jsonify({"error": "Errore nel caricamento su ImgBB"}), 500

if __name__ == "__main__":
    app.run(debug=True)
