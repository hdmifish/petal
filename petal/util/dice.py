"""Dice rolling module

Adapted from source of https://github.com/Davarice/PyDice by original author.
"""

import re
from secrets import randbelow


DicePattern = re.compile(r"(\d*d\d+([+]\d+)*)")


def randint(low: int, high: int) -> int:
    diff = high - low
    add = randbelow(diff + 1)
    return low + add


class DieRoll:
    def __init__(self, results: list, add_each=0, add_sum=0, src=None):
        self.res = results
        self.add_each = add_each
        self.add_sum = add_sum
        self.src = src

    @property
    def results(self):
        return [int(n) + self.add_each for n in self.res]

    @property
    def total(self):
        return sum(self.results) + self.add_sum


class Dice:
    def __init__(self, size, quantity=1, add_each=0, add_sum=0, low=1):
        self.low = low
        self.high = size
        self.quantity = quantity
        self.add_each = add_each
        self.add_sum = add_sum

    def roll(self):
        return DieRoll(
            results=[randint(self.low, self.high) for _ in range(self.quantity)],
            add_each=self.add_each,
            add_sum=self.add_sum,
            src=self,
        )

    @property
    def one(self):
        return (
            "d" + str(self.high) + (("+" + str(self.add_each)) if self.add_each else "")
        )

    def __str__(self):
        truth = [
            self.quantity,
            self.add_each,
            True,
            self.high,
            self.add_each,
            self.add_each,
            self.add_each,
            self.add_sum,
            self.add_sum,
        ]
        parts = [
            self.quantity,
            "(",
            "d",
            self.high,
            "+",
            self.add_each,
            ")",
            "+",
            self.add_sum,
        ]

        out = "".join([str(parts[i]) for i in range(len(parts)) if truth[i]])
        return out


def parse_dice(expr) -> (Dice, None):
    # Parse a "word" into a number of dice and maybe additions, and return one Dice object for them
    if not expr:
        return

    if expr.startswith("d"):
        expr = "1" + expr

    dice, *addends = expr.split("+")
    quantity, size = dice.split("d")

    addends = [int(n) for n in addends]
    quantity = int(quantity)
    size = int(size)

    return Dice(size, quantity, add_sum=sum(addends))


def get_die(istr) -> (Dice, None):
    if not DicePattern.fullmatch(istr.lower()):
        return None
    return parse_dice(istr)
