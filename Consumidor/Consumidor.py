import pika
import json

class Consumidor:
    def __init__(self, ip: str, nom_exchange: str, nom_queue_escenarios: str, nom_queue_resultados: str):
        self.conexion = pika.BlockingConnection(pika.ConnectionParameters(host=ip))
        self.canal = self.conexion.channel()
        self.nom_exchange = nom_exchange
        self.nom_queue_escenarios = nom_queue_escenarios
        self.nom_queue_resultados = nom_queue_resultados
        self.configuracion = {}
        self.formula = None
        self.constantes = {}

    def callback_configuracion(self, ch, method, properties, body):
        configuracion = body.decode('utf-8')
        self.configuracion.update(json.loads(configuracion))
        ch.stop_consuming()

    def callback_escenario(self, ch, method, properties, body):
        escenario = json.loads(body.decode('utf-8'))
        simulacion = {}
        simulacion.update(self.constantes)
        simulacion.update(escenario)

        try:
            if self.formula in None or not self.constantes:
                raise ValueError("Fórmula o constantes no configuradas correctamente")
            resultado = eval(self.formula, {"__builtins__": None}, simulacion)
        except Exception as e:
            print(f"[CONSUMIDOR - ERROR]: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        mensaje = {'resultado': resultado}
        cuerpo = json.dumps(mensaje)

        ch.basic_publish(
            exchange='',
            routing_key=self.nom_queue_resultados,
            body=cuerpo,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def configurar_conexion(self):
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type="fanout")
        self.canal.queue_declare(queue=self.nom_queue_escenarios, durable=True)
        self.canal.queue_declare(queue=self.nom_queue_resultados)

    def recibir_configuracion(self):
        resultado = self.canal.queue_declare(queue="", exclusive=True)
        nom_queue_config = resultado.method.queue
        self.canal.queue_bind(exchange=self.nom_exchange, queue=nom_queue_config)

        self.canal.basic_consume(queue=nom_queue_config, on_message_callback=self.callback_configuracion, auto_ack=True)

        print("[CONSUMIDOR] Esperando configuración...")

        self.canal.start_consuming()

        if not self.configuracion:
            raise ValueError("La configuración no se recibió correctamente.")

        self.formula = self.configuracion['formula']
        self.constantes = self.configuracion['constantes']

        print(f"[CONSUMIDOR] Configuración recibida: {self.configuracion}")

    def procesar_escenarios(self):
        print("[CONSUMIDOR]: Esperando escenarios...")

        self.canal.basic_consume(
            queue=self.nom_queue_escenarios,
            on_message_callback=self.callback_escenario
        )

        self.canal.start_consuming()

    def iniciar_consumidor(self):
        self.configurar_conexion()
        self.recibir_configuracion()
        self.procesar_escenarios()