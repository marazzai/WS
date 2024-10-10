from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

app = Flask(__name__)

@app.route("/")
def home():
    return "Benvenuto! Vai a /genera_immagine per creare la tua immagine."

@app.route("/genera_immagine")
def genera_immagine():
    # Carica l'immagine di base
    image = Image.open("static/image.png").convert("RGBA")  # Converti l'immagine in RGBA per supportare la trasparenza
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))  # Layer di testo trasparente
    draw = ImageDraw.Draw(txt_layer)

    # Font e dimensioni
    font_above = ImageFont.truetype("fonts/lumios_typewriter_tape.otf", 326)  # Font grande (sopra e sotto)
    font_below = ImageFont.truetype("fonts/lumios_typewriter_tape.otf", 326)
    font_center = ImageFont.truetype("fonts/lumios_typewriter_new.otf", 81)  # Font per il testo centrale

    # Colori e trasparenza
    color_above = (134, 81, 0, int(28 * 2.55))  # Colore sopra (#865100) con trasparenza 28%
    color_below = (31, 59, 0, int(63 * 2.55))   # Colore sotto (#1f3b00) con trasparenza 63%
    color_center = (43, 43, 43, 255)  # Colore del testo centrale (#2b2b2b) con opacità piena

    # Testo e coordinate aggiornate
    codice_riferimento = "101020240017"
    text_above = codice_riferimento
    text_below = codice_riferimento

    # Testo centrale con coordinate separate per ogni riga
    text_center = [
        ("Titolare: Williams Jackob", 871.07, 694.60),
        ("Importo Investito: 40.000,00 $", 871.07, 806.92),
        ("Rendimento Promesso: variabile dal 34% al 45%", 871.07, 919.24),
        ("Data di Scadenza: 31/10/2024", 871.07, 1031.56),
        ("Codice di Riferimento Unico: 101020240017", 871.07, 1143.87)
    ]

    # Posizione del testo sopra (con opacità al 28%)
    draw.text((2980.39, 588.83), text_above, font=font_above, fill=color_above, anchor="rd")

    # Testo centrale, con coordinate separate per ogni riga e colore #2b2b2b
    for line, x, y in text_center:
        draw.text((x, y), line, font=font_center, fill=color_center)

    # Posizione del testo sotto (con opacità al 63%)
    draw.text((-50.57, 1494.53), text_below, font=font_below, fill=color_below, anchor="la")

    # Combina il layer di testo con l'immagine di base
    final_image = Image.alpha_composite(image, txt_layer)

    # Salva l'immagine su un buffer
    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)

    # Restituisci l'immagine come file
    return send_file(buffer, mimetype="image/png", as_attachment=True, download_name="output_image.png")

if __name__ == "__main__":
    app.run(debug=True)
