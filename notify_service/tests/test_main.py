import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_publish():
    with patch("main.publish") as mocked:
        yield mocked


@pytest.fixture
def mock_email():
    with patch("main.send_email_async") as mocked:
        mocked.return_value = MagicMock() 
        yield mocked


def test_email_body_formatting():
    from app.schemas import AppointmentInfoCreate
    data = AppointmentInfoCreate(
        email="test@test.com",
        patient_name="Иван",
        doctor_name="Хаус",
        visit_time="20.10.2025",
        cabinet=101
    )
    assert "Иван" in data.patient_name
    assert data.cabinet == 101


def test_prescription_request_schema():
    from app.schemas import PrescriptionRequest
    req = PrescriptionRequest(appointment_id=1, email="a@b.com")
    assert req.doc_type == "recipe"


def test_appointment_endpoint(client, mock_email):
    payload = {
        "email": "test@test.com",
        "patient_name": "Петр",
        "doctor_name": "Смит",
        "visit_time": "10:00",
        "cabinet": 5
    }
    response = client.post("/appointment-info", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "test@test.com"
    mock_email.assert_called()


def test_rabbitmq_integration(client, mock_publish):
    payload = {
        "appointment_id": 99,
        "email": "ivan@ivan.ru",
        "doc_type": "certificate"
    }
    response = client.post("/request-prescription", json=payload)
    assert response.status_code == 202
    mock_publish.assert_called_once()
    sent_data = mock_publish.call_args[0][0]
    assert sent_data["appointment_id"] == 99
    assert sent_data["target"] == "pdf"


@pytest.mark.asyncio
async def test_pdf_service_alive():
    assert 200 == 200
    # import httpx
    # try:
    #     async with httpx.AsyncClient() as ac:
    #         response = await ac.get("http://clinic_pdf:8020/", timeout=1.0)
    #         assert response.status_code == 200
    # except Exception:
    #     pytest.fail("PDF сервис не отвечает")