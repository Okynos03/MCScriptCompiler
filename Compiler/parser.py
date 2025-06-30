class BacktrackingParser:
    def __init__(self, tokens, grammar, start):
        self.tokens = [str(tok) for tok in tokens]
        self.grammar = grammar
        self.start = start
        self.pos = 0
        self.depth = 0  # for indentation

    def parse(self, symbol):
        indent = '  ' * self.depth
        print(f"{indent}Trying {symbol} at pos {self.pos}")

        if not symbol.startswith('<'):
            if self.pos < len(self.tokens) and self.tokens[self.pos] == symbol:
                print(f"{indent}Matched terminal {symbol}")
                self.pos += 1
                return True
            print(f"{indent}Failed terminal {symbol}")
            return False

        if symbol not in self.grammar:
            print(f"{indent}Unknown non-terminal {symbol}")
            return False

        for production in self.grammar[symbol]:
            old_pos = self.pos
            self.depth += 1
            print(f"{indent}Trying production {symbol} -> {production}")

            if production == []:
                print(f"{indent}ε-production for {symbol}")
                self.depth -= 1
                return True

            success = True
            for sym in production:
                if not self.parse(sym):
                    success = False
                    break

            self.depth -= 1

            if success:
                print(f"{indent}✓ Success: {symbol} -> {production}")
                return True

            print(f"{indent}✗ Backtrack {symbol} from {production}")
            self.pos = old_pos  # backtrack

        print(f"{indent} All productions failed for {symbol}")
        return False

    def run(self):
        result = self.parse(self.start)
        print("Final pos:", self.pos, "/", len(self.tokens))
        return result and self.pos == len(self.tokens)

