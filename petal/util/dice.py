"""Dice rolling module

Adapted from source of https://github.com/Davarice/PyDice by original author.
"""

from re import compile
from secrets import randbelow
from typing import Optional, Tuple


dice_pattern = compile(r"(\d*d\d+([-+]\d+)*)")
die_modifier = compile(r"[-+]\d+")


def randint(low: int, high: int) -> int:
    diff = high - low
    add = randbelow(diff + 1)
    return low + add


class DieRoll:
    """Represents the outcome of a set of Dice being rolled."""

    def __init__(
        self, results: Tuple[int], add_each: int = 0, add_sum: int = 0, src=None
    ):
        self.res = results
        self.add_each = add_each
        self.add_sum = add_sum
        self.src = src

    @property
    def results(self) -> Tuple[int, ...]:
        return tuple(int(n) + self.add_each for n in self.res)

    @property
    def total(self) -> int:
        return sum(self.results) + self.add_sum


class Dice:
    def __init__(
        self,
        size: int,
        quantity: int = 1,
        add_each: int = 0,
        add_sum: int = 0,
        low: int = 1,
    ):
        self.low: int = low
        self.high: int = size
        self.quantity: int = quantity
        self.add_each: int = add_each
        self.add_sum: int = add_sum

        truth = (
            (self.quantity, self.quantity),
            (self.add_each, "("),
            (True, "d"),
            (self.high, self.high),
            ((self.add_each > 0), "+"),
            (self.add_each, self.add_each),
            (self.add_each, ")"),
            ((self.add_sum > 0), "+"),
            (self.add_sum, self.add_sum),
        )
        self._str: str = "".join(str(part) for relevant, part in truth if relevant)

    def roll(self) -> DieRoll:
        return DieRoll(
            results=tuple(randint(self.low, self.high) for _ in range(self.quantity)),
            add_each=self.add_each,
            add_sum=self.add_sum,
            src=self,
        )

    @property
    def one(self) -> str:
        return (
            "d"
            + str(self.high)
            + (
                (("+" if self.add_each > 0 else "") + str(self.add_each))
                if self.add_each
                else ""
            )
        )

    def __str__(self) -> str:
        return self._str


def get_dice(expr: str) -> Optional[Dice]:
    """Parse a "word" into a number of dice and maybe additions, and return one
        Dice Object for them.
    """
    if dice_pattern.fullmatch(expr.lower()):
        if expr.startswith("d"):
            expr = "1" + expr

        addends: Tuple[int, ...] = tuple(
            int(mod.strip("+")) for mod in die_modifier.findall(expr) if mod
        )
        dice = die_modifier.sub("", expr)
        quantity, size = map(int, dice.split("d"))

        return Dice(size, quantity, add_sum=sum(addends))
