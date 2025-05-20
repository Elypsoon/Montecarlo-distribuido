import pika
import json
import numpy as np
import multiprocessing as mp
from Modelo import Modelo

modelo_global = None

def iniciar_pool(ruta_modelo: str, variables: dict):
    global modelo_global
    modelo_global = Modelo(ruta_modelo=ruta_modelo)
    modelo_global.configurar_modelo()
    modelo_global.variables = variables

def generar_escenario(_):
    rng = np.random.default_rng()
    escenario = modelo_global.generar_escenario(rng=rng)
    return json.dumps(escenario, sort_keys=True)

class Productor:
    def __init__(self, ip: str, nom_exchange: str, nom_queue: str, ruta_modelo: str):
        self.conexion = pika.BlockingConnection(
            pika.ConnectionParameters(host=ip, credentials=pika.PlainCredentials("guest", "guest"))
        )
        self.canal = self.conexion.channel()
        self.ruta_modelo = ruta_modelo
        self.nom_exchange = nom_exchange
        self.nom_queue = nom_queue
        self.escenarios = set()
        self.modelo = Modelo(ruta_modelo=ruta_modelo)

    def configurar_conexion(self):
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type='fanout')
        self.canal.queue_declare(queue=self.nom_queue, durable=True)

    def configurar_modelo(self):
        self.modelo.configurar_modelo()
        print("[MODELO] Modelo cargado correctamente")

    def publicar_configuracion(self):
        print("[PRODUCTOR] Enviando configuración.")
        mensaje = json.dumps(self.modelo.obtener_configuracion())
        
        self.canal.basic_publish(
            exchange=self.nom_exchange, 
            routing_key='', 
            body=mensaje,
            properties=pika.BasicProperties(delivery_mode=2)
            )

    def generar_escenarios(self):
        iteraciones = self.modelo.iteraciones
        variables = self.modelo.variables

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

    def iniciar_productor(self):
        self.configurar_modelo()
        self.configurar_conexion()
        self.publicar_configuracion()
        self.generar_escenarios()
        self.conexion.close()