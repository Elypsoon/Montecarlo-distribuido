"""
__________________________________________________________________________________________
Módulo: Productor.py
Descripción: Implementa el Productor del sistema de simulación Montecarlo distribuido.
Este módulo se encargar de las siguientes acciones: 
    1. Lee un modelo desde un archivo JSON.
    2. Publica la configuración del modelo en un exchange de RabbitMQ.
    3. Generar múltiples escenarios simulados en paralelo.
    4. Envia los escenarios a una cola de mensajes.
Este módulo utiliza multiprocessing para acelerar la generación de escenarios y pika para la
comunicación con RabbitMQ.
"""
import pika
import json
import numpy as np
import multiprocessing as mp
from typing import Any, Dict
from Modelo import Modelo

modelo_global: Modelo = None

def iniciar_pool(ruta_modelo: str, variables: Dict[str, Any]) -> None:
    """
    Función de inicialización de procesos, se encarga de cargar cada proceso hijo.
        ruta_modelo (str): Ruta al archivo del modelo JSON.
        variables (dict): Definiciones de las variables del modelo.
    """
    global modelo_global
    modelo_global = Modelo(ruta_modelo=ruta_modelo)
    modelo_global.configurar_modelo()
    modelo_global.variables = variables

def generar_escenario(_: int) -> str:
    """
    Genera un escenario simulado usando el modelo global y lo serializa en JSON.
        _: Valor ignorado que permite la iteración.
        Returns: Escenario generado en formato JSON.
    """
    rng = np.random.default_rng()
    escenario = modelo_global.generar_escenario(rng=rng)
    return json.dumps(escenario, sort_keys=True)

class Productor:
    """
    Clase que representa el productor del sistema Montecarlo distribuido.
    Esta clase sirve para gestionar la conexión con RabbitMQ, la carga del modelo, 
    la generación paralela de escenarios y el envío de resultados a una cola.
    """
    def __init__(self, ip: str, nom_exchange: str, nom_queue: str, ruta_modelo: str) -> None:
        """
        Inicializa el productor con la conexión y configuración del modelo.
            ip (str): Dirección IP del servidor de RabbitMQ.
            nom_exchange (str): Nombre del exchange para enviar la configuración.
            nom_queue (str): Nombre de la cola para publicar los escenarios.
            ruta_modelo (str): Ruta al archivo JSON con el modelo.
        """
        self.conexion: pika.BlockingConnection = pika.BlockingConnection(
            pika.ConnectionParameters(host=ip, credentials=pika.PlainCredentials("guest", "guest"))
        )
        self.canal = self.conexion.channel()
        self.ruta_modelo: str = ruta_modelo
        self.nom_exchange: str = nom_exchange
        self.nom_queue: str = nom_queue
        self.escenarios: set = set()
        self.modelo: Modelo = Modelo(ruta_modelo=ruta_modelo)

    def configurar_conexion(self) -> None:
        """
        Declara el exchange y la cola en RabbitMQ para asegurar que existan.
        """
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type='fanout')
        self.canal.queue_declare(queue=self.nom_queue, durable=True)

    def configurar_modelo(self) -> None:
        """
        Carga la configuración del modelo desde el archivo JSON.
        """
        self.modelo.configurar_modelo()
        print("[MODELO] Modelo cargado correctamente")

    def publicar_configuracion(self) -> None:
        """
        Publica la configuración del modelo (fórmula y constantes) al exchange.
        """
        print("[PRODUCTOR] Enviando configuración.")
        mensaje: str = json.dumps(self.modelo.obtener_configuracion())
        
        self.canal.basic_publish(
            exchange=self.nom_exchange, 
            routing_key='', 
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def generar_escenarios(self) -> None:
        """
        Genera escenarios aleatorios en paralelo utilizando un pool de procesos.
        Cada escenario es generado por un proceso hijo, serializado a JSON y enviado a la cola de RabbitMQ.
        Además, almacena los escenarios generados en el atributo `self.escenarios` para evitar duplicados.
        """
        iteraciones: int = self.modelo.iteraciones
        variables: Dict[str, Any] = self.modelo.variables

        print(f"[PRODUCTOR] Generando {iteraciones} escenarios en paralelo.")

        with mp.Pool(
            initializer=iniciar_pool,
            initargs=(self.ruta_modelo, variables)
        ) as pool:
            for escenario_json in pool.imap_unordered(generar_escenario, range(iteraciones)):
                self.canal.basic_publish(
                    exchange='',
                    routing_key=self.nom_queue,
                    body=escenario_json,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                
                self.escenarios.add(escenario_json)
        
        print(f"[PRODUCTOR] Se han enviado {len(self.escenarios)} escenarios únicos.")

    def iniciar_productor(self) -> None:
        """
        Ejecuta el flujo principal del productor:
        1. Carga la configuración del modelo desde el archivo JSON.
        2. Declara el exchange y la cola en RabbitMQ.
        3. Publica la configuración del modelo en el exchange.
        4. Genera escenarios en paralelo y los envía a la cola de RabbitMQ.
        5. Cierra la conexión con RabbitMQ al finalizar.
        """
        self.configurar_modelo()
        self.configurar_conexion()
        self.publicar_configuracion()
        self.generar_escenarios()
        self.conexion.close()