import pika
import json

class Consumidor:
    def __init__(self, ip: str, nom_exchange: str, nom_queue_escenarios: str, nom_queue_resultados: str):
        self.conexion = pika.BlockingConnection(pika.ConnectionParameters(host=ip))
        self.canal = self.conexion.channel()
        self.nom_exchange = nom_exchange
        self.nom_queue_escenarios = nom_queue_escenarios
        self.nom_queue_resultados = nom_queue_resultados
        self.formula = None
        self.constantes = {}

    def callback_configuracion(self, ch, method, properties, body):
        configuracion = json.loads(body.decode("utf-8"))
        self.formula = configuracion.get("formula")
        self.constantes = {
            nombre: valor for nombre, valor in configuracion.items()
            if nombre != "formula"
        }
        print(f"[CONSUMIDOR] Configuración recibida.")

        ch.stop_consuming()

    def callback_escenario(self, ch, method, properties, body):
        escenario = json.loads(body.decode("utf-8"))

        simulacion = {}
        simulacion.update(self.constantes)
        simulacion.update(escenario)

        try:
            resultado = eval(
                self.formula,
                {"__builtins__": None},
                simulacion
            )
        except Exception as e:
            print(f"[CONSUMIDOR - ERROR]: error al evaluar fórmula: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        mensaje = json.dumps({"resultado": resultado})
        self.canal.basic_publish(
            exchange="",
            routing_key=self.nom_queue_resultados,
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    def configurar_conexion(self):
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type="fanout")
        self.canal.queue_declare(queue=self.nom_queue_escenarios, durable=True)
        self.canal.queue_declare(queue=self.nom_queue_resultados)
        self.canal.basic_qos(prefetch_count=1)

    def recibir_configuracion(self):

        cola = self.canal.queue_declare(queue="", exclusive=True)
        cola_configuracion = cola.method.queue

        self.canal.queue_bind(exchange=self.nom_exchange, queue=cola_configuracion)

        print("[CONSUMIDOR] Esperando configuración...")
        self.canal.basic_consume(
            queue=cola_configuracion,
            on_message_callback=self.callback_configuracion,
            auto_ack=True
        )

        self.canal.start_consuming()

        if not self.formula or not self.constantes:
            raise RuntimeError("No se recibió fórmula o constantes en la configuración.")

    def procesar_escenarios(self):
        print("[CONSUMIDOR]: Esperando escenarios...")

        self.canal.basic_qos(prefetch_count=1)
        self.canal.basic_consume(
            queue=self.nom_queue_escenarios,
            on_message_callback=self.callback_escenario
        )
        self.canal.start_consuming()

    def iniciar_consumidor(self):
        self.configurar_conexion()
        self.canal.queue_purge(queue=self.nom_queue_escenarios)
        self.recibir_configuracion()
        self.procesar_escenarios()