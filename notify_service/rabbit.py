import pika, json, os, time

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE = "main_queue"


def get_connection():
    for i in range(10):
        try:
            return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL + "?heartbeat=0"))
        except:
            print(f"RabbitMQ не готов ({i+1}/10)...")
            time.sleep(3)
    raise Exception("RabbitMQ недоступен")


def publish(data: dict):
    """
    Отправляет сообщение в очередь. 
    Принимает один аргумент - словарь с данными.
    """
    # Достаем имя очереди из словаря
    queue_name = data.get("target")
    if not queue_name:
        print("[RabbitMQ] ❌ Ошибка: в данных нет ключа 'target'")
        return

    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    import json
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(data), # Превращаем словарь в строку
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print(f"[RabbitMQ] ↗️ Отправлено в '{queue_name}': {data.get('action')}-{data.get('doc_type')}")
    connection.close()


def consume(queue_name: str, handlers: dict):
    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch, method, properties, body):
        # --- ДОБАВЬ ЭТУ СТРОКУ ДЛЯ ПРОВЕРКИ ---
        print(f"!!! [BROKER] К нам прилетело сообщение в очередь '{queue_name}' !!!", flush=True)
        # --------------------------------------
        
        import json
        msg = json.loads(body)
        action = msg.get("action")
        
        print(f"[RabbitMQ] ↙️ Получено действие: {action}", flush=True)

        if action in handlers:
            try:
                handlers[action](msg)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"❌ Ошибка воркера: {e}", flush=True)
        else:
            print(f"⚠️ Действие {action} не найдено в обработчиках", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming()