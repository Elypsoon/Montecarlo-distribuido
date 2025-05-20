"""
__________________________________________________________________________________________________________________________________________
Módulo: Consumidor.py
Descripción: El Consumidor es un proceso autónomo que se encarga de ejecutar simulaciones Montecarlo a partir de los escenarios enviados 
por el productor. Principalmente se encarga de recibir una configuración y luego procesar escenarios usando mensajes intercambiados con 
RabbitMQ que es un sistema de mensajería basado en colas. El consumidor procesa dos tipos de mensajes, despues ejecuta la formula con las 
variables recibidas y finalmente se publica el resultado en otra cola.
    1.Configuración inicial con formula matematica. 
    2. escenarios con valores variables. 
__________________________________________________________________________________________________________________________________________
"""

import pika
import json
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

class Consumidor:
    """
    Clase que implementa un consumidor de mensajes con RabbitMQ para procesar escenarios de simulación.

    Cuenta con dos funcionalidades, son las siguientes:
    1. Recibe una configuración que incluye una fórmula y constantes.
    2. Procesa escenarios usando dicha fórmula y publica los resultados en otra cola.

    Atributos:
        conexion (pika.BlockingConnection): Conexión al servidor RabbitMQ.
        canal (pika.channel.Channel): Canal de comunicación con RabbitMQ.
        nom_exchange (str): Nombre del exchange.
        nom_queue_escenarios (str): Nombre de la cola desde donde se reciben los escenarios.
        nom_queue_resultados (str): Nombre de la cola donde se publican los resultados.
        formula (str | None): Fórmula matemática a evaluar.
        constantes (dict): Diccionario con las constantes necesarias para la evaluación.
    """

    def __init__(self, ip: str, nom_exchange: str, nom_queue_escenarios: str, nom_queue_resultados: str) -> None:
        self.conexion: pika.BlockingConnection = pika.BlockingConnection(pika.ConnectionParameters(host=ip))
        self.canal: pika.channel.Channel = self.conexion.channel()
        self.nom_exchange: str = nom_exchange
        self.nom_queue_escenarios: str = nom_queue_escenarios
        self.nom_queue_resultados: str = nom_queue_resultados
        self.formula: str | None = None
        self.constantes: dict = {}

    def callback_configuracion(self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
        """
        Maneja la recepción de mensajes de configuración.
        Extrae la fórmula y las constantes del mensaje.

        Args:
            ch (BlockingChannel): Canal que recibe el mensaje.
            method (Basic.Deliver): Información del método de entrega.
            properties (BasicProperties): Propiedades del mensaje.
            body (bytes): Contenido del mensaje en formato JSON.
        """
        configuracion: dict = json.loads(body.decode("utf-8"))
        self.formula = configuracion.get("formula")
        self.constantes = {
            nombre: valor for nombre, valor in configuracion.items()
            if nombre != "formula"
        }
        print(f"[CONSUMIDOR] Configuración recibida.")
        ch.stop_consuming()

    def callback_escenario(self, ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
        """
        Maneja la recepción de un escenario, evalúa la fórmula y publica el resultado.

        Args:
            ch (BlockingChannel): Canal que recibe el mensaje.
            method (Basic.Deliver): Información del método de entrega.
            properties (BasicProperties): Propiedades del mensaje.
            body (bytes): Contenido del mensaje en formato JSON.
        """
        escenario: dict = json.loads(body.decode("utf-8"))

        simulacion: dict = {}
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

        mensaje: str = json.dumps({"resultado": resultado})
        self.canal.basic_publish(
            exchange="",
            routing_key=self.nom_queue_resultados,
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def configurar_conexion(self) -> None:
        """
        Declara el exchange y las colas necesarias, y configura el control de flujo de mensajes.
        """
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type="fanout")
        self.canal.queue_declare(queue=self.nom_queue_escenarios, durable=True)
        self.canal.queue_declare(queue=self.nom_queue_resultados)
        self.canal.basic_qos(prefetch_count=1)

    def recibir_configuracion(self) -> None:
        """
        Escucha temporalmente el exchange para recibir un único mensaje de configuración.
        Lanza una excepción si no se recibe la fórmula o las constantes.
        """
        cola = self.canal.queue_declare(queue="", exclusive=True)
        cola_configuracion: str = cola.method.queue

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

    def procesar_escenarios(self) -> None:
        """
        Comienza a consumir escenarios desde la cola correspondiente y los procesa.
        """
        print("[CONSUMIDOR]: Esperando escenarios...")

        self.canal.basic_qos(prefetch_count=1)
        self.canal.basic_consume(
            queue=self.nom_queue_escenarios,
            on_message_callback=self.callback_escenario
        )
        self.canal.start_consuming()

    def iniciar_consumidor(self) -> None:
        """
        Método principal que inicia todo el flujo del consumidor:
            - Configura conexión y colas.
            - Purga la cola de escenarios.
            - Espera y procesa la configuración.
            - Comienza el procesamiento de escenarios.
        """
        self.configurar_conexion()
        self.canal.queue_purge(queue=self.nom_queue_escenarios)
        self.recibir_configuracion()
        self.procesar_escenarios()
