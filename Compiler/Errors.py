class Error:
    def __init__(self, type, value, row, column, index, length):
        self.type = type
        self.value = value
        self.row = row
        self.column = column
        self.index = index
        self.length = length