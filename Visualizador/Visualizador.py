'''
___________________________________________________________________________
Módulo: Visualizador.py
Descripción: Módulo encargado de la visualización de resultados de una simulación Monte Carlo distribuida.
Recibe resultados a través de RabbitMQ y muestra en tiempo real la media acumulada de los escenarios simulados
usando una interfaz web interactiva basada en Dash y Plotly.
____________________________________________________________________________
'''

import dash
from dash import dcc, html, no_update
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import numpy as np
import pika
import json

# Hoja de estilo externa para fuentes
hojas_de_estilo_externas = ['https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap']

class Visualizador:
    """
    Clase principal para la visualización de la simulación Monte Carlo distribuida.
    Se encarga de crear la interfaz web, conectarse a RabbitMQ para recibir resultados,
    y actualizar en tiempo real la gráfica de la media acumulada.
    """
    def __init__(self):
        """
        Inicializa la aplicación Dash, configura el layout, conecta a RabbitMQ y
        registra los callbacks para la actualización automática del gráfico.
        """
        # Lista para almacenar los resultados recibidos
        self.resultados = []

        # Inicializa la aplicación Dash con la hoja de estilo externa
        self.aplicacion = dash.Dash(__name__, external_stylesheets=hojas_de_estilo_externas)
        
        # Define la estructura visual de la aplicación
        self.aplicacion.layout = html.Div([
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
            # Intervalo para actualizar el gráfico periódicamente (cada 100 ms)
            dcc.Interval(id="componente-intervalo", interval=100, n_intervals=0),
            html.Footer([
                html.P("Simulación Monte Carlo Distribuida")
            ], className="pie-de-pagina")
        ], className="contenedor-principal")
        
        # Conexión a RabbitMQ para recibir los resultados de la simulación
        self.rabbit_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='172.26.161.229', credentials=pika.PlainCredentials('guest', 'guest'))
        )
        self.rabbit_channel = self.rabbit_connection.channel()
        self.rabbit_channel.queue_declare(queue='Resultados')

        # Limpia la cola de resultados al iniciar la aplicación
        self.rabbit_channel.queue_purge(queue="Resultados")

        # Registra los callbacks de la aplicación Dash
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
        """
        Registra el callback que actualiza el gráfico en tiempo real cada vez que
        se recibe un nuevo resultado desde RabbitMQ.
        """
        @self.aplicacion.callback(
            Output("grafico-en-vivo", "extendData"),
            Input("componente-intervalo", "n_intervals")
        )
        def actualizar_grafico_en_vivo(n):
            """
            Callback ejecutado periódicamente por el componente Interval.
            Obtiene un nuevo resultado de la cola RabbitMQ, actualiza la lista de resultados,
            calcula la media acumulada y extiende el gráfico con el nuevo valor.
            """
            method, header, body = self.rabbit_channel.basic_get(
                queue='Resultados', auto_ack=True
            )
            if not method:
                return no_update

            mensaje = json.loads(body.decode("utf-8"))
            resultado = mensaje.get("resultado")
            self.resultados.append(resultado)

            id_escenario = len(self.resultados)
            media_acumulada = np.mean(self.resultados)

            return (
                {"x": [[id_escenario]], "y": [[media_acumulada]]},
                [0],
                200
            )

    def iniciar(self, debug=False):
        """
        Inicia el servidor web de la aplicación Dash.
        Parámetros:
            debug (bool): Si es True, activa el modo debug de Dash.
        """
        self.aplicacion.run(debug=debug)

if __name__ == "__main__":
    # Crea una instancia del visualizador y lo inicia
    visualizador = Visualizador()
    visualizador.iniciar(debug=False)
