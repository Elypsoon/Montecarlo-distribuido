import json

class Modelo:
    def __init__(self):
        self.formula = None
        self.num_variables = 0
        self.variables = {}
        self.iteraciones = 0
        pass

    def configurar_modelo(self):
        try:
            self.iteraciones = int(input("Ingrese el número de iteraciones de la simulación: "))
            self.num_variables = int(input("Ingrese el número de variables del modelo: "))

            i = 1
            while i <= self.num_variables:
                print(f"\nVARIABLE {i} DE {self.num_variables}")
                
                nom = input("Ingrese el nombre de la variable: ").strip()
                if nom in self.variables:
                    print("El nombre ingresado ya existe. Intente con otro.")
                    continue
                
                tipo = input("Tipo de variable [1: Constante, 2: Variable]: ").strip()
                if tipo not in ('1','2'):
                    print("Opción inválida; ingrese 1 o 2.")
                    continue

                if tipo == '1':
                    try:
                        val = float(input(f"Ingrese el valor de la constante '{nom}': "))
                        self.variables[nom] = ('const', val)
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
                            probs = []
                            for par in pares:
                                valor, probabilidad = par.split(':')
                                v = float(valor)
                                p = float(probabilidad)
                                valores.append(v)
                                probs.append(p)
                            if abs(sum(probs) - 1.0) > 1e-6:
                                print("La suma de probabilidades debe ser 1.0. Intente de nuevo.")
                                continue
                            self.variables[nom] = ('disc', valores, probs)
                            i += 1
                        except Exception:
                            print("Formato inválido; use valor:probabilidad separando pares con comas.")

                    else:
                        dist = input("Distribución [1: Uniforme, 2: Normal]: ").strip()
                        if dist not in ('1','2'):
                            print("Opción inválida; ingrese 1 o 2.")
                            continue

                        if dist == '1':
                            try:
                                lim_inferior = float(input("Límite inferior: "))
                                lim_superior = float(input("Límite superior: "))
                                if lim_inferior >= lim_superior:
                                    print("Límite inferior debe ser menor que el superior.")
                                    continue
                                self.variables[nom] = ('unif', lim_inferior, lim_superior)
                                i += 1
                            except ValueError:
                                print("Parámetros inválidos; ingrese números.")

                        else:
                            try:
                                media = float(input("Media (mu): "))
                                desv_est = float(input("Desviación estándar (sigma): "))
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
                                self.variables[nom] = ('normal', media, desv_est, lim_inferior, lim_superior)
                                i += 1
                            except ValueError:
                                print("Parámetros inválidos; ingrese números.")

            print("\nDefina la fórmula del modelo usando los nombres de variables.")
            print("Ejemplo: '(x + y) * z' si tiene x, y, z definidas.")
            self.formula = input("Ingrese la fórmula: ").strip()
            if not self.formula:
                raise ValueError("Fórmula vacía.")

            print("\n [MODELO] Configuración completada.")
            print(f"Iteraciones: {self.iteraciones}")
            print("Variables:")
            for var, especificacion in self.variables.items():
                print(f"\t- {var}: {especificacion}")
            print(f"Fórmula: {self.formula}")

        except KeyboardInterrupt:
            print("\n [Modelo - ERROR]: Ejecución interrumpida por el usuario.")
        except Exception as e:
            print(f"\n [Modelo - ERROR]: {e}")

    def obtener_configuracion(self):
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

        return json.dumps(configuracion, indent=4)
        
    def generar_escenarios(self):

        pass