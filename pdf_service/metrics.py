# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Счетчики
pdf_generated_total = Counter(
    'pdf_generated_total',
    'Total number of generated PDF documents',
    ['doc_type', 'status']   # doc_type: certificate, recipe, referral; status: success, error
)

rabbit_messages_total = Counter(
    'rabbit_messages_processed_total',
    'Total RabbitMQ messages processed',
    ['action', 'status']
)

# Гистограмма времени генерации PDF (в секундах)
pdf_generation_duration = Histogram(
    'pdf_generation_duration_seconds',
    'Time spent generating PDF',
    ['doc_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf'))
)

# Текущее количество активных генераций (воркеров)
active_generations = Gauge(
    'pdf_active_generations',
    'Number of PDF generations currently in progress'
)

# Метрика ошибок
pdf_errors_total = Counter(
    'pdf_errors_total',
    'Total number of PDF generation errors',
    ['doc_type', 'error_type']
)

def get_metrics():
    """Возвращает метрики в формате Prometheus"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)