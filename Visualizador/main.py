'''
    ___________________________________________________________________________
    Módulo: Visualizador.py
    Descripción: Módulo encargado de la visualización de resultados de una simulación Monte Carlo distribuida.
    Recibe resultados a través de RabbitMQ y muestra en tiempo real la media acumulada de los escenarios simulados
    usando una interfaz web interactiva basada en Dash y Plotly.
    ____________________________________________________________________________
'''
from Visualizador import Visualizador

def main() -> None:
    """
    Punto de entrada de la aplicación.
    Esta función inicializa la instancia de Visualizador y arranca el proceso de visualización llamando a su método 'iniciar' con la depuración desactivada.
    """
    
    visualizador = Visualizador()
    visualizador.iniciar(debug=False)

if __name__ == "__main__":
    main()