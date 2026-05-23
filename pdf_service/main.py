import asyncio
import base64
import os
import sys
import time
import threading
from rabbit import consume, publish
from models import Appointment, Prescription
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pdf_generator import generate_recipe_pdf, generate_certificate_pdf, generate_referral_pdf
from fastapi import FastAPI, Response
import uvicorn

# Импорт метрик
from metrics import (
    pdf_generated_total,
    rabbit_messages_total,
    pdf_generation_duration,
    active_generations,
    pdf_errors_total,
    get_metrics
)

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok", "service": "pdf-generator-worker"}

@app.get("/metrics")
def metrics():
    """Эндпоинт для сбора метрик Prometheus"""
    return get_metrics()

def run_fastapi():
    # Запускаем на порту 8020
    uvicorn.run(app, host="0.0.0.0", port=8020)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://bog:password@postgres:5432/clinic")

async def process_pdf_async(msg):
    appointment_id = msg["appointment_id"]
    email = msg["email"]
    doc_type = msg.get("doc_type", "recipe")
    pdf_path = None
    engine = None

    # Увеличиваем счетчик активных генераций
    active_generations.inc()
    start_time = time.time()
    status = "success"
    error_type = None

    print(f"[PDF Service] Начинаю генерацию {doc_type} для ID {appointment_id}", flush=True)

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            # 1. Загружаем ЗАПИСЬ (Appointment)
            result = await db.execute(
                select(Appointment)
                .options(
                    selectinload(Appointment.patient),
                    selectinload(Appointment.doctor)
                )
                .filter(Appointment.id_rec == appointment_id)
            )
            appointment = result.scalar_one_or_none()

            if not appointment:
                print(f"[PDF Service] Ошибка: Запись {appointment_id} не найдена!", flush=True)
                status = "error"
                error_type = "appointment_not_found"
                pdf_generated_total.labels(doc_type=doc_type, status="error").inc()
                pdf_errors_total.labels(doc_type=doc_type, error_type=error_type).inc()
                rabbit_messages_total.labels(action="generate_pdf", status=status).inc()
                return

            # 2. Загружаем РЕЦЕПТ (Prescription)
            presc_result = await db.execute(
                select(Prescription)
                .options(
                    selectinload(Prescription.diagnosis),
                    selectinload(Prescription.drug)
                )
                .filter(Prescription.id_rec == appointment_id)
            )
            prescription = presc_result.scalar_one_or_none()

            # 3. Генерируем нужный тип документа
            if doc_type == "certificate":
                pdf_path = await generate_certificate_pdf(appointment)
            elif doc_type == "referral":
                pdf_path = await generate_referral_pdf(appointment)
            elif doc_type == "recipe":
                pdf_path = await generate_recipe_pdf(appointment, prescription)
            else:
                print(f"[PDF Service] Неизвестный тип документа: {doc_type}", flush=True)
                status = "error"
                error_type = "unknown_doc_type"
                pdf_generated_total.labels(doc_type=doc_type, status="error").inc()
                pdf_errors_total.labels(doc_type=doc_type, error_type=error_type).inc()
                rabbit_messages_total.labels(action="generate_pdf", status=status).inc()
                return

        # 4. Если всё успешно — отправляем
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
            os.remove(pdf_path)
            print(f"[PDF Service] ✅ PDF готов. Отправляю в Rabbit...", flush=True)

            publish({
                "target": "notification",
                "action": "send_email",
                "email": email,
                "doc_type": doc_type,
                "pdf_base64": pdf_base64
            })

            # Успешная генерация
            pdf_generated_total.labels(doc_type=doc_type, status="success").inc()
        else:
            print(f"[PDF Service] ❌ Ошибка: Файл PDF не создался (path: {pdf_path})", flush=True)
            status = "error"
            error_type = "file_not_created"
            pdf_generated_total.labels(doc_type=doc_type, status="error").inc()
            pdf_errors_total.labels(doc_type=doc_type, error_type=error_type).inc()

    except Exception as e:
        status = "error"
        error_type = type(e).__name__
        pdf_generated_total.labels(doc_type=doc_type, status="error").inc()
        pdf_errors_total.labels(doc_type=doc_type, error_type=error_type).inc()
        print(f"[PDF Service] 🔥 Критическая ошибка: {e}", flush=True)
    finally:
        # Записываем время выполнения
        duration = time.time() - start_time
        pdf_generation_duration.labels(doc_type=doc_type).observe(duration)
        active_generations.dec()
        rabbit_messages_total.labels(action="generate_pdf", status=status).inc()

        if engine:
            await engine.dispose()

def handle_generate_pdf(msg):
    asyncio.run(process_pdf_async(msg))

if __name__ == "__main__":
    # Запускаем веб-сервер для Health Check и метрик в отдельном потоке
    threading.Thread(target=run_fastapi, daemon=True).start()

    print("🚀 PDF Generator запущен (Worker + Health API + Metrics)...", flush=True)
    consume("pdf", {
        "generate_pdf": handle_generate_pdf
    })