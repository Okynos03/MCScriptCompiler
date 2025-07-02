from Compiler.ast_nodes import *


def pretty_print(node, indent=0):
    tab = '  ' * indent
    if node is None:
        return tab + 'None'
    if isinstance(node, list):
        return '\n'.join(pretty_print(n, indent) for n in node)

    if isinstance(node, Programa):
        return tab + "Programa:\n" + pretty_print(node.sentencias, indent + 1)

    elif isinstance(node, DeclaracionFuncion):
        s = f"{tab}Portal: {node.nombre}({', '.join(node.parametros)})\n"
        s += pretty_print(node.cuerpo, indent + 1)
        return s

    elif isinstance(node, SentenciaDeclaracion):
        s = f"{tab}Declaración: {node.tipo} {node.nombre}"
        if node.valor:
            s += " =\n" + pretty_print(node.valor, indent + 1)
        return s

    elif isinstance(node, SentenciaAsignacion):
        return f"{tab}Asignación: {node.nombre} =\n" + pretty_print(node.valor, indent + 1)

    elif isinstance(node, SentenciaTP):
        if node.destino:
            return f"{tab}Teletransportar:\n" + pretty_print(node.destino, indent + 1)
        else:
            return f"{tab}Teletransportar (vacío)"

    elif isinstance(node, SentenciaSi):
        s = f"{tab}Si:\n{tab}  Condición:\n" + pretty_print(node.condicion, indent + 2)
        s += f"\n{tab}  Entonces:\n" + pretty_print(node.entonces, indent + 2)
        if node.sino:
            s += f"\n{tab}  Sino:\n" + pretty_print(node.sino, indent + 2)
        return s

    elif isinstance(node, SentenciaMientras):
        s = f"{tab}Mientras:\n{tab}  Condición:\n" + pretty_print(node.condicion, indent + 2)
        s += f"\n{tab}  Cuerpo:\n" + pretty_print(node.cuerpo, indent + 2)
        return s

    elif isinstance(node, SentenciaPara):
        s = f"{tab}Para:\n{tab}  Inicialización:\n" + pretty_print(node.inicial, indent + 2)
        s += f"\n{tab}  Condición:\n" + pretty_print(node.condicion, indent + 2)
        s += f"\n{tab}  Actualización:\n" + pretty_print(node.actualizacion, indent + 2)
        s += f"\n{tab}  Cuerpo:\n" + pretty_print(node.cuerpo, indent + 2)
        return s

    elif isinstance(node, SentenciaExpresion):
        return f"{tab}Expresión:\n" + pretty_print(node.expresion, indent + 1)

    elif isinstance(node, SentenciaVacia):
        return f"{tab}Sentencia vacía"

    elif isinstance(node, ExpresionBinaria):
        s = f"{tab}Expresión binaria: {node.operador}\n"
        s += pretty_print(node.izquierda, indent + 1) + "\n"
        s += pretty_print(node.derecha, indent + 1)
        return s

    elif isinstance(node, ExpresionLiteral):
        return f"{tab}Literal: {node.valor}"

    elif isinstance(node, ExpresionIdentificador):
        return f"{tab}Identificador: {node.nombre}"

    elif isinstance(node, ExpresionAccesoArreglo):
        s = f"{tab}Acceso arreglo: {node.nombre}[ ]\n"
        s += pretty_print(node.indice, indent + 1)
        return s

    elif isinstance(node, ExpresionBooleana):
        return f"{tab}Booleano: {node.valor}"

    elif isinstance(node, ExpresionCadena):
        s = f"{tab}Cadena: {node.texto}"
        for extra in node.concatenaciones:
            s += "\n" + pretty_print(extra, indent + 1)
        return s

    elif isinstance(node, ExpresionUnaria):
        return f"{tab}Expresión unaria: {node.operador} {node.expresion}"

    elif isinstance(node, ExpresionLlamadaFuncion):
        s = f"{tab}Llamada función: {node.funcion}()\n"
        s += pretty_print(node.argumentos, indent + 1)
        return s

    elif isinstance(node, FuncionAntorchar):
        return f"{tab}Función especial: ANTORCHAR\n" + pretty_print(node.valor, indent + 1)

    elif isinstance(node, FuncionChat):
        return f"{tab}Función especial: CHAT\n" + pretty_print(node.mensaje, indent + 1)

    elif isinstance(node,
                    (FuncionCraftear, FuncionRomper, FuncionApilar, FuncionRepartir, FuncionSobrar, FuncionEncantar)):
        return f"{tab}Función especial: {type(node).__name__}\n{tab}  Izq: {node.izq}\n{tab}  Der: {node.der}"

    return tab + f"Desconocido: {type(node)}"
