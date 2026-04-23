import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)

# 1. ЮНИТ-ТЕСТ: Валидация (теперь будет 422, если добавишь EmailStr)
def test_appointment_info_validation():
    bad_data = {
        "email": "not-an-email",
        "patient_name": "Ivan",
        "doctor_name": "House",
        "visit_time": "tomorrow",
        "cabinet": 101
    }
    response = client.post("/appointment-info", json=bad_data)
    assert response.status_code == 422

# 2. ИНТЕГРАЦИОННЫЙ ТЕСТ: /appointment-info
# Патчим функцию там, где она вызывается - в main.py
@patch("main.send_email_async") 
def test_send_appointment_info(mock_email):
    # Настраиваем мок, чтобы он не делал ничего, но считался асинхронным
    mock_email.return_value = MagicMock()
    
    data = {
        "email": "test@test.com",
        "patient_name": "Иван",
        "doctor_name": "Хаус",
        "visit_time": "2026-05-05 10:00",
        "cabinet": 101
    }
    response = client.post("/appointment-info", json=data)
    assert response.status_code == 201
    # Проверяем, что лог в БД создался
    assert response.json()["type"] == "appointment"

# 3. ИНТЕГРАЦИОННЫЙ ТЕСТ: RabbitMQ
@patch("main.publish")
def test_request_prescription(mock_publish):
    data = {
        "appointment_id": 7,
        "email": "test@test.com",
        "doc_type": "recipe"
    }
    response = client.post("/request-prescription", json=data)
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    mock_publish.assert_called_once()

# 4. ТЕСТ ДОСТУПНОСТИ СЕРВИСА КОЛЛЕГИ
import httpx
@pytest.mark.asyncio
async def test_pdf_service_availability():
    # clinic_pdf - имя контейнера в докере
    url = "http://clinic_pdf:8020/" 
    try:
        async with httpx.AsyncClient() as ac:
            response = await ac.get(url, timeout=5.0)
            assert response.status_code == 200
    except Exception as e:
        pytest.fail(f"Сервис коллеги не ответил: {e}")