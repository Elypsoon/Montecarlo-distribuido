"""
______________________________________________________________________________
Módulo: Main.py
Descripción: Módulo principal para ejecutar el Productor del sistema de simulación 
Montecarlo distribuido. Este script configura y lanza el productor, el cual se 
encarga de enviar la configuración y los escenarios de simulación a través de 
una cola de mensajes utilizando RabbitMQ.
______________________________________________________________________________
"""


from Productor import Productor

IP = 'localhost'
EXCHANGE = 'Cofiguracion'
QUEUE = 'Escenarios'
RUTA_MODELO = './modelo.json'

def main():
    """
    Función principal que inicializa y ejecuta el Productor. El Productor carga 
    el modelo desde un archivo JSON, envía la configuración a un exchange, y 
    luego genera y envía escenarios simulados a una cola específica.
    """
    productor = Productor(ip=IP, nom_exchange=EXCHANGE, nom_queue=QUEUE, ruta_modelo=RUTA_MODELO)
    productor.iniciar_productor()
    
if __name__ == '__main__':
    main()