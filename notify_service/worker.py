import base64, asyncio, os
from tempfile import NamedTemporaryFile
from rabbit import publish, consume
from email_sender import send_email_async



def handle_process(msg):
    """Django попросил отправить документ — запрашиваем PDF"""
    publish(
        target="pdf",
        action="generate_pdf",
        appointment_id=msg["appointment_id"],
        email=msg["email"],
        doc_type=msg.get("doc_type", "recipe"),
    )


def handle_send_email(msg):
    """PDF-сервис прислал готовый PDF — отправляем на почту"""
    pdf_bytes = base64.b64decode(msg["pdf_base64"])
    doc_type = msg.get("doc_type", "document")

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        asyncio.run(send_email_async(
            subject=f"Ваш документ: {doc_type}",
            email_to=msg["email"],
            body=f"<h1>Документ</h1><p>Во вложении: {doc_type}</p>",
            attachments=[tmp_path],
        ))
        print(f"[✓] Email → {msg['email']}")
    finally:
        os.remove(tmp_path)


if __name__ == "__main__":
    consume("notification", {
        "process": handle_process,
        "send_email": handle_send_email,
    })