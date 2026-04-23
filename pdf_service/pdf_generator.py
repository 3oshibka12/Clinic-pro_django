import os
import tempfile
import asyncio
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform
from concurrent.futures import ThreadPoolExecutor

pdf_executor = ThreadPoolExecutor(max_workers=15)

def register_cyrillic_font():
    """Регистрация шрифта с поддержкой кириллицы"""
    # Пути к шрифтам в разных ОС
    font_paths = [
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf'
    ]
    
    # Ищем обычный шрифт
    regular_font = None
    bold_font = None
    
    for path in font_paths:
        if os.path.exists(path):
            if 'Bold' in path or 'bold' in path or '_Bold' in path:
                if not bold_font:
                    bold_font = path
            else:
                if not regular_font:
                    regular_font = path
        
        if regular_font and bold_font:
            break
    
    # Регистрируем найденные шрифты
    if regular_font:
        try:
            pdfmetrics.registerFont(TTFont('CyrillicFont', regular_font))
            print(f"Зарегистрирован обычный шрифт: {regular_font}")
        except Exception as e:
            print(f"Ошибка регистрации обычного шрифта: {e}")
            regular_font = None
    
    if bold_font:
        try:
            pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', bold_font))
            print(f"Зарегистрирован жирный шрифт: {bold_font}")
        except Exception as e:
            print(f"Ошибка регистрации жирного шрифта: {e}")
            bold_font = None
    
    # Если не нашли жирный шрифт, используем обычный для жирного
    if not bold_font and regular_font:
        try:
            pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', regular_font))
            print("Используется обычный шрифт для жирного текста")
        except:
            pass
    
    return regular_font is not None

# Регистрируем шрифты при импорте
FONTS_REGISTERED = register_cyrillic_font()

async def generate_certificate_pdf(appointment):
    """Генерация PDF справки с поддержкой кириллицы (асинхронная обертка)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        pdf_executor,
        generate_certificate_pdf_sync,
        appointment
    )

def generate_certificate_pdf_sync(appointment):
    """Синхронная реализация генерации PDF справки"""
    fd, path = tempfile.mkstemp(suffix='.pdf', prefix=f'certificate_{appointment.id_rec}_')
    os.close(fd)
    
    # Создаем canvas
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    # Проверяем, зарегистрированы ли шрифты
    if FONTS_REGISTERED:
        normal_font = "CyrillicFont"
        bold_font = "CyrillicFont-Bold"
    else:
        # Если нет кириллических шрифтов, используем Helvetica (только латиница)
        normal_font = "Helvetica"
        bold_font = "Helvetica-Bold"
        print("Внимание: используются стандартные шрифты (кириллица может не отображаться)")
    
    try:
        # Заголовок
        c.setFont(bold_font, 16)
        c.drawCentredString(width/2, height - 50, "МЕДИЦИНСКАЯ СПРАВКА")
        
        # Дата
        c.setFont(normal_font, 10)
        c.drawRightString(width - 50, height - 80, f"Дата: {datetime.now().strftime('%d.%m.%Y')}")
        
        y = height - 120
        line_height = 20
        
        # Информация о пациенте
        patient = appointment.patient
        if patient:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Пациент:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            lname = patient.lname or ""
            fname = patient.fname or ""
            c.drawString(70, y, f"{lname} {fname}".strip())
            y -= line_height
            
            if patient.birth_date:
                c.drawString(70, y, f"Дата рождения: {patient.birth_date.strftime('%d.%m.%Y')}")
                y -= line_height * 1.5
            else:
                y -= line_height
        
        # Информация о враче
        doctor = appointment.doctor
        if doctor:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Врач:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            lname = doctor.lname or ""
            fname = doctor.fname or ""
            c.drawString(70, y, f"{lname} {fname}".strip())
            y -= line_height
            
            spec = doctor.specialization or ""
            c.drawString(70, y, f"Специализация: {spec}")
            y -= line_height * 1.5
        
        # Текст справки
        c.setFont(bold_font, 12)
        c.drawString(50, y, "Справка:")
        y -= line_height
        
        c.setFont(normal_font, 12)
        
        # Формируем строки с проверкой на None
        patient_name = f"{patient.lname or ''} {patient.fname or ''}".strip() if patient else ""
        doctor_name = f"{doctor.lname or ''} {doctor.fname or ''}".strip() if doctor else ""
        visit_time = appointment.visit_time.strftime('%d.%m.%Y в %H:%M') if appointment.visit_time else ""
        cabinet = appointment.cabinet or ""
        
        lines = [
            f"Дана в том, что пациент {patient_name}",
            f"посетил врача {doctor_name}",
            f"{visit_time}.",
            f"Кабинет № {cabinet}"
        ]
        
        for line in lines:
            if line.strip() and not line.endswith("№ "):  # Не рисуем пустые строки
                c.drawString(70, y, line)
                y -= line_height
        
    except Exception as e:
        print(f"Ошибка при генерации PDF: {e}")
        # Если ошибка, пишем простой текст
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, f"Certificate for appointment {appointment.id_rec}")
    
    c.save()
    return path

async def generate_referral_pdf(appointment):
    """Генерация PDF направления (асинхронная обертка)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        pdf_executor,
        generate_referral_pdf_sync,
        appointment
    )

def generate_referral_pdf_sync(appointment):
    """Синхронная реализация генерации PDF направления"""
    fd, path = tempfile.mkstemp(suffix='.pdf', prefix=f'referral_{appointment.id_rec}_')
    os.close(fd)
    
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    if FONTS_REGISTERED:
        normal_font = "CyrillicFont"
        bold_font = "CyrillicFont-Bold"
    else:
        normal_font = "Helvetica"
        bold_font = "Helvetica-Bold"
    
    try:
        # Заголовок
        c.setFont(bold_font, 18)
        c.drawCentredString(width/2, height - 50, "НАПРАВЛЕНИЕ")
        c.line(50, height - 60, width - 50, height - 60)
        
        # Дата
        c.setFont(normal_font, 10)
        c.drawRightString(width - 50, height - 80, f"Дата: {datetime.now().strftime('%d.%m.%Y')}")
        
        y = height - 120
        line_height = 20
        
        patient = appointment.patient
        doctor = appointment.doctor
        
        # Информация о пациенте
        if patient:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Пациент:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            patient_name = f"{patient.lname or ''} {patient.fname or ''}".strip()
            c.drawString(70, y, patient_name)
            y -= line_height * 2
        
        # Информация о направлении
        if doctor:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Направляется к:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            spec = doctor.specialization or ""
            c.drawString(70, y, spec)
            y -= line_height
            
            doctor_name = f"{doctor.lname or ''} {doctor.fname or ''}".strip()
            c.drawString(70, y, f"Врач: {doctor_name}")
            y -= line_height * 2
        
        # Цель направления
        c.setFont(bold_font, 12)
        c.drawString(50, y, "Цель:")
        y -= line_height
        
        c.setFont(normal_font, 12)
        c.drawString(70, y, "Консультация / обследование")
        y -= line_height * 2
        
    except Exception as e:
        print(f"Ошибка при генерации направления: {e}")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, f"Referral for appointment {appointment.id_rec}")
    
    c.save()
    return path

async def generate_recipe_pdf(appointment, prescription):
    """Генерация PDF рецепта (асинхронная обертка)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        pdf_executor,
        generate_recipe_pdf_sync,
        appointment,
        prescription
    )

def generate_recipe_pdf_sync(appointment, prescription):
    """Синхронная реализация генерации PDF рецепта"""
    fd, path = tempfile.mkstemp(suffix='.pdf', prefix=f'recipe_{appointment.id_rec}_')
    os.close(fd)
    
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    if FONTS_REGISTERED:
        normal_font = "CyrillicFont"
        bold_font = "CyrillicFont-Bold"
    else:
        normal_font = "Helvetica"
        bold_font = "Helvetica-Bold"
    
    try:
        # Заголовок
        c.setFont(bold_font, 20)
        c.drawCentredString(width/2, height - 50, "РЕЦЕПТ")
        
        # Номер и дата
        c.setFont(normal_font, 10)
        visit_time = appointment.visit_time.strftime('%d.%m.%Y') if appointment.visit_time else datetime.now().strftime('%d.%m.%Y')
        c.drawRightString(width - 50, height - 80, f"№ {appointment.id_rec}")
        c.drawRightString(width - 50, height - 95, f"от {visit_time}")
        
        y = height - 130
        line_height = 20
        
        patient = appointment.patient
        doctor = appointment.doctor
        
        # Информация о пациенте
        if patient:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Пациент:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            patient_name = f"{patient.lname or ''} {patient.fname or ''}".strip()
            c.drawString(70, y, patient_name)
            y -= line_height
        
        # Информация о враче
        if doctor:
            c.setFont(bold_font, 12)
            c.drawString(50, y, "Врач:")
            y -= line_height
            
            c.setFont(normal_font, 12)
            doctor_name = f"{doctor.lname or ''} {doctor.fname or ''}".strip()
            c.drawString(70, y, doctor_name)
            y -= line_height * 1.5
        
        # Назначение
        c.setFont(bold_font, 12)
        c.drawString(50, y, "Назначение:")
        y -= line_height
        
        c.setFont(normal_font, 12)
        treatment = prescription.treatment or ""
        # Разбиваем длинный текст
        words = treatment.split()
        line = ""
        for word in words:
            if len(line + " " + word) < 60:
                line += " " + word if line else word
            else:
                if line:
                    c.drawString(70, y, line)
                    y -= line_height
                line = word
        if line:
            c.drawString(70, y, line)
            y -= line_height
        
        # Информация о лекарстве
        if prescription.drug and prescription.drug.name:
            y -= line_height
            c.drawString(70, y, f"Препарат: {prescription.drug.name}")
            y -= line_height
        
        # Частота
        if prescription.frequency:
            c.drawString(70, y, f"Частота: {prescription.frequency} раз(а) в день")
            y -= line_height * 2
        
    except Exception as e:
        print(f"Ошибка при генерации рецепта: {e}")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, f"Recipe for appointment {appointment.id_rec}")
    
    c.save()
    return path