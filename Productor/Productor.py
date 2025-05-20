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
import itertools
from Modelo import Modelo

modelo_global = None

def iniciar_pool(ruta_modelo: str, variables: dict):
    """
    Función de inicialización de procesos, se encarga de cargar cada proceso hijo.
        ruta_modelo (str): Ruta al archivo del modelo JSON.
        variables (dict): Definiciones de las variables del modelo.
    """
    global modelo_global
    modelo_global = Modelo(ruta_modelo=ruta_modelo)
    modelo_global.configurar_modelo()
    modelo_global.variables = variables

def generar_escenario(_):
    """
    Genera un escenario simulado usando el modelo global y lo serializa en JSON.
        str: Escenario generado en formato JSON.
    """
    rng = np.random.default_rng()
    escenario = modelo_global.generar_escenario(rng=rng)
    print(f"El escenario generado es: {escenario}")
    return json.dumps(escenario, sort_keys=True)

class Productor:

    """
    Clase que representa el productor del sistema Montecarlo distribuido.
    Esta clase sirve para gestiona la conexión con RabbitMQ, la carga del modelo, 
    la generación paralela de escenarios y el envío de resultados a una cola.
    """
    def __init__(self, ip: str, nom_exchange: str, nom_queue: str, ruta_modelo: str):
        """
        Inicializa el productor con la conexión y configuración del modelo.
            ip (str): Dirección IP del servidor de RabbitMQ.
            nom_exchange (str): Nombre del exchange para enviar la configuración.
            nom_queue (str): Nombre de la cola para publicar los escenarios.
            ruta_modelo (str): Ruta al archivo JSON con el modelo.
        """

        self.conexion = pika.BlockingConnection(
            pika.ConnectionParameters(host=ip)
        )
        self.canal = self.conexion.channel()
        self.ruta_modelo = ruta_modelo
        self.nom_exchange = nom_exchange
        self.nom_queue = nom_queue
        self.escenarios = set()
        self.modelo = Modelo(ruta_modelo=ruta_modelo)

    def configurar_conexion(self):
        """
        Declara el exchange y la cola en RabbitMQ para asegurar que existan.
        """
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type='fanout')
        self.canal.queue_declare(queue=self.nom_queue, durable=True)

    def configurar_modelo(self):
        """
        Carga la configuración del modelo desde el archivo JSON.
        """
        self.modelo.configurar_modelo()

    def publicar_configuracion(self):
        """
        Publica la configuración del modelo (fórmula y constantes) al exchange.
        """
        print("[PRODUCTOR] Enviando configuración.")
        print(f"[PRODUCTOR] La configuración del modelo es: {self.modelo.obtener_configuracion()}")
        mensaje = json.dumps(self.modelo.obtener_configuracion())
        
        self.canal.basic_publish(
            exchange=self.nom_exchange, 
            routing_key='', 
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
            )

    def generar_escenarios(self):
        """
        Genera escenarios aleatorios en paralelo usando un pool de procesos.
        Tambien, almacena los escenarios generados en el atributo `self.escenarios`.
        """
        iteraciones = self.modelo.iteraciones
        variables = self.modelo.variables

        print(f"[PRODUCTOR] Generando {iteraciones} escenarios en paralelo.")

        with mp.Pool(
            initializer=iniciar_pool,
            initargs=(self.ruta_modelo, variables)
        ) as pool:
            for escenario_json in pool.map(generar_escenario, range(iteraciones)):
                self.escenarios.add(escenario_json)
        
        print(f"[PRODUCTOR] Se han generado {len(self.escenarios)} escenarios únicos.")

    def publicar_escenarios(self):
        """
        Publica todos los escenarios generados en la cola definida.
        """
        for escenario in self.escenarios:
            self.canal.basic_publish(
                exchange='', 
                routing_key=self.nom_queue, 
                body=escenario
            )

    def iniciar_productor(self):
        """
        Ejecuta todo el ciclo del productor: 
        - carga modelo,
        - configura conexión,
        - publica configuración,
        - genera y publica escenarios.
        """
        self.configurar_modelo()
        self.configurar_conexion()
        self.publicar_configuracion()
        self.generar_escenarios()
        self.publicar_escenarios()