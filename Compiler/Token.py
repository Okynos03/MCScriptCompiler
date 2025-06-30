class Token:
    def __init__(self, type, value, row, column):
        self.type = type
        self.value = value
        self.row = row
        self.column = column
        self.pool_id = None

    def set_pool_id(self, pool_id):
        self.pool_id = pool_id