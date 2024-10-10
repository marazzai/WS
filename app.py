from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

app = Flask(__name__)

# Home route con un form HTML per ricevere i dati
@app.route("/")
def home():
    return '''
        <h1>Generatore di Immagini Personalizzabile</h1>
        <form action="/genera_immagine" method="get">
            Nome: <input type="text" name="nome" value="Williams Jackob"><br><br>
            Importo: <input type="text" name="importo" value="40.000,00 $"><br><br>
            Rendimento: <input type="text" name="rendimento" value="45%"><br><br>
            Data di Scadenza: <input type="text" name="data" value="31/10/2024"><br><br>
            Codice di Riferimento: <input type="text" name="codice" value="101020240017"><br><br>
            <input type="submit" value="Genera Immagine">
        </form>
    '''

# Route per generare l'immagine personalizzata
@app.route("/genera_immagine")
def genera_immagine():
    # Ottieni i parametri dal form
    nome = request.args.get("nome", "Williams Jackob").replace(" ", "_")
    importo = request.args.get("importo", "40.000,00 $")
    rendimento = request.args.get("rendimento", "45%")
    data_scadenza = request.args.get("data", "31/10/2024")
    codice_riferimento = request.args.get("codice", "101020240017")

    # Carica l'immagine di base
    image = Image.open("static/image.png").convert("RGBA")
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    # Font e dimensioni
    font_above = ImageFont.truetype("fonts/lumios_typewriter_tape.otf", 326)
    font_below = ImageFont.truetype("fonts/lumios_typewriter_tape.otf", 326)
    font_center = ImageFont.truetype("fonts/lumios_typewriter_new.otf", 81)

    # Colori e trasparenza
    color_above = (134, 81, 0, int(28 * 2.55))
    color_below = (31, 59, 0, int(63 * 2.55))
    color_center = (43, 43, 43, 255)

    # Testo centrale personalizzato
    text_center = [
        (f"Titolare: {nome.replace('_', ' ')}", 871.07, 694.60),
        (f"Importo Investito: {importo}", 871.07, 806.92),
        (f"Rendimento Promesso: variabile dal 34% al {rendimento}", 871.07, 919.24),
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

    # Salva l'immagine su un buffer
    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)

    # Nome del file basato sul nome del titolare
    filename = f"{nome}.png"

    # Restituisci l'immagine come file scaricabile con il nome del titolare
    return send_file(buffer, mimetype="image/png", as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True)
