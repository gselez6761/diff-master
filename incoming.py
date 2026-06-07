class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name, qty):
        self.items[name] = self.items.get(name, 0) + qty

    def remove(self, name, qty):
        current = self.items.get(name, 0)
        if current < qty:
            raise ValueError(f"not enough {name}: have {current}, need {qty}")
        self.items[name] = current - qty

    def report(self):
        for name, qty in sorted(self.items.items()):
            print(f"{name}: {qty}")
