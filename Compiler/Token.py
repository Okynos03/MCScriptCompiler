class Token:
    def __init__(self, type, value, row, column, index, length):
        self.type = type
        self.value = value
        self.row = row
        self.column = column
        self.index = index
        self.length = length
        self.pool_id = None

    def set_pool_id(self, pool_id):
        self.pool_id = pool_id