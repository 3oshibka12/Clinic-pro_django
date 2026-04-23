import asyncio
import base64
import os
import sys
from rabbit import consume, publish
from models import Appointment, Prescription # Добавили Prescription
from sqlalchemy import select
from sqlalchemy.orm import selectinload # Добавили для подгрузки связей
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pdf_generator import generate_recipe_pdf, generate_certificate_pdf, generate_referral_pdf

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://bog:password@postgres:5432/clinic")

async def process_pdf_async(msg):
    appointment_id = msg["appointment_id"]
    email = msg["email"]
    doc_type = msg.get("doc_type", "recipe")
    pdf_path = None

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
                # Справка обычно требует только данные визита
                pdf_path = await generate_certificate_pdf(appointment)
            
            elif doc_type == "referral":
                # Направление
                pdf_path = await generate_referral_pdf(appointment)
            
            elif doc_type == "recipe":
                # Рецепт требует подгрузки prescription
                # (код загрузки prescription оставь выше)
                pdf_path = await generate_recipe_pdf(appointment, prescription)
            
            else:
                print(f"[PDF Service] Неизвестный тип документа: {doc_type}", flush=True)
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
        else:
            print(f"[PDF Service] ❌ Ошибка: Файл PDF не создался (path: {pdf_path})", flush=True)

    except Exception as e:
        print(f"[PDF Service] 🔥 Критическая ошибка: {e}", flush=True)
    finally:
        await engine.dispose()

def handle_generate_pdf(msg):
    asyncio.run(process_pdf_async(msg))

if __name__ == "__main__":
    print("🚀 PDF Generator запущен...", flush=True)
    consume("pdf", {
        "generate_pdf": handle_generate_pdf
    })