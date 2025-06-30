class Error:
    def __init__(self, type, value, row, column):
        self.type = type
        self.value = value
        self.row = row
        self.column = column