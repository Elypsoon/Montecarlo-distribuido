"""
______________________________________________________________________________
Módulo: main.py
Descripción: Script principal para ejecutar el productor del sistema de simulación 
Montecarlo distribuido. Este script inicializa el productor, que se encarga de 
leer un modelo desde un archivo JSON y enviar tanto la configuración como los 
escenarios de simulación a través de RabbitMQ, utilizando un exchange y una cola 
específicos.
______________________________________________________________________________
"""

from Productor import Productor

IP = 'localhost'
EXCHANGE = 'Cofiguracion'  # Nombre del exchange donde se enviará la configuración
QUEUE = 'Escenarios'       # Nombre de la cola donde se enviarán los escenarios
RUTA_MODELO = './modelo.json'  # Ruta al archivo JSON con el modelo de simulación

def main():
    """
    Función principal que crea una instancia del Productor, carga el modelo de 
    simulación desde un archivo JSON, y utiliza RabbitMQ para enviar la 
    configuración al exchange y los escenarios generados a la cola indicada.
    """
    productor = Productor(ip=IP, nom_exchange=EXCHANGE, nom_queue=QUEUE, ruta_modelo=RUTA_MODELO)
    productor.iniciar_productor()
    
if __name__ == '__main__':
    main()