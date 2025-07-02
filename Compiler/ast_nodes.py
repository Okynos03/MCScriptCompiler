class Nodo:
    pass

class Programa(Nodo):
    def __init__(self, sentencias):
        self.sentencias = sentencias


#SENTENCIAS
class SentenciaVacia(Nodo):
    pass

class SentenciaDeclaracion(Nodo):
    def __init__(self, tipo, nombre, valor=None):
        self.tipo = tipo
        self.nombre = nombre
        self.valor = valor  # puede ser None

class SentenciaAsignacion(Nodo):
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

class SentenciaExpresion(Nodo):
    def __init__(self, expresion):
        self.expresion = expresion

class SentenciaTP(Nodo):
    def __init__(self, destino=None):
        self.destino = destino  # puede ser None (vacía)

class SentenciaSi(Nodo):
    def __init__(self, condicion, entonces, sino=None):
        self.condicion = condicion
        self.entonces = entonces  # lista de sentencias
        self.sino = sino  # lista de sentencias o None

class SentenciaMientras(Nodo):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo

class SentenciaPara(Nodo):
    def __init__(self, inicial, condicion, actualizacion, cuerpo):
        self.inicial = inicial
        self.condicion = condicion
        self.actualizacion = actualizacion
        self.cuerpo = cuerpo

class DeclaracionFuncion(Nodo):
    def __init__(self, nombre, parametros, cuerpo):
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo


#EXPRESIONES
class ExpresionBinaria(Nodo):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

class ExpresionLiteral(Nodo):
    def __init__(self, valor):
        self.valor = valor

class ExpresionIdentificador(Nodo):
    def __init__(self, nombre):
        self.nombre = nombre

class ExpresionAccesoArreglo(Nodo):
    def __init__(self, nombre, indice):
        self.nombre = nombre
        self.indice = indice

class ExpresionLlamadaFuncion(Nodo):
    def __init__(self, funcion, argumentos):
        self.funcion = funcion
        self.argumentos = argumentos

class ExpresionBooleana(Nodo):
    def __init__(self, valor):  # ENCENDIDO o APAGADO
        self.valor = valor

class ExpresionCadena(Nodo):
    def __init__(self, texto, concatenaciones=None):
        self.texto = texto
        self.concatenaciones = concatenaciones or []

class ExpresionUnaria:
    def __init__(self, operador, expresion):
        self.operador = operador
        self.expresion = expresion


#FUNCIONES ESPECIALES
class FuncionAntorchar(Nodo):
    def __init__(self, valor):
        self.valor = valor

class FuncionCraftear(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionRomper(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionApilar(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionRepartir(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionSobrar(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionEncantar(Nodo):
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

class FuncionChat(Nodo):
    def __init__(self, mensaje):
        self.mensaje = mensaje
