from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    height = letter[1]
    y = height - 40

    for line in text.split("\n"):
        if y < 40:
            c.showPage()
            y = height - 40
        c.setFont("Helvetica", 10)
        c.drawString(40, y, line[:100])
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer

