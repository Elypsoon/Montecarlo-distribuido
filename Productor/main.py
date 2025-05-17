from Productor import Productor

IP = 'localhost'
EXCHANGE = 'Cofiguracion'
QUEUE = 'Escenarios'

def main():
    productor = Productor(ip=IP, nom_exchange=EXCHANGE, nom_queue=QUEUE)
    productor.iniciar_productor()
    
if __name__ == '__main__':
    main()