from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

conf = ConnectionConfig(
    MAIL_USERNAME="staryakk777@gmail.com",
    MAIL_PASSWORD="hfyi tktg xlst tbxg",
    MAIL_FROM="staryakk777@gmail.com",
    MAIL_PORT=587,         
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_email_async(subject: str, email_to: str, body: str, attachments: list = None):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=MessageType.html,
        attachments=attachments or []
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Получилось отправить {email_to}")
    except Exception as e:
        print(f"НЕ получилось отправить: {e}")