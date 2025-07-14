import re

from Compiler.Token import Token
from Compiler.Errors import Error

class Automaton:
    def __init__(self, matrix, sigma, Q, q0, F):
        self.Q = Q
        self.matrix = matrix
        self.sigma = sigma
        self.q0 = q0
        self.F = F
        #self.types = {6000: "identifier", 1000: "keyword", 3000: "punctuation", 2000: "operator", 4000: "curly brace", 5000: "bracket", 7000: "integer", 8000: "float"}

    def run(self, text):
        list = []
        errors = []
        i = 0
        column = 1
        row = 1
        while i < len(text):
            current = self.q0
            j = i
            accepted = False
            word = ""
            start_index = j
            aux = ""

            while j < len(text):
                symbol = text[j]

                if current == 160 and symbol != '"':
                    word += symbol
                    j += 1
                    column += 1
                    if symbol == "\n":
                        row += 1
                        column = 1
                    continue
                elif current == 164 and symbol != '\n':
                    j += 1
                    column += 1
                    continue

                if symbol == "\n":
                    symbol = "\\n"
                elif symbol == " ":
                    symbol = "\\s"
                elif re.match(r'\s', symbol):
                    j += 1
                    continue

                if symbol.isdigit():
                    symbol = int(symbol)

                if symbol not in self.sigma:
                    error = Error("Lexical", "Unrecognized character '%s'" %symbol, row, column, j, 1)
                    errors.append(error)
                    j += 1
                    column += 1
                    continue

                current = self.matrix[self.Q.index(current)][self.sigma.index(symbol)]

                if current in self.F:
                    accepted = True
                    aux = symbol
                    break

                j += 1
                column += 1
                word += str(symbol)

            i = j

            if accepted or j == len(text):
                if j == len(text):
                    current = self.matrix[self.Q.index(current)][self.sigma.index("\\n")]

                if current == 998:
                    error = Error("Lexical", "Invalid number literal '%s'" % (word + aux), row, column - len(word), start_index, i - start_index)
                    errors.append(error)
                    i += 1
                    continue
                elif current == 100000 or current == 9000 or current == 163:
                    if current == 9000:
                        row += 1
                        column = 1
                    continue

                if current not in self.F:
                    continue
                token = Token(current, word, row, column - len(word), start_index, i - start_index)
                list.append(token)

        list.append(Token(1, 'EOF', -1, -1, -1, -1))
        return list, errors




