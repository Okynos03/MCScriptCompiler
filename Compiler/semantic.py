from static.series import *
from Compiler.ast_nodes import *

class Simbolo:
    def __init__(self, nombre, tipo, ambito, es_funcion=False, parametros=None, tipo_retorno=None, tipo_contenido=None):
        self.nombre = nombre
        self.tipo = tipo
        self.ambito = ambito
        self.es_funcion = es_funcion
        self.parametros = parametros or []
        self.tipo_retorno = tipo_retorno
        self.tipo_contenido = tipo_contenido
        #self.nodo = nodo tal vez usarlo, luego vemos


class Entorno:
    def __init__(self):
        self.ambitos = [{}]  # lista de diccionarios para representar los ámbitos
        self.historial = []  # aquí guardarás todos los símbolos para fases posteriores

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        self.ambitos.pop()

    def declarar(self, nombre, simbolo):
        self.ambitos[-1][nombre] = simbolo
        self.historial.append((len(self.ambitos) - 1, simbolo))  # Guarda el nivel y el símbolo

    def buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def existe_en_actual(self, nombre):
        return nombre in self.ambitos[-1]

    def imprimir_historial(self):
        s = "=== Historial completo de símbolos ===\n"
        for nivel, simbolo in self.historial:
            linea = f"Ámbito {nivel} | {simbolo.nombre}: tipo={simbolo.tipo}"
            if simbolo.es_funcion:
                linea += f", función=True, retorno={simbolo.tipo_retorno}, parámetros={simbolo.parametros}"
            s += linea + "\n"
        return s


class AnalizadorSemantico:
    def __init__(self):
        self.entorno = Entorno()
        self.funcion_actual = None
        self.errores = []

    def analizar(self, nodo):
        metodo = f"visitar_{type(nodo).__name__}"
        if(type(nodo).__name__ == "ExpresionCadena"):
            if(len(nodo.texto) == 3):
                metodo = f"visitar_ExpresionCaracter"
        elif(type(nodo).__name__[0:7] == 'Funcion'):
            metodo = f"visitar_ExpresionLlamadaFuncion"
        visitador = getattr(self, metodo, self.visitar_desconocido)
        return visitador(nodo)

    def visitar_desconocido(self, nodo):
        self.errores.append(f"[Error] Nodo no reconocido: {type(nodo).__name__}")

    def visitar_Programa(self, nodo):
        self.entorno.entrar_ambito()
        for sentencia in nodo.sentencias:
            self.analizar(sentencia)
        self.entorno.salir_ambito()

    # def visitar_DeclaracionFuncion(self, nodo):
    #     if self.entorno.existe_en_actual(nodo.nombre):
    #         self.errores.append(f"[Error] Función '{nodo.nombre}' ya declarada en este ámbito")
    #     tipo_retorno = self.inferir_tipo_retorno(nodo.cuerpo)
    #     simbolo = Simbolo(nodo.nombre, 'funcion', ambito='local', es_funcion=True, parametros=nodo.parametros, tipo_retorno=tipo_retorno)
    #     self.entorno.declarar(nodo.nombre, simbolo)
    #     self.entorno.entrar_ambito()
    #     for param in nodo.parametros:
    #         if self.entorno.existe_en_actual(param):
    #             self.errores.append(f"[Error] Parámetro '{param}' ya declarado en esta función")
    #         self.entorno.declarar(param, Simbolo(param, 'item', ambito='local'))
    #     self.funcion_actual = nodo.nombre
    #     # contiene_tp = False
    #     # for sentencia in nodo.cuerpo:
    #     #     self.analizar(sentencia)
    #     #     if isinstance(sentencia, SentenciaTP):
    #     #         contiene_tp = True
    #     # if not contiene_tp:
    #     #     self.errores.append(f"[Error] La función '{nodo.nombre}' no contiene una sentencia TELETRANSPORTAR")
    #     self.funcion_actual = None
    #     self.entorno.salir_ambito()

    def visitar_DeclaracionFuncion(self, nodo):
        if self.entorno.existe_en_actual(nodo.nombre):
            self.errores.append(f"[Error] Función '{nodo.nombre}' ya declarada en este ámbito")
        self.entorno.entrar_ambito()
        for param in nodo.parametros:
            if self.entorno.existe_en_actual(param):
                self.errores.append(f"[Error] Parámetro '{param}' ya declarado en esta función")
            self.entorno.declarar(param, Simbolo(param, 'item', ambito='local'))
        self.funcion_actual = nodo.nombre
        tipos_retorno = []
        for sentencia in nodo.cuerpo:
            self.analizar(sentencia)
            if isinstance(sentencia, SentenciaTP) and sentencia.destino:
                tipo_retorno = self.analizar(sentencia.destino)
                tipos_retorno.append(tipo_retorno)
        tipo_final = 'item'
        if tipos_retorno:
            tipo_final = tipos_retorno[0]
            for tipo in tipos_retorno:
                if not self.comparar_tipos(tipo_final, tipo):
                    self.errores.append( f"[Error] Inconsistencia en tipo de retorno en función '{nodo.nombre}': '{tipo_final}' ≠ '{tipo}'")
        self.entorno.salir_ambito()
        self.funcion_actual = None
        simbolo = Simbolo(nodo.nombre, 'funcion', ambito='local', es_funcion=True, parametros=nodo.parametros,tipo_retorno=tipo_final)
        self.entorno.declarar(nodo.nombre, simbolo)

    def visitar_SentenciaExpresion(self, nodo):
        self.analizar(nodo.expresion)

    def inferir_tipo_retorno(self, cuerpo):
        for s in cuerpo:
            if isinstance(s, SentenciaTP) and s.destino:
                return self.analizar(s.destino)
        return 'item' #esto no estoy seguro, tal vez no esta bien

    #ESTO HAY QUE CHECARLO MUCHOOO
    def verificar_retorno_consistente(self, cuerpo):
        tipos_retorno = []
        for sentencia in cuerpo:
            if isinstance(sentencia, SentenciaTP):
                if sentencia.destino:
                    tipo_expr = self.analizar(sentencia.destino)
                    tipos_retorno.append(tipo_expr)
            elif hasattr(sentencia, 'entonces') or hasattr(sentencia, 'sino'):
                tipos_si = self.verificar_retorno_consistente(sentencia.entonces)
                tipos_sino = self.verificar_retorno_consistente(sentencia.sino or [])
                tipos_retorno.extend(tipos_si + tipos_sino)

        return tipos_retorno

    def visitar_SentenciaDeclaracion(self, nodo):
        if self.entorno.existe_en_actual(nodo.nombre):
            self.errores.append(f"[Error] Variable '{nodo.nombre}' ya declarada en este ámbito")
        tipo = self.obtener_tipo_nombre(nodo.tipo)
        self.entorno.declarar(nodo.nombre, Simbolo(nodo.nombre, tipo, ambito='local'))
        if hasattr(nodo, 'valor') and nodo.valor:
            if isinstance(nodo.valor, ListaFactores):
                if tipo != 'cofre':
                    self.errores.append(f"[Error] Solo variables tipo cofre pueden inicializarse con una lista")
                self.analizar(nodo.valor)
            else:
                tipo_valor = self.analizar(nodo.valor)
                if not self.comparar_tipos(tipo, tipo_valor):
                    self.errores.append(
                        f"[Error] Tipo incompatible en asignación a '{nodo.nombre}': {tipo} = {tipo_valor}")

    def visitar_SentenciaAsignacion(self, nodo):
        simbolo = self.entorno.buscar(nodo.nombre)
        if simbolo is None:
            self.errores.append(f"[Error] Variable '{nodo.nombre}' no declarada")
        elif nodo.es_acceso:
            if simbolo.tipo != 'cofre':
                self.errores.append(f"[Error] Variable '{nodo.nombre}' no es un cofre, no puede indexarse")
            else:
                tipo_indice = self.analizar(nodo.indice)
                if tipo_indice != 'bloque':
                    self.errores.append(
                        f"[Error] El índice para acceder a '{nodo.nombre}' debe ser de tipo bloque, se recibió '{tipo_indice}'")
            self.analizar(nodo.valor)
        elif isinstance(nodo.valor, ListaFactores): #nuevo
            if simbolo.tipo != 'cofre':
                self.errores.append(f"[Error] Se intentó asignar una lista a '{nodo.nombre}' que no es tipo cofre")
            else:
                self.analizar(nodo.valor)
        else:
            tipo_valor = self.analizar(nodo.valor)
            if not self.comparar_tipos(simbolo.tipo, tipo_valor):
                self.errores.append(f"[Error] Tipo incompatible en asignación a '{nodo.nombre}': {simbolo.tipo} = {tipo_valor}")

    def visitar_SentenciaSi(self, nodo):
        tipo_cond = self.analizar(nodo.condicion)
        if tipo_cond != 'palanca':
            self.errores.append(f"[Error] Condición del SI debe ser de tipo palanca, se encontró '{tipo_cond}'")
        self.entorno.entrar_ambito()
        for s in nodo.entonces:
            self.analizar(s)
        self.entorno.salir_ambito()
        if nodo.sino:
            self.entorno.entrar_ambito()
            for s in nodo.sino:
                self.analizar(s)
            self.entorno.salir_ambito()

    def visitar_SentenciaMientras(self, nodo):
        tipo_cond = self.analizar(nodo.condicion)
        if tipo_cond != 'palanca':
            self.errores.append(f"[Error] Condición del MIENTRAS debe ser de tipo palanca, se encontró '{tipo_cond}'")
        self.entorno.entrar_ambito()
        for s in nodo.cuerpo:
            self.analizar(s)
        self.entorno.salir_ambito()

    def visitar_SentenciaPara(self, nodo):
        self.entorno.entrar_ambito()
        self.analizar(nodo.inicial)
        tipo_cond = self.analizar(nodo.condicion)
        if tipo_cond != 'palanca':
            self.errores.append(f"[Error] La condición en PARA debe ser de tipo palanca, se encontró '{tipo_cond}'")
        self.analizar(nodo.actualizacion)
        for s in nodo.cuerpo:
            self.analizar(s)
        self.entorno.salir_ambito()

    def visitar_ExpresionLiteral(self, nodo):
        if isinstance(nodo.valor, int):
            return 'bloque'
        elif isinstance(nodo.valor, float):
            return 'losa'
        elif isinstance(nodo.valor, str):
            if len(nodo.valor) == 1:
                return 'hoja'
            return 'libro'
        return 'item'

    def visitar_ExpresionBooleana(self, nodo):
        return 'palanca'

    def visitar_ExpresionIdentificador(self, nodo):
        simbolo = self.entorno.buscar(nodo.nombre)
        if simbolo is None:
            self.errores.append(f"[Error] Variable '{nodo.nombre}' no declarada")
            return 'item'
        return simbolo.tipo

    def visitar_ExpresionAccesoArreglo(self, nodo):
        simbolo = self.entorno.buscar(nodo.nombre)
        if simbolo is None:
            self.errores.append(f"[Error] Variable '{nodo.nombre}' no declarada")
            return 'item'
        if simbolo.tipo != 'cofre':
            self.errores.append(f"[Error] Variable '{nodo.nombre}' no es un cofre y se intenta indexar")
        tipo_indice = self.analizar(nodo.indice)
        if tipo_indice != 'bloque':
            self.errores.append(f"[Error] El índice en '{nodo.nombre}[exp]' debe ser de tipo bloque, se recibió '{tipo_indice}'")
        if isinstance(nodo.indice, ExpresionLiteral):
            if isinstance(nodo.indice.valor, int):
                if nodo.indice.valor < 0: #en realidad no sirve de nada jajajaja pq es una expresion unaria jajaja
                    self.errores.append(f"[Error] El índice en '{nodo.nombre}[{nodo.indice.valor}]' no puede ser negativo")
            else:
                self.errores.append(f"[Error] El índice debe ser entero, se recibió '{nodo.indice.valor}'")
        if hasattr(simbolo, 'tipo_contenido') and simbolo.tipo_contenido:
            return simbolo.tipo_contenido

        return 'item'

    def visitar_ExpresionLlamadaFuncion(self, nodo):
        try:
            simbolo = self.entorno.buscar(nodo.funcion)
            if simbolo is None or not simbolo.es_funcion:
                return self.verificar_funcion_nativa(nodo)
        except AttributeError:
            return self.verificar_funcion_nativa(nodo)
        if len(nodo.argumentos) != len(simbolo.parametros):
            self.errores.append(f"[Error] Número de argumentos inválido para función '{nodo.funcion}'")
        else:
            for arg, param in zip(nodo.argumentos, simbolo.parametros):
                tipo_arg = self.analizar(arg)
                tipo_param = self.entorno.buscar(param).tipo if self.entorno.buscar(param) else 'item'
                if not self.comparar_tipos(tipo_param, tipo_arg): #puede que sea al reves
                    self.errores.append(f"[Error] Tipo de argumento incompatible en llamada a '{nodo.funcion}': {tipo_arg} ≠ {tipo_param}")
        return simbolo.tipo_retorno or 'item'

    def verificar_funcion_nativa(self, nodo):
        nombre = type(nodo).__name__[7:].upper()
        if nombre == 'CHAT':
            return 'item' #no se que devolver aqui asi que el default
        if nombre == 'ANTORCHAR':
            args = [nodo.valor]
            tipo = self.analizar(args[0])
            if args and tipo != 'palanca':
                self.errores.append("[Error] ANTORCHAR espera una expresión de tipo palanca")
            return 'palanca'
        if nombre in ['CRAFTEAR', 'ROMPER', 'APILAR', 'REPARTIR', 'SOBRAR', 'ENCANTAR']:
            if not nodo.izq or not nodo.der:
                self.errores.append(f"[Error] {nombre} espera exactamente 2 argumentos")
            else:
                args = [nodo.izq, nodo.der]
                tipos = [self.analizar(args[0]), self.analizar(args[1])]
                for i, tipo in enumerate(tipos):
                    if tipo not in ['bloque', 'losa', 'item']:
                        self.errores.append(f"[Error] Argumento {i+1} de {nombre} debe ser tipo numérico")
                        return 'item'
                if nombre == 'SOBRAR' and 'losa' in tipos:
                    self.errores.append("[Error] SOBRAR no permite valores tipo losa (debe ser entero)")
                if nombre == 'REPARTIR':
                    if isinstance(args[1], ExpresionLiteral) and args[1].valor == 0:
                        self.errores.append("[Error] Segundo argumento de REPARTIR no puede ser cero")
                if 'item' in tipos:
                    return 'item'
                elif 'losa' in tipos:
                    return 'losa'
                else:
                    return 'bloque'
        self.errores.append(f"[Error] Función '{nodo.funcion}' no declarada")
        return 'item'

    def visitar_ExpresionBinaria(self, nodo):
        tipo_izq = self.analizar(nodo.izquierda)
        tipo_der = self.analizar(nodo.derecha)
        if nodo.operador in ['+', '-', '*', '/', '%']:
            if tipo_izq in ['bloque', 'losa', 'item'] and tipo_der in ['bloque', 'losa', 'item']:
                if nodo.operador in ['/', '%'] or 'losa' in [tipo_izq, tipo_der]:
                    return 'losa'
                if 'item' in [tipo_izq, tipo_der]:
                    return 'item'
                return 'bloque'
            else:
                self.errores.append(f"[Error] Operación aritmética inválida entre '{tipo_izq}' y '{tipo_der}'")
                return 'item'
        elif nodo.operador in ['==']:
            if self.comparar_tipos(tipo_izq, tipo_der):
                return 'palanca'
            else:
                self.errores.append(f"[Error] Comparación de igualdad inválida entre '{tipo_izq}' y '{tipo_der}'")
                return 'item'
        elif nodo.operador in ['<', '>', '<=', '>=']:
            if tipo_izq in ['bloque', 'losa'] and tipo_der in ['bloque', 'losa']:
                return 'palanca'
            else:
                self.errores.append(f"[Error] Comparación relacional inválida entre '{tipo_izq}' y '{tipo_der}'")
                return 'item'
        elif nodo.operador in ['y', 'o']:
            if tipo_izq == 'palanca' and tipo_der == 'palanca':
                return 'palanca'
            else:
                self.errores.append(f"[Error] Operación lógica inválida entre '{tipo_izq}' y '{tipo_der}'")
                return 'item'
        elif nodo.operador == '.':
            if tipo_izq in ['hoja', 'libro'] and tipo_der in ['hoja', 'libro']:
                return 'libro'
            else:
                self.errores.append(f"[Error] Operación lógica inválida entre '{tipo_izq}' y '{tipo_der}'")
                return 'item'
        return 'item'

    #EL NODO EN REALIDAD SI ACEPTA EXPRESIONES, PERO ESTO POR EL MOMENTO SOLO CONSIDERA -1 Y +1 NO MAS
    def visitar_ExpresionUnaria(self, nodo):
        tipo_op = self.analizar(nodo.expresion)
        if nodo.operador == '-':
            if tipo_op in ['bloque', 'losa', 'item']:
                return tipo_op
            else:
                self.errores.append(f"[Error] Operador '-' no válido para tipo '{tipo_op}'")
                return 'item'
        elif nodo.operador == '+':
            if tipo_op in ['bloque', 'losa', 'item']:
                return tipo_op
            else:
                self.errores.append(f"[Error] Operador '+' no válido para tipo '{tipo_op}'")
                return 'item'
        #POR SI LUEGO AGREGAMOS EL NO
        # elif nodo.operador == 'no':
        #     if tipo_op == 'palanca':
        #         return 'palanca'
        #     else:
        #         self.errores.append(f"[Error] Operador 'no' solo se puede usar con palanca, se recibió '{tipo_op}'")
        #         return 'item'
        else:
            self.errores.append(f"[Error] Operador unario desconocido: {nodo.operador}")
            return 'item'

    def visitar_ExpresionCadena(self, nodo):
        return 'libro'

    def visitar_ExpresionCaracter(self, nodo):
        return 'hoja'

    def visitar_SentenciaTP(self, nodo):
        if self.funcion_actual is None:
            self.errores.append(f"[Error] TELETRANSPORTAR sólo se permite dentro de funciones")
        if nodo.destino:
            self.analizar(nodo.destino)

    def visitar_ListaFactores(self, nodo):
        if hasattr(nodo, 'elementos'): # No se si esta bien esta verificacion jaja
            tipos = [self.analizar(factor) for factor in nodo.elementos]
            if not tipos:
                return 'cofre'
        else:
            return 'cofre'

        #Reglas los tipos deben ser consistentes, o se generaliza a item
        tipo_base = tipos[0]
        for t in tipos[1:]:
            if not self.comparar_tipos(tipo_base, t):
                tipo_base = 'item'
                break
        return 'cofre'

#tal vez agregar para strings?? al menos el ==
    def comparar_tipos(self, tipo_destino, tipo_origen):
        if tipo_destino == tipo_origen:
            return True
        if tipo_destino == 'libro' and (tipo_origen == 'libro' or tipo_origen == 'hoja'):
            return True
        if tipo_destino == 'losa' and (tipo_origen == 'losa' or tipo_origen == 'bloque'):
            return True
        if tipo_destino == 'losa' and tipo_origen == 'item':
            return False
        if tipo_destino == 'bloque' and (tipo_origen == 'losa' or tipo_origen == 'item'):
            return False
        if tipo_destino == 'cofre' and tipo_origen == 'item':
            return False
        if tipo_destino == 'funcion' or tipo_origen == 'funcion': #habria que revisarlo
            return False
        if tipo_destino == 'item' or tipo_origen == 'item':
            return True
        return False

    def obtener_tipo_nombre(self, token_type):
        tipos = {
            BLOQUE: 'bloque',
            LOSA: 'losa',
            PALANCA: 'palanca',
            LIBRO: 'libro',
            HOJA: 'hoja',
            COFRE: 'cofre',
            ITEM: 'item'
        }
        return tipos.get(token_type, 'item')
