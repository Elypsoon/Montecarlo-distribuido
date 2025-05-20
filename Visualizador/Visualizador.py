'''
___________________________________________________________________________
Módulo: Visualizador.py
Descripción: Parte del proyecto encargado de la visualización de los datos.
Temporalmente con datos de prueba que simulan el comportamiento de los datos.
En este módulo se visualiza la simulación Monte Carlo, se crea una interfaz
web interactuva utilizando Dash y Plotly para visualizar la evolución de la 
media acomulada de los escenarios generados. 
____________________________________________________________________________
'''

import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import random
import numpy as np

# Hoja de estilo externa
hojas_de_estilo_externas = ['https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap']

class Visualizador:
    """
    Esta clase se encarga de crear y ejecutar la interfaz gráfica para visualizar la media acumulada
    de escenarios de una simulación Monte Carlo.
        resultados (list): Lista de valores generados (simulados).
        aplicacion (dash.Dash): Instancia de la aplicación Dash.
    """
    def __init__(self):
        """Inicializa la interfaz, define su estructura visual y configura 
        el estilo y los callbacks."""

        self.resultados = [] # Lista para almacenar los resultados

        self.aplicacion = dash.Dash(__name__, external_stylesheets=hojas_de_estilo_externas)  # Inicializa la aplicación Dash con una hoja de estilo externa
        
        
        self.aplicacion.layout = html.Div([  # Configura el layout de la aplicación Dash
            html.Div([
                html.H1("Simulación Monte Carlo", className="titulo-cabecera"),
                html.H3("Visualización de Media Acumulada", className="subtitulo-cabecera"),
            ], className="cabecera"),
            html.Div([
                dcc.Graph(
                    id="grafico-en-vivo",
                    config={"displayModeBar": False},
                    animate=False,
                    figure={
                        "data": [
                            go.Scatter(
                                x=[],
                                y=[],
                                mode="lines+markers",
                                name="Media Acumulada"
                            )
                        ],
                        "layout": go.Layout(
                            xaxis=dict(
                                title="Escenario",
                                gridcolor='rgba(211,211,211,0.2)',
                                linecolor='rgba(211,211,211,0.5)'
                            ),
                            yaxis=dict(
                                title="Media obtenida",
                                gridcolor='rgba(211,211,211,0.2)',
                                linecolor='rgba(211,211,211,0.5)'
                            ),
                            template="plotly_dark",
                            plot_bgcolor='rgba(33, 33, 33, 0.8)',
                            paper_bgcolor='rgba(33, 33, 33, 0.8)',
                            hovermode='closest',
                            margin=dict(l=40, r=40, t=40, b=40),
                            uirevision='constant'
                        )
                    }
                )
            ], className="contenedor-grafico"),
            # Intervalo para actualizar el gráfico periódicamente
            dcc.Interval(id="componente-intervalo", interval=100, n_intervals=0),
            html.Footer([
                html.P("Simulación Monte Carlo Distribuida")
            ], className="pie-de-pagina")
        ], className="contenedor-principal")

        # Registra los callbacks de la aplicación
        self.registrar_callbacks()

        # Define el HTML base y CSS personalizado para la aplicación
        self.aplicacion.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Simulación Monte Carlo</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                margin: 0;
                background-color: #121212;
                color: #f5f5f5;
            }
            .contenedor-principal {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .cabecera {
                text-align: center;
                margin-bottom: 30px;
            }
            .titulo-cabecera {
                color: #f9c846;
                margin-bottom: 10px;
            }
            .subtitulo-cabecera {
                color: #a7a7a7;
                font-weight: 300;
                margin-top: 0;
            }
            .contenedor-grafico {
                background-color: #1e1e1e;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .pie-de-pagina {
                text-align: center;
                margin-top: 30px;
                padding: 10px;
                color: #a7a7a7;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

    def registrar_callbacks(self):
        """Registra los callbacks necesarios para la actualización automática del gráfico."""
        # Callback para actualizar el gráfico en vivo cada vez que el intervalo se dispara
        @self.aplicacion.callback(
            Output("grafico-en-vivo", "extendData"),
            Input("componente-intervalo", "n_intervals")
        )
        def actualizar_grafico_en_vivo(n):

            """
            Callback que se ejecuta cada vez que el componente de intervalo se actualiza.
                n (int): Número de veces que se ha ejecutado el intervalo.
                tuple: Datos extendidos para el gráfico.
            """
            # Genera un nuevo valor aleatorio (simulación)
            nuevo_valor = random.gauss(0, 1)
            self.resultados.append(nuevo_valor)
            id_escenario = len(self.resultados)
            # Calcula la media acumulada de los resultados
            media_acumulada = np.mean(self.resultados)
            # Devuelve los nuevos datos para extender el gráfico
            return (
                {"x": [[id_escenario]], "y": [[media_acumulada]]},
                [0],
                200
            )

    def iniciar(self, debug=False):
        """
        Inicia el servidor de la aplicación Dash.
            debug (bool): Activa el modo debug de Dash. Útil para desarrollo.
        """
        self.aplicacion.run(debug=debug)

if __name__ == "__main__":
    # Crea una instancia del visualizador y lo inicia
    visualizador = Visualizador()
    visualizador.iniciar(debug=False)
