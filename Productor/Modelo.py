import numpy as np

class Modelo:
    def __init__(self):
        self.formula = None
        self.num_variables = 0
        self.variables = {}
        self.iteraciones = 0

    def configurar_modelo(self) -> None:
        print("\n\t[MODELO] Configuración del modelo.")
        try:
            self.iteraciones = int(input("Ingrese el número de iteraciones de la simulación: "))
            self.num_variables = int(input("Ingrese el número de variables del modelo: "))

            i = 1
            while i <= self.num_variables:
                print(f"\nVARIABLE {i} DE {self.num_variables}")
                
                nombre = input("Ingrese el nombre de la variable: ").strip()
                if nombre in self.variables:
                    print("El nombre ingresado ya existe. Intente con otro.")
                    continue
                
                tipo = input("Tipo de variable [1: Constante, 2: Variable]: ").strip()
                if tipo not in ('1','2'):
                    print("Opción inválida; ingrese 1 o 2.")
                    continue

                if tipo == '1':
                    try:
                        valor = float(input(f"Ingrese el valor de la constante '{nombre}': "))
                        self.variables[nombre] = ('const', valor)
                        i += 1
                    except ValueError:
                        print("Valor inválido; ingrese un número.")

                else:
                    subtipo = input("Subtipo de variable [1: Discreta, 2: Continua]: ").strip()
                    if subtipo not in ('1','2'):
                        print("Opción inválida; ingrese 1 o 2.")
                        continue

                    if subtipo == '1':
                        datos = input("Ingrese pares valor:probabilidad separados por comas (ej: 1:0.2, 2:0.8): ").strip()
                        try:
                            pares = [par.strip() for par in datos.split(',') if par.strip()]
                            valores = []
                            propabilidades = []
                            for par in pares:
                                valor, probabilidad = par.split(':')
                                v = int(valor)
                                p = float(probabilidad)
                                valores.append(v)
                                propabilidades.append(p)
                            if abs(sum(propabilidades) - 1.0) > 1e-6:
                                print("La suma de probabilidades debe ser 1.0. Intente de nuevo.")
                                continue
                            self.variables[nombre] = ('disc', valores, propabilidades)
                            i += 1
                        except Exception:
                            print("Formato inválido; use valor:probabilidad separando pares con comas.")

                    else:
                        distribucion = input("Distribución [1: Uniforme, 2: Normal]: ").strip()
                        if distribucion not in ('1','2'):
                            print("Opción inválida; ingrese 1 o 2.")
                            continue

                        if distribucion == '1':
                            try:
                                lim_inferior = float(input("Límite inferior: "))
                                lim_superior = float(input("Límite superior: "))
                                if lim_inferior >= lim_superior:
                                    print("Límite inferior debe ser menor que el superior.")
                                    continue
                                self.variables[nombre] = ('unif', lim_inferior, lim_superior)
                                i += 1
                            except ValueError:
                                print("Parámetros inválidos; ingrese números.")

                        else:
                            try:
                                media = float(input("Media: "))
                                desv_est = float(input("Desviación estándar: "))
                                if desv_est <= 0:
                                    print("La desviación debe de ser positiva.")
                                    continue
                                acotar = input("¿Desea acotar la distribución? (s/n): ").strip().lower()
                                if acotar == 's':
                                    lim_inferior = float(input("Límite inferior de muestreo: "))
                                    lim_superior = float(input("Límite superior de muestreo: "))
                                    if lim_inferior >= lim_superior:
                                        print("Límite inferior debe ser menor que el superior.")
                                        continue
                                else:
                                    lim_inferior, lim_superior = None, None
                                self.variables[nombre] = ('normal', media, desv_est, lim_inferior, lim_superior)
                                i += 1
                            except ValueError:
                                print("Parámetros inválidos; ingrese números.")

            print("\nDefina la fórmula del modelo usando los nombres de variables.")
            print("Ejemplo: '(x + y) * z' si tiene x, y, z definidas.")
            self.formula = input("Ingrese la fórmula: ").strip()
            if not self.formula:
                raise ValueError("Fórmula vacía.")

            print("\n\t[MODELO] Configuración completada.")
            print(f"Iteraciones: {self.iteraciones}")
            print("Variables:")
            for variable, especificacion in self.variables.items():
                print(f"\t- {variable}: {especificacion}")
            print(f"Fórmula: {self.formula}")

        except KeyboardInterrupt:
            print("\n\t[Modelo - ERROR] Ejecución interrumpida por el usuario.")
        except Exception as e:
            print(f"\n\t[Modelo - ERROR] {e}")

    def obtener_configuracion(self) -> dict:
        configuracion = {}
        configuracion['formula'] = self.formula
        constantes = []
        for nombre, valor in self.variables.items():
            const = {}
            if 'const' in valor:
                nom = nombre
                val = valor[1]
                const[nom] = val
                constantes.append(const)
        configuracion['constantes'] = constantes

        return configuracion
        
    def generar_escenario(self, rng: np.random.Generator) -> dict:
        escenario = {}
        for nombre, valor in self.variables.items():
            if 'disc' in valor:
                valores = valor[1]
                probabilidades = valor[2]
                v = rng.choice(a=valores, p=probabilidades)
                v = float(v)
                escenario[nombre] = v
            elif 'unif' in valor:
                lim_inferior = valor[1]
                lim_superior = valor[2]
                v = rng.uniform(lim_inferior, lim_superior)
                v = float(v)
                escenario[nombre] = v
            elif 'normal' in valor:
                media = valor[1]
                desv_est = valor[2]
                v = rng.normal(media, desv_est)
                if valor[3] is not None and valor[4] is not None:
                    lim_inferior = valor[3]
                    lim_superior = valor[4]
                    v = np.clip(v, lim_inferior, lim_superior)
                    v = float(v)
                escenario[nombre] = v
        
        return escenario