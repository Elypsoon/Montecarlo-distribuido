import pika
import json
import numpy as np
import multiprocessing as mp
import itertools
from Modelo import Modelo

def generar_escenario(modelo_variables):
    rng = np.random.default_rng()
    
    modelo = Modelo()
    modelo.variables.update(modelo_variables)

    return modelo.generar_escenario(rng)

class Productor:
    def __init__(self, ip: str, nom_exchange: str, nom_queue: str):
        self.conexion = pika.BlockingConnection(
            pika.ConnectionParameters(host=ip)
        )
        self.canal = self.conexion.channel()
        self.nom_exchange = nom_exchange
        self.nom_queue = nom_queue
        self.escenarios = set()
        self.modelo = Modelo()

    def configurar_conexion(self):
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type='fanout')
        self.canal.queue_declare(queue=self.nom_queue, durable=True)

    def configurar_modelo(self):
        self.modelo.configurar_modelo()

    def publicar_configuracion(self):
        print("\n\t[PRODUCTOR] Enviando configuración.")
        configuracion = json.dumps(self.modelo.obtener_configuracion())
        self.canal.basic_publish(
            exchange=self.nom_exchange, 
            routing_key='', 
            body=configuracion,
            properties=pika.BasicProperties(delivery_mode=2)
            )

    def generar_escenarios(self):
        iteraciones = self.modelo.iteraciones
        print(f"\t[PRODUCTOR] Generando {iteraciones} escenarios.")

        modelo_variables = self.modelo.obtener_variables()

        with mp.Pool() as pool:
            repetidos = itertools.repeat(modelo_variables, iteraciones)
            for escenario in pool.map(generar_escenario, repetidos):
                escenario_json = json.dumps(escenario, sort_keys=True)
                if escenario_json not in self.escenarios:
                    self.escenarios.add(escenario_json)

        print(f"\t[PRODUCTOR] Se han generado {len(self.escenarios)} escenarios únicos.")

    def publicar_escenarios(self):
        for escenario in self.escenarios:
            self.canal.basic_publish(
                exchange='', 
                routing_key=self.nom_queue, 
                body=escenario
            )

    def iniciar_productor(self):
        self.configurar_modelo()
        self.configurar_conexion()
        self.publicar_configuracion()
        self.generar_escenarios()
        self.publicar_escenarios()