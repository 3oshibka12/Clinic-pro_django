import os
import requests
import logging

logger = logging.getLogger(__name__)

# Читаем адрес микросервиса из окружения (в Docker это http://notify_service:8000)
# Если запускаешь локально без докера, будет http://localhost:8000
NOTIFY_SERVICE_URL = os.getenv("NOTIFY_SERVICE_URL", "http://notify_service:8000")

def send_appointment_confirmation(email, patient_name, doctor_name, visit_time, cabinet):
    """Отправляет запрос на email-подтверждение новой записи"""
    url = f"{NOTIFY_SERVICE_URL}/appointment-info"
    payload = {
        "email": email,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "visit_time": visit_time.strftime("%d.%m.%Y %H:%M"), # Форматируем дату красиво
        "cabinet": cabinet
    }
    try:
        # timeout=3 значит, что Django не будет ждать ответа дольше 3 секунд
        requests.post(url, json=payload, timeout=3)
        logger.info(f"Запрос на подтверждение записи отправлен в Notify Service для {email}")
    except requests.RequestException as e:
        logger.error(f"Ошибка связи с микросервисом уведомлений: {e}")

def request_prescription_generation(appointment_id, patient_email, doc_type="recipe"):
    """Отправляет запрос на генерацию PDF рецепта и отправку его на почту"""
    url = f"{NOTIFY_SERVICE_URL}/request-prescription"
    payload = {
        "appointment_id": appointment_id,
        "email": patient_email,
        "doc_type": doc_type
    }
    try:
        requests.post(url, json=payload, timeout=3)
        logger.info(f"Запрос на PDF отправлен в Notify Service для appointment {appointment_id}")
    except requests.RequestException as e:
        logger.error(f"Ошибка связи с микросервисом уведомлений: {e}")