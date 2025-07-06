from static.series import *
from Compiler.semantic import Entorno, Simbolo

class GeneradorIntermedio:
    def __init__(self):
        self.instrucciones = []
        self.temp_id = 0
        self.entorno = Entorno()
        self.etiquetas_funciones = {}
        self.contador_etiquetas = 0
        self.offset_local_actual = 0

    def nueva_etiqueta(self, prefijo="L"):
        etiqueta = f"{prefijo}{self.contador_etiquetas}"
        self.contador_etiquetas += 1
        return etiqueta

    def nuevo_temp(self):
        temp = f"t{self.temp_id}"
        self.temp_id += 1
        return temp

    def emitir(self, instruccion):
        self.instrucciones.append(instruccion)

    def generar(self, nodo):
        metodo = f"generar_{type(nodo).__name__}"
        return getattr(self, metodo, self.generar_desconocido)(nodo)

    def generar_Programa(self, nodo):
        for sentencia in nodo.sentencias:
            self.generar(sentencia)

    def generar_desconocido(self, nodo):
        raise Exception(f"No se puede generar código para {type(nodo).__name__}")

    def generar_SentenciaVacia(self, nodo):
        pass

    def generar_SentenciaAsignacion(self, nodo):
        valor_temp = self.generar(nodo.valor)
        if nodo.es_acceso:
            indice = self.generar(nodo.indice)
            self.emitir(f"SET_LIST_ITEM {nodo.nombre}, {indice}, {valor_temp}")
        else:
            self.emitir(f"{nodo.nombre} = {valor_temp}")

    def generar_SentenciaDeclaracion(self, nodo):
        tipo = nodo.tipo if isinstance(nodo.tipo, str) else self.obtener_nombre_tipo(nodo.tipo)
        self.emitir(f"# Declaración de {tipo} {nodo.nombre}")
        if nodo.valor:
            valor_temp = self.generar(nodo.valor)
            self.emitir(f"{nodo.nombre} = {valor_temp}")
        else:
            pass

    def generar_SentenciaExpresion(self, nodo):
        self.generar(nodo.expresion) # estamos discardeando el resultado pq ps si

    def generar_DeclaracionFuncion(self, nodo):
        #self.entorno.entrar_ambito()
        self.offset_local_actual = 0
        etiqueta_funcion = f"FUNC_{nodo.nombre}"
        self.emitir(f"# ETIQUETA {etiqueta_funcion}:")
        self.etiquetas_funciones[nodo.nombre] = etiqueta_funcion
        for param in nodo.parametros:
            self.emitir(f"# PARAM_DECL {param} OFFSET {self.offset_local_actual}") #innecesario pq pues python
            self.offset_local_actual += 4 #solo si se usa ens supongo pero no se va a usar aca pq pues python :)
            #self.entorno.declarar(param, Simbolo(param, tipo='item', ambito='local'))
        for sentencia in nodo.cuerpo:
            self.generar(sentencia)
        # self.emitir(f"# ALLOC_LOCALS {self.offset_local_actual}") # si se usa pila dejar el espacio, epro no creo puro trad a python y ya
        self.emitir(f"# FIN_FUNC {nodo.nombre}")
        #self.entorno.salir_ambito()

    def generar_SentenciaTP(self, nodo):
        if nodo.destino:
            valor_a_retornar = self.generar(nodo.destino)
            self.emitir(f"RETURN {valor_a_retornar}")
        else:
            self.emitir("RETURN")

    def generar_SentenciaSi(self, nodo):
        resultado_condicion = self.generar(nodo.condicion)
        etiqueta_sino = self.nueva_etiqueta("ELSE")
        etiqueta_fin_si = self.nueva_etiqueta("ENDIF")

        if nodo.sino:
            self.emitir(f"GOTO_IF_FALSE {resultado_condicion}, {etiqueta_sino}")
        else:
            self.emitir(f"GOTO_IF_FALSE {resultado_condicion}, {etiqueta_fin_si}")

        for sentencia_entonces in nodo.entonces:
            self.generar(sentencia_entonces)

        if nodo.sino:
            self.emitir(f"GOTO {etiqueta_fin_si}")
            self.emitir(f"# ETIQUETA {etiqueta_sino}:")
            for sentencia_sino in nodo.sino:
                self.generar(sentencia_sino)

        self.emitir(f"# ETIQUETA {etiqueta_fin_si}:")

    def generar_SentenciaMientras(self, nodo):
        etiqueta_inicio_bucle = self.nueva_etiqueta("WHILE_START")
        etiqueta_fin_bucle = self.nueva_etiqueta("WHILE_END")
        self.emitir(f"# ETIQUETA {etiqueta_inicio_bucle}:")
        resultado_condicion = self.generar(nodo.condicion)
        self.emitir(f"GOTO_IF_FALSE {resultado_condicion}, {etiqueta_fin_bucle}")

        for sentencia_cuerpo in nodo.cuerpo:
            self.generar(sentencia_cuerpo)

        self.emitir(f"GOTO {etiqueta_inicio_bucle}")
        self.emitir(f"ETIQUETA {etiqueta_fin_bucle}:")

    #pendiente
    def generar_SentenciaPara(self):
        pass

    def generar_ExpresionBinaria(self, nodo):
        izq = self.generar(nodo.izquierda)
        der = self.generar(nodo.derecha)
        temp = self.nuevo_temp()
        self.emitir(f"{temp} = {izq} {nodo.operador if nodo.operador != "^" else "**"} {der}")
        return temp

    def generar_ExpresionLiteral(self, nodo):
        return nodo.valor

    def generar_ExpresionIdentificador(self, nodo):
        return nodo.nombre

    def generar_ExpresionLlamadaFuncion(self, nodo):
        etiqueta_entrada_funcion = self.etiquetas_funciones.get(nodo.funcion)
        if not etiqueta_entrada_funcion:
            raise Exception(f"Error interno del generador: Etiqueta de función '{nodo.funcion}' no encontrada.")#me recomendo poner esto gemini lol

        argumentos_generados = []
        for arg_node in nodo.argumentos:
            valor_arg = self.generar(arg_node)
            argumentos_generados.append(valor_arg)
            self.emitir(f"PUSH_PARAM {valor_arg}")

        self.emitir(f"CALL {etiqueta_entrada_funcion}")

        if nodo.recibe and nodo.recibe is not None:
            temp_retorno = self.nuevo_temp()
            self.emitir(f"{temp_retorno} = POP_RETVAL")
            return temp_retorno
        else:
            return None

    def generar_ExpresionBooleana(self, nodo):
        #return str( 1 if nodo.valor == "encendido" else 0)
        return nodo.valor

    def generar_ExpresionCadena(self, nodo):
        if nodo.concatenaciones:
            concat = str(nodo.texto)
            for cadena in nodo.concatenaciones:
                concat += self.generar(cadena)
            return str(nodo.texto) + concat
        return str(nodo.texto)

    def generar_ExpresionUnaria(self, nodo):
        operando_generado = self.generar(nodo.expresion)
        temp_resultado = self.nuevo_temp()

        if nodo.operador == '-':
            self.emitir(f"{temp_resultado} = NEG {operando_generado}")
        elif nodo.operador == '+': #pq supongo que nucna hace nada
            pass
        else:
            raise Exception(f"Operador unario desconocido: {nodo.operador}")

        return temp_resultado

    def generar_ExpresionAccesoArreglo(self, nodo):
        referencia_lista_ir = nodo.nombre
        indice_generado = self.generar(nodo.indice)
        temp_resultado = self.nuevo_temp()

        # GET_LIST_ITEM
        # Sintaxis: <temporal_resultado> = GET_LIST_ITEM <referencia_lista>, <indice>
        self.emitir(f"{temp_resultado} = GET_LIST_ITEM {referencia_lista_ir}, {indice_generado}")

        return temp_resultado

    def generar_FuncionAntorchar(self, nodo):
        valor_generado = self.generar(nodo.valor)
        self.emitir(f"NOT {valor_generado}")
        return None

    def generar_FuncionCraftear(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} + {der_generado}")
        return temp_resultado

    def generar_FuncionRomper(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} - {der_generado}")
        return temp_resultado

    def generar_FuncionApilar(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} * {der_generado}")
        return temp_resultado

    def generar_FuncionRepartir(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} / {der_generado}")
        return temp_resultado

    def generar_FuncionSobrar(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} % {der_generado}")
        return temp_resultado

    def generar_FuncionEncantar(self, nodo):
        izq_generado = self.generar(nodo.izq)
        der_generado = self.generar(nodo.der)
        temp_resultado = self.nuevo_temp()
        self.emitir(f"{temp_resultado} = {izq_generado} ** {der_generado}")
        return temp_resultado

    def generar_FuncionChat(self, nodo):
        mensaje_generado = self.generar(nodo.mensaje)
        self.emitir(f"PRINT {mensaje_generado}")
        return None

    def generar_ListaFactores(self, nodo):
        resultados_factores_ir = []
        for factor_nodo in nodo.factores:
            resultado_factor = self.generar(factor_nodo)
            resultados_factores_ir.append(resultado_factor)
        return resultados_factores_ir #la mando asi nada mas pq jajaja traducimos la lista a una de python y ya ajajaj

    def obtener_nombre_tipo(self, token_type):
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

    #no se va a usar creo era solo si se pasa a ens
    def _obtener_tamano_tipo(self, tipo):
        if tipo == "entero": return 4
        if tipo == "flotante": return 8
        if tipo == "booleano": return 1
        return 0
