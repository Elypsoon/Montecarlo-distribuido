import pika
import json
import numpy as np
from Modelo import Modelo   

class Productor:
    def __init__(self, ip: str, nom_exchange: str, nom_queue: str):
        #self.conexion = pika.BlockingConnection(
        #    pika.ConnectionParameters(host=ip)
        #)
        #self.canal = self.conexion.channel()
        self.nom_exchange = nom_exchange
        self.nom_queue = nom_queue
        self.escenarios = set()
        self.modelo = Modelo()

    #queue name y durable true
    #en publish -> properties=pika.basicproperties(pika.deliverymode.persistent)
    #channel.basic_qos(prefetch_count=1) EN CONSUMIDOR

    def configurar_conexion(self):
        self.canal.exchange_declare(exchange=self.nom_exchange, exchange_type='fanout')
        self.canal.queue_declare(queue=self.nom_queue, durable=True)

    def configurar_modelo(self):
        self.modelo.configurar_modelo()

    def publicar_configuracion(self):
        print("\n\t[PRODUCTOR] Configuración por enviar: ")
        configuracion = json.dumps(self.modelo.obtener_configuracion(), indent=4)
        print(configuracion)
        #self.canal.basic_publish(
        #    exchange=self.nom_exchange, 
        #    routing_key='', 
        #    body=configuracion,
        #    properties=pika.BasicProperties(delivery_mode=2)
        #    )

    def generar_escenarios(self):
        
        pass

    def publicar_escenarios(self):
        pass

    def iniciar_productor(self):
        self.configurar_modelo()
        #self.configurar_conexion()
        self.publicar_configuracion()
        self.generar_escenarios()
        #self.generar_escenarios()
        #self.publicar_escenario()
