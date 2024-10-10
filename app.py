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
def calcola_data_scadenza(rendimento):
    giorni = 14 if '14gg' in rendimento else 21
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
def invia_a_google_sheet(nome, importo, tipo_investimento):
    try:
        url = "https://script.google.com/macros/s/AKfycbxJ7qR7z8OHWt6KSYo2UoRQjRzipiRgRoYS6ecUUOIZCxXOwHIbyiJh3KicCtEjKZEj/exec"
        payload = {
            'nome': nome,  # Passa il nome senza underscore e in maiuscolo
            'importo': importo,
            'tipo_investimento': tipo_investimento
        }
        logging.debug(f"Inviando a Google Sheet: {payload}")  # Aggiungi il log del payload
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, json=payload, headers=headers)  # Invia i dati come JSON
        logging.debug(f"Risposta dal Google Script: {response.status_code} - {response.text}")  # Logga la risposta
        response.raise_for_status()  # Solleva un'eccezione se c'è un errore HTTP
        return True
    except Exception as e:
        logging.error(f"Errore durante l'invio dei dati a Google Sheet: {str(e)}")
        return False

# Home route con il form per ricevere i dati
@app.route("/")
def home():
    return '''
        <h1>Generatore di Immagini Personalizzabile</h1>
        <form action="/genera_immagine" method="get">
            Nome: <input type="text" name="nome" value="Williams Jackob"><br><br>
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
        nome = request.args.get("nome", "Williams Jackob").replace("_", " ").upper()  # Usa spazio e maiuscolo
        importo = request.args.get("importo", "40000").replace(".", "").replace(",", "")  # Rimuovi simboli non numerici
        rendimento_selezionato = request.args.get("rendimento", "25%")
        
        # Calcola la data di scadenza e genera il codice di riferimento
        data_scadenza = calcola_data_scadenza(rendimento_selezionato)
        codice_riferimento = genera_codice_riferimento()

        # Invia i dati a Google Sheet
        if invia_a_google_sheet(nome, importo, rendimento_selezionato):
            logging.debug("Dati inviati correttamente a Google Sheet")
            return jsonify({"success": True})
        else:
            logging.error("Errore nell'invio dei dati a Google Sheet")
            return jsonify({"error": "Errore nell'invio dei dati a Google Sheet"}), 500

    except Exception as e:
        logging.error(f"Errore durante la generazione dell'immagine: {str(e)}")
        return jsonify({"error": "Errore durante la generazione dell'immagine"}), 500

if __name__ == "__main__":
    app.run(debug=True)
