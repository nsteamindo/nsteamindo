class ColorLog:
    pref: str

    def __init__(self, pref: str):
        self.pref = pref

    def __str__(self):
        return self.pref

    def __repr__(self):
        return self.pref

    def __add__(self, other):
        return self.pref + other

    def __lshift__(self, other):
        print(self.pref, other)
