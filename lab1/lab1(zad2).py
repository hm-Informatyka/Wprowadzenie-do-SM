import time
import math

class LCG:
    def __init__(self, seed=None):
        self.a = 16807
        self.c = 2147483647
        self.b = 0

        if seed is None:
            seed = int(time.time() * 1000) % self.c

        if seed == 0:
            seed = 1

        self.state = seed

    def random(self):
        self.state = (self.a * self.state + self.b) % self.c
        return self.state / self.c


def poisson_one(lmbda, gen):
    q = math.exp(-lmbda)
    s = 1.0
    x = -1

    while s > q:
        u = gen.random()
        s *= u
        x += 1

    return x

if __name__ == "__main__":
    gen1 = LCG(seed=123)
    gen2 = LCG()

    print("Z seed=123:", [gen1.random() for _ in range(5)])
    print("Bez seed:", [gen2.random() for _ in range(5)])

    lmbda = 5.0
    print("Poisson (seed=123):", [poisson_one(lmbda, gen1) for _ in range(10)])
    print("Poisson (no seed):", [poisson_one(lmbda, gen2) for _ in range(10)])

input("Press Enter to leave")
