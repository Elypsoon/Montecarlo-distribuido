'''
___________________________________________________________________________
Módulo: main.py
Descripción: Punto de entrada de la aplicación Visualizador.
Este script permite configurar de forma variable los parámetros de conexión, el nombre de la cola
y el modo debug, de forma similar al enfoque usado en el Consumidor.
____________________________________________________________________________
'''
from Visualizador import Visualizador

# Parámetros configurables para el Visualizador
IP: str = 'localhost'
COLA: str = 'Resultados'
DEBUG: bool = False         

def main() -> None:
    """
    Función principal que inicializa el visualizador con los parámetros configurados
    y arranca el servidor web para la visualización de la simulación.
    """
    visualizador = Visualizador(host=IP, cola=COLA)
    visualizador.iniciar(debug=DEBUG)

if __name__ == "__main__":
    main()