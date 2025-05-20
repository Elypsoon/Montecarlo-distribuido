'''
Implementación de un visualizador para la simulación Monte Carlo.
Este visualizador utiliza Dash y Plotly para crear una interfaz gráfica
'''

import dash
from dash import dcc, html, no_update
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import numpy as np
import pika
import json

# Hoja de estilo externa
hojas_de_estilo_externas = ['https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap']

class Visualizador:
    def __init__(self):
        # Lista para almacenar los resultados
        self.resultados = []

        # Inicializa la aplicación Dash con una hoja de estilo externa
        self.aplicacion = dash.Dash(__name__, external_stylesheets=hojas_de_estilo_externas)
        
        # Configura el layout de la aplicación Dash
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
            # Intervalo para actualizar el gráfico periódicamente
            dcc.Interval(id="componente-intervalo", interval=100, n_intervals=0),
            html.Footer([
                html.P("Simulación Monte Carlo Distribuida")
            ], className="pie-de-pagina")
        ], className="contenedor-principal")
        
         # Conectar a RabbitMQ y declarar cola de resultados
        self.rabbit_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        self.rabbit_channel = self.rabbit_connection.channel()
        self.rabbit_channel.queue_declare(queue='Resultados')

        self.rabbit_channel.queue_purge(queue="Resultados")

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
        @self.aplicacion.callback(
            Output("grafico-en-vivo", "extendData"),
            Input("componente-intervalo", "n_intervals")
        )
        def actualizar_grafico_en_vivo(n):
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
        self.aplicacion.run(debug=debug)

if __name__ == "__main__":
    # Crea una instancia del visualizador y lo inicia
    visualizador = Visualizador()
    visualizador.iniciar(debug=False)
