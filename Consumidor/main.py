from Consumidor import Consumidor

IP = 'localhost'
EXCHANGE = 'Cofiguracion'
QUEUE_ESCENARIOS = 'Escenarios'
QUEUE_RESULTADOS = 'Resultados'

def main():
    consumidor = Consumidor(ip=IP, 
                            nom_exchange=EXCHANGE, 
                            nom_queue_escenarios=QUEUE_ESCENARIOS, 
                            nom_queue_resultados=QUEUE_RESULTADOS)
    consumidor.iniciar_consumidor()

if __name__ == "__main__":
    main()