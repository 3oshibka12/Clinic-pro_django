# notify_service/main.py
import logging
import json
import time
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Response

from app import schemas, models
from app.database import get_db, engine
from email_sender import send_email_async
from rabbit import publish

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from middleware import MetricsMiddleware

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        return json.dumps(log_entry)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Notification Service")

app.add_middleware(MetricsMiddleware) # !!!!!


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"status": "active", "db": "connected"}


@app.get("/notification-log", response_model=list[schemas.NotificationResp])
def check_up(db: Session = Depends(get_db)):
    return db.query(models.Notification).all()

@app.get("/notification-log/{noti_id}", response_model=schemas.NotificationResp)
def check_up_by_id(noti_id: int, db: Session = Depends(get_db)):
    db_notification = db.get(models.Notification, noti_id)
    if not db_notification:
        logger.warning(f"Notification with id {noti_id} not found")
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification


@app.post("/appointment-info", response_model=schemas.NotificationResp, status_code=201)
def send_appointment_info(letter: schemas.AppointmentInfoCreate, bd: BackgroundTasks, db: Session = Depends(get_db)): 
    logger.info(f"Received appointment info for: {letter.email}")
    
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
    logger.info(f"Sending reminder to: {letter.email}")
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


@app.post("/request-prescription", status_code=202)
def request_prescription(
    data: schemas.PrescriptionRequest,
    db: Session = Depends(get_db)
):
    logger.info(f"Requesting prescription for appointment #{data.appointment_id}")
    db_notification = models.Notification(
        type="prescription",
        email=data.email,
        content=f"Запрос PDF для appointment #{data.appointment_id} (ожидание)",
        created_at=datetime.now()
    )
    db.add(db_notification)
    db.commit()
    
    logger.info("Publishing task to RabbitMQ for PDF generation")
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


@app.get("/metrics")
async def get_metrics():
    """Эндпоинт для Prometheus"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/test/error")
async def test_error():
    """Тестовая 500 ошибка для метрики Error rate"""
    logger.error("Test error endpoint called")
    raise HTTPException(status_code=500, detail="Тестовая ошибка")

@app.get("/test/slow")
async def test_slow():
    """Имитация долгой обработки для метрики Latency"""
    logger.info("Test slow endpoint called - sleeping for 2 seconds")
    time.sleep(2)
    return {"status": "ok", "message": "Медленный ответ после 2 секунд"}