'''
___________________________________________________________________________
Módulo: Visualizador.py
Descripción: Módulo encargado de la visualización de resultados de una simulación Monte Carlo distribuida.
Recibe resultados a través de RabbitMQ y muestra en tiempo real la media acumulada de los escenarios simulados
usando una interfaz web interactiva basada en Dash y Plotly.
____________________________________________________________________________
'''
from typing import Any, Dict, List, Tuple, Union
import dash
from dash import dcc, html, no_update
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import numpy as np
import pika
import json

# Hoja de estilo externa para fuentes
hojas_de_estilo_externas: List[str] = ['https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap']
host = 'localhost'

class Visualizador:
    """
    Clase principal para la visualización de la simulación Monte Carlo distribuida.
    Se encarga de crear la interfaz web, conectarse a RabbitMQ para recibir resultados,
    y actualizar en tiempo real la gráfica de la media acumulada.
    """
    def __init__(self) -> None:
        """
        Inicializa la aplicación Dash, configura el layout, conecta a RabbitMQ y
        registra los callbacks para la actualización automática del gráfico.
        """
        # Lista para almacenar los resultados recibidos
        self.resultados: List[float] = []

        # Inicializa la aplicación Dash con la hoja de estilo externa
        self.aplicacion: dash.Dash = dash.Dash(__name__, external_stylesheets=hojas_de_estilo_externas)
        
        # Define la estructura visual de la aplicación
        self.aplicacion.layout = html.Div([
            html.Div([
                html.H1("Simulación Monte Carlo", className="titulo-cabecera"),
                html.H3("Visualización de Media Acumulada", className="subtitulo-cabecera"),
            ], className="cabecera"),
            
            # Panel de estadísticos
            html.Div([
                html.Div([
                    html.H4("Estadísticos", className="titulo-estadisticos"),
                    html.Div([
                        html.Div([
                            html.P("Media:"),
                            html.P(id="valor-media", children="--")
                        ], className="estadistico"),
                        html.Div([
                            html.P("Varianza:"),
                            html.P(id="valor-varianza", children="--")
                        ], className="estadistico"),
                        html.Div([
                            html.P("Desviación Estándar:"),
                            html.P(id="valor-desviacion", children="--")
                        ], className="estadistico"),
                        html.Div([
                            html.P("Simulaciones:"),
                            html.P(id="valor-simulaciones", children="0")
                        ], className="estadistico"),
                    ], className="panel-estadisticos-contenido")
                ], className="panel-estadisticos")
            ], className="contenedor-estadisticos"),
            
            # Gráficos
            html.Div([
                # Gráfico de media acumulada
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
                                title="Media Acumulada",
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
                ], className="grafico-container"),
                
                # Histograma de resultados
                html.Div([
                    dcc.Graph(
                        id="histograma",
                        config={"displayModeBar": False},
                        figure={
                            "data": [
                                go.Histogram(
                                    x=[],
                                    marker_color='#f9c846',
                                    opacity=0.7,
                                    name="Distribución"
                                )
                            ],
                            "layout": go.Layout(
                                title="Distribución de Resultados",
                                xaxis=dict(
                                    title="Valor",
                                    gridcolor='rgba(211,211,211,0.2)',
                                    linecolor='rgba(211,211,211,0.5)'
                                ),
                                yaxis=dict(
                                    title="Frecuencia",
                                    gridcolor='rgba(211,211,211,0.2)',
                                    linecolor='rgba(211,211,211,0.5)'
                                ),
                                template="plotly_dark",
                                plot_bgcolor='rgba(33, 33, 33, 0.8)',
                                paper_bgcolor='rgba(33, 33, 33, 0.8)',
                                bargap=0.05,
                                margin=dict(l=40, r=40, t=40, b=40),
                                uirevision='constant'
                            )
                        }
                    )
                ], className="grafico-container"),
            ], className="contenedor-graficos"),
            
            # Intervalo para actualizar el gráfico periódicamente (cada 100 ms)
            dcc.Interval(id="componente-intervalo", interval=100, n_intervals=0),
            html.Footer([
                html.P("Simulación Monte Carlo Distribuida")
            ], className="pie-de-pagina")
        ], className="contenedor-principal")
        
        # Conexión a RabbitMQ para recibir los resultados de la simulación
        self.rabbit_connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, credentials=pika.PlainCredentials('guest', 'guest'))
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
            .contenedor-estadisticos {
                margin-bottom: 20px;
            }
            .panel-estadisticos {
                background-color: #1e1e1e;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .titulo-estadisticos {
                color: #f9c846;
                margin-top: 0;
                margin-bottom: 15px;
                text-align: center;
            }
            .panel-estadisticos-contenido {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
            }
            .estadistico {
                text-align: center;
                margin: 0 15px;
            }
            .estadistico p:first-child {
                color: #a7a7a7;
                margin-bottom: 5px;
            }
            .estadistico p:last-child {
                font-size: 1.2em;
                font-weight: bold;
                color: #f9c846;
                margin-top: 0;
            }
            .contenedor-graficos {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
            }
            .grafico-container {
                flex: 1 1 calc(50% - 20px);
                min-width: 450px;
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
            @media (max-width: 950px) {
                .grafico-container {
                    flex: 1 1 100%;
                }
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

    def registrar_callbacks(self) -> None:
        """
        Registra los callbacks que actualizan los gráficos y estadísticos en tiempo real
        cada vez que se recibe un nuevo resultado desde RabbitMQ.
        """
        @self.aplicacion.callback(
            [Output("grafico-en-vivo", "extendData"),
             Output("histograma", "figure"),
             Output("valor-media", "children"),
             Output("valor-varianza", "children"),
             Output("valor-desviacion", "children"),
             Output("valor-simulaciones", "children")],
            Input("componente-intervalo", "n_intervals")
        )
        def actualizar_visualizador(n: int) -> Union[
            Any,
            Tuple[Dict[str, List[List[Union[int, float]]]], Dict[str, Any], str, str, str, str]
        ]:
            """
            Callback ejecutado periódicamente por el componente Interval.
            Obtiene un nuevo resultado de la cola RabbitMQ, actualiza la lista de resultados,
            calcula la media acumulada, estadísticos y actualiza el histograma.
            """
            method, header, body = self.rabbit_channel.basic_get(
                queue='Resultados', auto_ack=True
            )
            if not method:
                return no_update, no_update, no_update, no_update, no_update, no_update

            mensaje: Dict[str, Any] = json.loads(body.decode("utf-8"))
            resultado: float = mensaje.get("resultado")
            self.resultados.append(resultado)

            id_escenario: int = len(self.resultados)
            media_acumulada: float = np.mean(self.resultados)
            
            # Calcular estadísticos
            media: float = media_acumulada
            varianza: float = np.var(self.resultados) if len(self.resultados) > 1 else 0
            desviacion: float = np.std(self.resultados) if len(self.resultados) > 1 else 0
            
            # Formatear estadísticos como cadenas con formato a 3 decimales
            media_str: str = f"{media:.3f}"
            varianza_str: str = f"{varianza:.3f}"
            desviacion_str: str = f"{desviacion:.3f}"
            simulaciones_str: str = str(id_escenario)
            
            # Crear histograma actualizado
            histograma_figura = {
                "data": [
                    go.Histogram(
                        x=self.resultados,
                        marker_color='#f9c846',
                        opacity=0.7,
                        name="Distribución",
                        nbinsx=30
                    )
                ],
                "layout": go.Layout(
                    title="Distribución de Resultados",
                    xaxis=dict(
                        title="Valor",
                        gridcolor='rgba(211,211,211,0.2)',
                        linecolor='rgba(211,211,211,0.5)'
                    ),
                    yaxis=dict(
                        title="Frecuencia",
                        gridcolor='rgba(211,211,211,0.2)',
                        linecolor='rgba(211,211,211,0.5)'
                    ),
                    template="plotly_dark",
                    plot_bgcolor='rgba(33, 33, 33, 0.8)',
                    paper_bgcolor='rgba(33, 33, 33, 0.8)',
                    bargap=0.05,
                    margin=dict(l=40, r=40, t=40, b=40),
                    uirevision='constant'
                )
            }
            
            # Devuelve los datos para actualizar la gráfica de la media acumulada
            return (
                {"x": [[id_escenario]], "y": [[media_acumulada]]},
                [0],
                1000000
            ), histograma_figura, media_str, varianza_str, desviacion_str, simulaciones_str

    def iniciar(self, debug: bool = False) -> None:
        """
        Inicia el servidor web de la aplicación Dash.
        Parámetros:
            debug (bool): Si es True, activa el modo debug de Dash.
        """
        self.aplicacion.run(debug=debug)