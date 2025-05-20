"""
_____________________________________________________________________________________
Modelo: Modelo.py
Descripción: Define y generar escenarios de simulación o experimentación estadística,
usando variables aleatorias configuradas por el usuario en un archivo JSON.
Funciones clave: 
    1. Lee configuración desde un archivo JSON
    2. Configura los atributos del modelo.
    3. Obtiene configuración básica del modelo.
    4. Genera un escenario aleatorio de variables.
    5. Obtiene las variables definidas del modelo.
_____________________________________________________________________________________
"""


import numpy as np
import json

class Modelo:
    def __init__(self, ruta_modelo: str):
        """
        Inicializa una instancia del modelo leyendo la configuración desde un archivo JSON.

        Argumentos:   
            ruta_modelo (str): Rutea el archivo JSON que contiene la configuración del modelo.

        Atributos:
            self.configuracion_modelo (dict): Diccionario con los datos del archivo JSON.
            self.formula (str): Fórmula para evaluar el modelo.
            self.iteraciones (int): Cantidad de iteraciones para la simulación.
            self.num_variables (int): Número de variables aleatorias.
            self.constantes (dict): Constantes del modelo.
            self.variables (dict): Definiciones de las variables aleatorias.
        """
        try:            
            with open(ruta_modelo, "r") as modelo:
                self.configuracion_modelo = json.load(modelo)
            self.formula = None
            self.iteraciones = None
            self.num_variables = None
            self.constantes = None
            self.variables = None
        except FileNotFoundError:
            print(f"ERROR: El archivo {ruta_modelo} no existe.")
        except json.JSONDecodeError:
            print(f"ERROR: El archivo {ruta_modelo} no cumple con el formato JSON.")

    def configurar_modelo(self):
        """
        Asigna los valores de configuración del modelo desde el archivo JSON a los 
        atributos internos de la clase.
        """
        self.formula = self.configuracion_modelo["formula"]
        self.iteraciones = self.configuracion_modelo["iteraciones"]
        self.num_variables = self.configuracion_modelo["num_variables"]
        self.constantes = self.configuracion_modelo["constantes"]
        self.variables = self.configuracion_modelo["variables"]

        print("[MODELO] Modelo cargado correctamente")

    def obtener_configuracion(self) -> dict:
        """
        Obtiene la configuración del modelo que incluye la fórmula y las constantes.
            dict: Diccionario con la fórmula y constantes del modelo.
        """
        configuracion = {
            "formula": self.formula,
            **self.constantes
        }

        return configuracion
            
    def obtener_variables(self):
        """
        Retorna las definiciones de las variables aleatorias del modelo.        
            dict: Diccionario con las variables y sus distribuciones asociadas.
        """
        return self.variables

    def generar_escenario(self, rng: np.random.Generator) -> dict:
        """
        Genera un escenario aleatorio con base en las distribuciones de las variables.
            rng (np.random.Generator): Generador de números aleatorios de NumPy.
            dict: Retorna diccionario con los valores simulados para cada variable.
        """
        escenario = {}
        for nombre, definicion in self.variables.items():
            tipo = definicion["tipo"]
            p = definicion["parametros"]

            if tipo == "discreta":
                v = rng.choice(a=p["valores"], p=p["probabilidades"])

            elif tipo == "continua":
                dist = p["distribucion"]

                if dist == "uniforme":
                    v = rng.uniform(p["limite_inferior"], p["limite_superior"])

                elif dist == "normal":
                    v = rng.normal(p["media"], p["desviacion"])
                    # Aplicar límites si existen
                    li = p.get("limite_inferior")
                    ls = p.get("limite_superior")
                    if li is not None and ls is not None:
                        v = np.clip(v, li, ls)
            escenario[nombre] = float(v)

        return escenario