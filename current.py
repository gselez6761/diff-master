class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, qty):
        self.items[name] = self.items.get(name, 0) + qty

    def remove(self, name, qty):
        if self.items.get(name, 0) < qty:
            raise ValueError("not enough " + name)
        self.items[name] -= qty

    def restock(self, name, qty):
        # The AI loves to silently drop whole methods like this one.
        self.add(name, qty)
        return self.items[name]

    def report(self):
        for name, qty in self.items.items():
            print(name, qty)
