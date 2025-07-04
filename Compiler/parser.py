from Compiler.ast_nodes import *
from Compiler.Token import Token
from static.series import *
from Compiler.Errors import *

class DummyToken:
    def __init__(self):
        self.type = EOF
        self.value = 'EOF'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.sync_tokens = [SEMICOLON, RBRACE]
        self.errors = []

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        else:
            return Token(EOF, '', -1, -1, -1, -1)

    def match(self, expected_type, soft = False):
        if self.current().type == expected_type:
            self.pos += 1
        elif self.current().type == EOF:
            self.error(f"Se esperaba {expected_type}, pero se alcanzó EOF.")
            raise Exception("Fin del archivo inesperado")
        else:
            if soft:
                return
            self.error(f"Se esperaba tipo {expected_type}, se encontró {self.current().type}")

    def error(self, mensaje):
        #print(f"[Error] {mensaje} en token {self.current().type} (posición {self.pos})")
        self.errors.append(Error("Syntax", f"[Error] {mensaje} en token {self.current().type} (posición {self.pos})", -1, -1, self.pos, -1))
        self.panic()

    def panic(self):
        if self.current().type == EOF:
            return
        while self.current().type not in self.sync_tokens and self.current().type != EOF:
            self.pos += 1
        if self.current().type in self.sync_tokens and self.current().type != RBRACE:
            self.pos += 1

    def parse(self):
        try:
            if self.current().type == SPAWNEAR:
                self.match(SPAWNEAR)
                self.match(LBRACE)
                sentencias = self.lista_sentencias()
                self.match(RBRACE)
                self.match(MORIR)
                self.match(SEMICOLON)
                return Programa(sentencias)
            else:
                self.error("Se esperaba SPAWNEAR al inicio del programa")
                return Programa([])
        except Exception as e:
            #print(f"[Fatal] {e}")
            self.errors.append(Error("Syntax", f"[Fatal] {e}", -1, -1, self.pos, -1))
            return Programa([])

    def lista_sentencias(self):
        sentencias = []
        while self.current().type not in [RBRACE, EOF]:
            s = self.sentencia()
            if s:
                sentencias.append(s)
        return sentencias

    def sentencia(self):
        tipo = self.current().type
        if tipo == PORTAL:
            return self.declaracion_funcion()
        elif tipo in [BLOQUE, LOSA, PALANCA, LIBRO, HOJA, COFRE, ITEM]:
            return self.sentencia_declaracion()
        elif tipo == ID:
            pos_inicial = self.pos
            try:
                return self.sentencia_asignacion()
            except Exception:
                self.pos = pos_inicial
                expr = self.expresion()
                self.match(SEMICOLON)
                return SentenciaExpresion(expr)
        elif tipo == SI:
            return self.sentencia_si()
        elif tipo == MIENTRAS:
            return self.sentencia_mientras()
        elif tipo == PARA:
            return self.sentencia_para()
        elif tipo == TELETRANSPORTAR:
            return self.sentencia_tp()
        elif tipo == SEMICOLON:
            self.match(SEMICOLON)
            return SentenciaVacia()
        else:
            expr = self.expresion()
            self.match(SEMICOLON)
            return SentenciaExpresion(expr)

    def declaracion_funcion(self):
        self.match(PORTAL)
        nombre = self.current().value
        self.match(ID)
        self.match(LPAREN)
        parametros = self.parametros()
        self.match(RPAREN)
        self.match(LBRACE)
        cuerpo = self.lista_sentencias()
        self.match(RBRACE)
        return DeclaracionFuncion(nombre, parametros, cuerpo)

    def parametros(self):
        params = []
        if self.current().type == ID:
            params.append(self.current().value)
            self.match(ID)
            while self.current().type == COMMA:
                self.match(COMMA)
                params.append(self.current().value)
                self.match(ID)
        return params

    def sentencia_declaracion(self):
        tipo = self.current().type
        self.match(tipo)
        nombre = self.current().value
        self.match(ID)
        if self.current().type == ASSIGN:
            self.match(ASSIGN)
            if self.current().type == LSQB:
                self.match(LSQB)
                lista = self.lista_factores()
                self.match(RSQB)
                self.match(SEMICOLON)
                return SentenciaDeclaracion(tipo, nombre, lista, es_lista=True)
            else:
                valor = self.expresion()
                self.match(SEMICOLON)
                return SentenciaDeclaracion(tipo, nombre, valor, es_lista=False)
        else:
            self.match(SEMICOLON)
            return SentenciaDeclaracion(tipo, nombre, valor=None, es_lista=False)

    def sentencia_asignacion(self):
        nombre = self.current().value
        self.match(ID)
        if self.current().type != ASSIGN:
            self.match(ASSIGN, True)
            if self.current().type == LSQB:
                self.match(LSQB)
                indice = self.expresion()
                self.match(RSQB)
                self.match(ASSIGN)
                valor = self.expresion()
                self.match(SEMICOLON)
                return SentenciaAsignacion(nombre, valor, indice=indice, es_acceso=True)
            raise Exception
        self.match(ASSIGN)
        if self.current().type == LSQB:  # [
            self.match(LSQB)
            lista = self.lista_factores()
            self.match(RSQB)
            self.match(SEMICOLON)
            return SentenciaAsignacion(nombre, lista, es_lista=True)
        else:
            valor = self.expresion()
            self.match(SEMICOLON)
            return SentenciaAsignacion(nombre, valor, es_lista=False)

    def sentencia_tp(self):
        self.match(TELETRANSPORTAR)
        if self.current().type != SEMICOLON:
            destino = self.expresion()
        else:
            destino = None
        self.match(SEMICOLON)
        return SentenciaTP(destino)

    def sentencia_si(self):
        self.match(SI)
        self.match(LPAREN)
        cond = self.expresion()
        self.match(RPAREN)
        self.match(LBRACE)
        entonces = self.lista_sentencias()
        self.match(RBRACE)
        if self.current().type == SINO:
            self.match(SINO)
            if self.current().type == LBRACE:
                self.match(LBRACE)
                sino = self.lista_sentencias()
                self.match(RBRACE)
            elif self.current().type == SI:
                sino = [self.sentencia_si()]  # como lista para mantener estructura
            else:
                self.error("Se esperaba '{' o 'si' después de 'sino'")
                sino = []
            return SentenciaSi(cond, entonces, sino)
        else:
            return SentenciaSi(cond, entonces)

    def sentencia_mientras(self):
        self.match(MIENTRAS)
        self.match(LPAREN)
        cond = self.expresion()
        self.match(RPAREN)
        self.match(LBRACE)
        cuerpo = self.lista_sentencias()
        self.match(RBRACE)
        return SentenciaMientras(cond, cuerpo)

    def sentencia_para(self):
        self.match(PARA)
        self.match(LPAREN)
        inicial = self.sentencia_asignacion()
        cond = self.expresion()
        self.match(SEMICOLON)
        actualizacion = self.expresion()
        self.match(RPAREN)
        self.match(LBRACE)
        cuerpo = self.lista_sentencias()
        self.match(RBRACE)
        return SentenciaPara(inicial, cond, actualizacion, cuerpo)

    def expresion(self):
        return self.expresion_logica()

    def expresion_logica(self):
        izquierda = self.expresion_igualdad()
        while self.current().type in [AND, OR]:
            op = self.current().value
            self.match(self.current().type)
            derecha = self.expresion_igualdad()
            izquierda = ExpresionBinaria(izquierda, op, derecha)
        return izquierda

    def expresion_igualdad(self):
        izquierda = self.expresion_relacional()
        while self.current().type == EQUAL:
            op = self.current().value
            self.match(EQUAL)
            derecha = self.expresion_relacional()
            izquierda = ExpresionBinaria(izquierda, op, derecha)
        return izquierda

    def expresion_relacional(self):
        izquierda = self.expresion_aritmetica()
        while self.current().type in [LE, LOE, GE, GOE]:
            op = self.current().value
            self.match(self.current().type)
            derecha = self.expresion_aritmetica()
            izquierda = ExpresionBinaria(izquierda, op, derecha)
        return izquierda

    def expresion_aritmetica(self):
        izquierda = self.termino()
        while self.current().type in [PLUS, MINUS]:
            op = self.current().value
            self.match(self.current().type)
            derecha = self.termino()
            izquierda = ExpresionBinaria(izquierda, op, derecha)
        return izquierda

    def termino(self):
        izquierda = self.factor()
        while self.current().type in [MUL, DIV, MOD]:
            op = self.current().value
            self.match(self.current().type)
            derecha = self.factor()
            izquierda = ExpresionBinaria(izquierda, op, derecha)
        return izquierda

    def factor(self):
        tipo = self.current().type
        valor = self.current().value
        if tipo in [PLUS, MINUS]:
            op = valor
            self.match(tipo)
            expr = self.factor()
            return ExpresionUnaria(op, expr)
        elif tipo == LPAREN:
            self.match(LPAREN)
            expr = self.expresion()
            self.match(RPAREN)
            return expr
        elif tipo == ID:
            nombre = valor
            self.match(ID)
            if self.current().type == LPAREN:
                self.match(LPAREN)
                args = self.argumentos()
                self.match(RPAREN)
                return ExpresionLlamadaFuncion(nombre, args)
            elif self.current().type == LSQB:
                self.match(LSQB)
                indice = self.expresion()
                self.match(RSQB)
                return ExpresionAccesoArreglo(nombre, indice)
            else:
                return ExpresionIdentificador(nombre)
        elif tipo in [INT, FLOAT]:
            self.match(tipo)
            if tipo == INT:
                return ExpresionLiteral(int(valor)) # hice mod aqui a ver si jala
            else:
                return ExpresionLiteral(float(valor))
        elif tipo in [ENCENDIDO, APAGADO]:
            self.match(tipo)
            return ExpresionBooleana(valor)
        elif tipo == QUOTE:
            return self.cadena_texto()
        elif tipo in [ANTORCHAR, CRAFTEAR, ROMPER, APILAR, REPARTIR, SOBRAR, ENCANTAR, CHAT]:
            return self.funcion_especial()
        elif tipo == LSQB:
            self.match(LSQB)
            factores = self.lista_factores()
            self.match(RSQB)
            return ListaFactores(factores)
        else:
            self.error("Factor inválido")
            return ExpresionLiteral(0)

    def argumentos(self):
        args = []
        if self.current().type not in [RPAREN]:
            args.append(self.expresion())
            while self.current().type == COMMA:
                self.match(COMMA)
                args.append(self.expresion())
        return args

    def funcion_especial(self):
        tipo = self.current().type
        self.match(tipo)
        self.match(LPAREN)
        if tipo == CHAT:
            arg = self.expresion()
            self.match(RPAREN)
            return FuncionChat(arg)
        elif tipo == ANTORCHAR:
            arg = self.expresion()
            self.match(RPAREN)
            return FuncionAntorchar(arg)
        else:
            izq = self.expresion()
            self.match(COMMA)
            der = self.expresion()
            self.match(RPAREN)
            cls_map = {
                CRAFTEAR: FuncionCraftear,
                ROMPER: FuncionRomper,
                APILAR: FuncionApilar,
                REPARTIR: FuncionRepartir,
                SOBRAR: FuncionSobrar,
                ENCANTAR: FuncionEncantar
            }
            return cls_map[tipo](izq, der)

    def cadena_texto(self):
        texto = self.current().value
        self.match(QUOTE)
        concatenaciones = []
        while self.current().type == DOT:
            self.match(DOT)
            if self.current().type == QUOTE:
                concatenaciones.append(self.cadena_texto())
            else:
                concatenaciones.append(self.expresion())

        return ExpresionCadena(texto, concatenaciones)

    #esto se lo pedi a chat pq fue de ultimo jaja
    def lista_factores(self):
        factores = []
        primeros_tokens_factor = [
            PLUS, MINUS, LPAREN, ID, INT, FLOAT, ENCENDIDO, APAGADO, QUOTE,
            ANTORCHAR, CRAFTEAR, ROMPER, APILAR, REPARTIR, SOBRAR, ENCANTAR, CHAT, LSQB
        ]
        if self.current().type in primeros_tokens_factor:
            factores.append(self.factor())
            factores.extend(self.resto_factores())

        return ListaFactores(factores)

    #si mantenemos lista de factores
    def resto_factores(self):
        factores = []
        while self.current().type == COMMA:
            self.match(COMMA)
            factores.append(self.factor())
        return factores


