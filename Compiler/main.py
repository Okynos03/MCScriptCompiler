from Compiler.excel import Excel
from Compiler.textfile import TextFile
from Compiler.algorithm import Automaton
from Compiler.parser import BacktrackingParser

def init_automata():
    excel = Excel()
    excel.open('./static/MatrizTransicion.xlsx')

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

def main(automata, code):
    # excel = Excel()
    # resultsfile=TextFile()
    #
    # resultsfile.clear('./Results/Tokens.txt')
    # resultsfile.clear('./Results/Lists.txt')
    #
    # excel.open('./static/MatrizTransicion.xlsx')
    #
    # excel_data = excel.read()
    #
    # matrix = [i[1:] for i in excel_data[1:]]
    # sigma = excel_data[0][1:]
    # Q = [i[0] for i in excel_data[1:]]
    # q0 = Q[0]
    # F = [998, 999]
    # for row in matrix:
    #     for i in row:
    #         if i and i not in F and i > 999:
    #             F.append(i)
    #
    # automaton = Automaton(matrix, sigma, Q, q0, F)
    resultsfile = TextFile()
    resultsfile.clear('./Results/Tokens.txt')
    resultsfile.clear('./Results/Lists.txt')

    tokens, identifiers, strings, errors = automata.run(code)

    if not tokens:
        print("El archivo no arrojo resultado, favor de revisar")
    else:
        print("Done")
        resultsfile.write(tokens)
        resultsfile.write_symbol_data(identifiers, strings)
        if errors:
            resultsfile.write_errors(errors)
            print("Hubo errores lexicos")

    return tokens, errors
    # while True:
    #     if excel.open():
    #         break
    #     print("Porfa selecciona el archivo de la gramatica excel")
    # excel_data = excel.read_asymmetrical()
    #
    #
    #
    # tokens = normalize_indent_tokens(result)
    # grammar = {}
    # for rule in excel_data:
    #     head = rule[0]
    #     bodies = rule[1:]
    #     if head not in grammar:
    #         grammar[head] = []
    #     for body in bodies:
    #         if isinstance(body, str):
    #             body = body.strip()
    #             if body == 'E':
    #                 grammar[head].append([])
    #             else:
    #                 symbols = body.split()
    #                 grammar[head].append(symbols)
    #         else:
    #             grammar[head].append([str(body)])
    #
    # print(grammar)
    # print(tokens)
    # parser = BacktrackingParser(tokens, grammar, '<p>')
    # print(parser.run())

if __name__ == "__main__":
    main()