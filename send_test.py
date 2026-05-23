import pika
import json

connection = pika.BlockingConnection(pika.URLParameters("amqp://admin:admin123@localhost:5672/"))
channel = connection.channel()
channel.queue_declare(queue="pdf", durable=True)

msg = {
    "target": "pdf",
    "action": "generate_pdf",
    "appointment_id": 1,        # замените на существующий ID
    "email": "test@example.com",
    "doc_type": "certificate"
}

channel.basic_publish(exchange='', routing_key='pdf', body=json.dumps(msg))
print("Сообщение отправлено")
connection.close()