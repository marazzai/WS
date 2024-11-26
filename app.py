import logging
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime, timedelta
import base64
import pytz
import requests

app = Flask(__name__)

# Configura il logging per catturare i dettagli degli errori
logging.basicConfig(level=logging.DEBUG)

# Cache per risorse statiche (immagini e font)
base_image = None
fonts_cache = {}

# Funzione per ottenere l'immagine di base
def get_base_image():
    global base_image
    if base_image is None:
        base_image = Image.open("static/image.webp").convert("RGBA")
    return base_image.copy()

# Funzione per ottenere il font dalla cache
def get_font(name, size):
    key = f"{name}-{size}"
    if key not in fonts_cache:
        fonts_cache[key] = ImageFont.truetype(f"fonts/{name}.otf", size)
    return fonts_cache[key]

# Funzione per calcolare la data di scadenza basata sul tipo di investimento
def calcola_data_scadenza(tipo_investimento):
    giorni = 14 if '14GG' in tipo_investimento else 21
    fuso_orario_italia = pytz.timezone('Europe/Rome')
    data_attuale = datetime.now(fuso_orario_italia)
    data_scadenza = data_attuale + timedelta(days=giorni)
    return data_scadenza.strftime("%d/%m/%Y")

# Funzione per generare un codice di riferimento unico basato sulla data e ora
def genera_codice_riferimento():
    fuso_orario_italia = pytz.timezone('Europe/Rome')
    now = datetime.now(fuso_orario_italia)
    return now.strftime("%d%m%Y%H%M")

# Funzione per inviare i dati a Google Sheet tramite Apps Script
def invia_a_google_sheet(nome, importo, tipo_investimento, data_investimento):
    try:
        url = "https://script.google.com/macros/s/AKfycbxJ7qR7z8OHWt6KSYo2UoRQjRzipiRgRoYS6ecUUOIZCxXOwHIbyiJh3KicCtEjKZEj/exec"
        payload = {
            'nome': nome,
            'importo': importo,
            'tipo_investimento': tipo_investimento,
            'data_investimento': data_investimento
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Errore durante l'invio dei dati a Google Sheet: {str(e)}")
        return False

# Funzione per caricare l'immagine su FiveManage
def carica_su_fivemanage(image_buffer, api_key):
    try:
        # Endpoint per l'upload dell'immagine
        url = "https://api.fivemanage.com/api/image"

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # L'immagine deve essere inviata come parte di `multipart/form-data`
        files = {
            "image": ("image.png", image_buffer, "image/png")
        }

        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()

        # Supponendo che la risposta contenga il link all'immagine caricata
        return response.json().get("url")
    except Exception as e:
        logging.error(f"Errore durante il caricamento su FiveManage: {str(e)}")
        return None

# Home route con il form per ricevere i dati
@app.route("/")
def home():
    return '''
        <h1>Generatore di Immagini Personalizzabile</h1>
        <form action="/genera_immagine" method="get">
            Nome: <input type="text" name="nome" value="Nome Cognome"><br><br>
            Importo: <input type="text" name="importo" value="40.000,00 $"><br><br>
            
            <label>Rendimento Promesso:</label><br>
            <input type="radio" id="basso_14gg" name="rendimento" value="25%" checked>
            <label for="basso_14gg">BASSO 14gg (25%)</label><br>
            <input type="radio" id="basso_21gg" name="rendimento" value="37%">
            <label for="basso_21gg">BASSO 21gg (37%)</label><br>
            <input type="radio" id="alto_14gg" name="rendimento" value="variabile dal 23% al 30%">
            <label for="alto_14gg">ALTO 14gg (variabile dal 23% al 30%)</label><br>
            <input type="radio" id="alto_21gg" name="rendimento" value="variabile dal 34% al 45%">
            <label for="alto_21gg">ALTO 21gg (variabile dal 34% al 45%)</label><br><br>

            <input type="submit" value="Genera Immagine">
        </form>
    '''

# Route per generare l'immagine e inviare i dati al foglio Google
@app.route("/genera_immagine")
def genera_immagine():
    try:
        # Ottieni i parametri dal form
        nome = request.args.get("nome", "Nome Cognome").replace("_", " ")
        importo = request.args.get("importo", "40000").replace(".", "").replace(",", "").replace("$", "")
        rendimento_selezionato = request.args.get("rendimento", "25%")
        tipo_investimento = "BASSO 14GG" if rendimento_selezionato == "25%" else "BASSO 21GG" if rendimento_selezionato == "37%" else "ALTO 14GG" if "23%" in rendimento_selezionato else "ALTO 21GG"
        
        # Calcola la data di scadenza in base al tipo di investimento
        data_scadenza = calcola_data_scadenza(tipo_investimento)
        codice_riferimento = genera_codice_riferimento()

        # Data dell'investimento (la data corrente)
        fuso_orario_italia = pytz.timezone('Europe/Rome')
        data_investimento = datetime.now(fuso_orario_italia).strftime("%d/%m/%Y")

        # Invia i dati a Google Sheet
        if invia_a_google_sheet(nome, importo, tipo_investimento, data_investimento):
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
                (f"Titolare: {nome}", 871.07, 694.60),
                (f"Importo Investito: {request.args.get('importo', '40.000,00 $')}", 871.07, 806.92),
                (f"Rendimento Promesso: {'variabile dal 23% al 30%' if '23%' in rendimento_selezionato else rendimento_selezionato}", 871.07, 919.24),
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
            final_image = final_image.resize(new_size, Image.Resampling.LANCZOS)

            # Salva l'immagine su un buffer
            buffer = BytesIO()
            final_image.save(buffer, format="PNG")
            buffer.seek(0)

            # Carica l'immagine su FiveManage
            imgbb_url = carica_su_fivemanage(buffer, "LvTU9eoJ9aVelrBG7ClyjbaAifIvhxHi")

            if imgbb_url:
                return jsonify({"imgbb_url": imgbb_url})
            else:
                logging.error("Errore nel caricamento su FiveManage")
                return jsonify({"error": "Errore nel caricamento su FiveManage"}), 500
        else:
            logging.error("Errore nell'invio dei dati a Google Sheet")
            return jsonify({"error": "Errore nell'invio dei dati a Google Sheet"}), 500
    except Exception as e:
        logging.error(f"Errore durante la generazione dell'immagine: {str(e)}")
        return jsonify({"error": "Errore durante la generazione dell'immagine"}), 500

if __name__ == "__main__":
    app.run(debug=True)
