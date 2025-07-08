from Compiler.excel import Excel
from Compiler.textfile import TextFile
from Compiler.algorithm import Automaton
from Compiler.parser import Parser
from Compiler.pretty_print import pretty_print
from Compiler.semantic import AnalizadorSemantico
from Compiler.intermediate import GeneradorIntermedio
from Compiler.optimizer import OptimizadorCodigoIntermedio
from Compiler.backend import PythonCode

def init_automata():
    excel = Excel()
    excel.open('./static/MatrizTransicion_LA.xlsx')

    excel_data = excel.read()

    matrix = [i[1:] for i in excel_data[1:]]
    sigma = excel_data[0][1:]
    Q = [i[0] for i in excel_data[1:]]
    q0 = Q[0]
    F = [998, 999]
    for row in matrix:
        for i in row:
            if i and i not in F and i > 999:
                F.append(i)

    automaton = Automaton(matrix, sigma, Q, q0, F)
    return automaton

def lexical(automata, code):
    resultsfile = TextFile()
    resultsfile.clear('./Results/Tokens.txt')
    resultsfile.clear('./Results/Lists.txt')

    tokens, errors = automata.run(code)

    if not tokens:
        #print("El archivo no arrojo resultado, favor de revisar")
        pass
    else:
        #print("Done")
        #resultsfile.write(tokens)
        #resultsfile.write_symbol_data(identifiers, strings)
        if errors:
            pass
            #resultsfile.write_errors(errors)
            #print("Hubo errores lexicos")

    return tokens, errors

def syntax(tokens):
    parser = Parser(tokens)
    ast = parser.parse()
    string_ast = pretty_print(ast)

    return string_ast, parser.errors, ast

def semantic(ast, tokens):
    sem = AnalizadorSemantico(tokens)
    sem.visitar_Programa(ast)

    return sem.entorno.imprimir_historial(), sem.errores

def intermediate(ast):
    gen = GeneradorIntermedio()
    gen.generar(ast)

    return gen.instrucciones

def optimize(int_code):
    opt = OptimizadorCodigoIntermedio(int_code)
    opt.optimizar()

    return opt.codigo_intermedio

def trasnlation(int_code):
    exe = PythonCode(int_code)
    exe.translate()

    return exe