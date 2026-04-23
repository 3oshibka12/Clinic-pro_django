from sqlalchemy.orm import Session
from datetime import datetime
from app import schemas, models
from app.database import get_db, engine
import os
import base64
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from email_sender import send_email_async

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Notification Service")


@app.get("/")
def root():
    return {"status": "active", "db": "connected"}


@app.get("/notification-log", response_model=list[schemas.NotificationResp])
def check_up(db: Session = Depends(get_db)):
    return db.query(models.Notification).all()

@app.get("/notification-log/{noti_id}", response_model=schemas.NotificationResp)
def check_up_by_id(noti_id: int, db: Session = Depends(get_db)):
    db_notification = db.get(models.Notification, noti_id)
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification



@app.post("/appointment-info", response_model=schemas.NotificationResp, status_code=201)
def send_appointment_info(letter: schemas.AppointmentInfoCreate, bd: BackgroundTasks, db: Session = Depends(get_db)): 
    email_body = f"""
    <h1>Подтверждение записи</h1>
    <p>Здравствуйте, <b>{letter.patient_name}</b>!</p>
    <p>Вы записаны к врачу: {letter.doctor_name}.</p>
    <p>📅 Время: {letter.visit_time}</p>
    <p>🚪 Кабинет: {letter.cabinet}</p>
    """
    
    db_notification = models.Notification(
        type="appointment",
        email=letter.email,
        content=email_body,
        created_at=datetime.now()
    )

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    bd.add_task(send_email_async, "Подтверждение записи", letter.email, email_body)

    return db_notification

@app.post("/reminder", response_model=schemas.NotificationResp, status_code=201)
def send_reminder(letter: schemas.ReminderCreate, bd: BackgroundTasks, db: Session = Depends(get_db)):
    db_notification = models.Notification(
        type="reminder",
        email=letter.email,
        content=letter.message,
        created_at=datetime.now()
    )

    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    bd.add_task(send_email_async, "Напоминание о приеме", letter.email, f"<p>{letter.message}</p>")

    return db_notification






from rabbit import publish

@app.post("/request-prescription", status_code=202)
def request_prescription(
    data: schemas.PrescriptionRequest,
    db: Session = Depends(get_db)
):

    db_notification = models.Notification(
        type="prescription",
        email=data.email,
        content=f"Запрос PDF для appointment #{data.appointment_id} (ожидание)",
        created_at=datetime.now()
    )
    db.add(db_notification)
    db.commit()
    print("CHANGED")
    publish({
        "target": "pdf",
        "action": "generate_pdf",
        "appointment_id": data.appointment_id,
        "email": data.email,
        "notification_id": db_notification.id,
        "doc_type": data.doc_type
    })

    return {
        "status": "queued",
        "message": "PDF запрошен, email будет отправлен автоматически",
        "notification_id": db_notification.id,
    }