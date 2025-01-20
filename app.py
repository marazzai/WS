import logging
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime, timedelta
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

# Funzione aggiornata per calcolare la data di scadenza basata sul tipo di investimento
def calcola_data_scadenza(tipo_investimento):
    giorni = 7 if "7GG" in tipo_investimento else 14 if "14GG" in tipo_investimento else 21
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
        logging.debug(f"Payload inviato a Google Sheets: {payload}")
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"Errore durante l'invio dei dati a Google Sheet: {str(e)}")
        return False

# Route per la home page con il form aggiornato
@app.route("/")
def home():
    return '''
        <h1>Generatore di Immagini Personalizzabile</h1>
        <form action="/genera_immagine" method="get">
            Nome: <input type="text" name="nome" value="Nome Cognome"><br><br>
            Importo: <input type="text" name="importo" value="40.000,00 $"><br><br>
            
            <label>Rendimento Promesso:</label><br>
            <input type="radio" id="basso_7gg" name="rendimento" value="11%" checked>
            <label for="basso_7gg">BASSO 7gg (11%)</label><br>
            <input type="radio" id="basso_14gg" name="rendimento" value="25%">
            <label for="basso_14gg">BASSO 14gg (25%)</label><br>
            <input type="radio" id="basso_21gg" name="rendimento" value="37%">
            <label for="basso_21gg">BASSO 21gg (37%)</label><br><br>

            <input type="submit" value="Genera Immagine">
        </form>
    '''

# Route per generare l'immagine e inviare i dati al foglio Google
@app.route("/genera_immagine")
def genera_immagine():
    try:
        nome = request.args.get("nome", "Nome Cognome").replace("_", " ")
        importo = request.args.get("importo", "40000").strip()

        # Normalizza l'importo
        importo = importo.replace(".", "").replace(",", "").replace("$", "")
        if importo.isdigit():
            importo = int(importo)
        else:
            logging.error("Importo non valido: " + importo)
            return jsonify({"error": "Importo non valido"}), 400

        rendimento_selezionato = request.args.get("rendimento", "11%")
        tipo_investimento = "BASSO 7GG" if rendimento_selezionato == "11%" else \
                            "BASSO 14GG" if rendimento_selezionato == "25%" else \
                            "BASSO 21GG"

        data_scadenza = calcola_data_scadenza(tipo_investimento)
        codice_riferimento = genera_codice_riferimento()

        fuso_orario_italia = pytz.timezone('Europe/Rome')
        data_investimento = datetime.now(fuso_orario_italia).strftime("%d/%m/%Y")

        if invia_a_google_sheet(nome, importo, tipo_investimento, data_investimento):
            return jsonify({"success": True, "message": "Dati inviati con successo"})
        else:
            return jsonify({"error": "Errore nell'invio dei dati a Google Sheet"}), 500
    except Exception as e:
        logging.error(f"Errore durante la generazione dell'immagine: {str(e)}")
        return jsonify({"error": "Errore durante la generazione dell'immagine"}), 500

if __name__ == "__main__":
    app.run(debug=True)
