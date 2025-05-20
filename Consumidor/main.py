"""
____________________________________________________________________________________
Módulo: main.py
Descripción: Este es un sistema distribuido de procesamiento de mensajes que realiza
las siguientes funciones:
    1. Recibe escenarios desde una cola.
    2. Evalúa esos escenarios.
    3. Publica los resultados en otra cola.
_____________________________________________________________________________________
"""

from Consumidor import Consumidor

IP = '172.26.161.229'
EXCHANGE = 'Cofiguracion'
QUEUE_ESCENARIOS = 'Escenarios'
QUEUE_RESULTADOS = 'Resultados'

def main():
    """
    Función principal del consumidor.
    Este script representa la parte del sistema se encarga de las siguientes funciones:
        1. Escucha la configuración enviada por el productor.
        2. Escucha escenarios generados y recibidos en la cola correspondiente.
        3. Evalua los escenarios usando la fórmula y constantes proporcionadas.
        4. Publica los resultados en la cola de resultados.
    Utiliza una instancia de la clase `Consumidor` para realizar todo el flujo de trabajo.
    """
    consumidor = Consumidor(ip=IP, 
                            nom_exchange=EXCHANGE, 
                            nom_queue_escenarios=QUEUE_ESCENARIOS, 
                            nom_queue_resultados=QUEUE_RESULTADOS)
    consumidor.iniciar_consumidor()

if __name__ == "__main__":
    main()