import numpy as np
import json

class Modelo:
    def __init__(self, ruta_modelo: str):
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
        self.formula = self.configuracion_modelo["formula"]
        self.iteraciones = self.configuracion_modelo["iteraciones"]
        self.num_variables = self.configuracion_modelo["num_variables"]
        self.constantes = self.configuracion_modelo["constantes"]
        self.variables = self.configuracion_modelo["variables"]

        print("[MODELO] Modelo cargado correctamente")

    def obtener_configuracion(self) -> dict:
        configuracion = {
            "formula": self.formula,
            **self.constantes
        }

        return configuracion
            
    def obtener_variables(self):
        return self.variables

    def generar_escenario(self, rng: np.random.Generator) -> dict:
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