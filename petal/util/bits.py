"""Bits: Module to convert raw bytes into Unicode Braille for data presentation.

Originally written under GPLv3, relicensed as MIT for Petal by author.
"""

from itertools import zip_longest
from typing import Iterable, TypeVar


T = TypeVar("T")

# Braille Characters. The Index of each Character is also its Integer Value.
# NOTE: This is NOT the order the Characters appear in Unicode. Due to legacy
#   concerns, the bit pattern was made irregular when the fourth row was added.
#   This order is modified to better represent bytes visually.
braille = (
    "⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⡂⡃⡄⡅⡆⡇"  # [00] - 0F
    "⠈⠉⠊⠋⠌⠍⠎⠏⡈⡉⡊⡋⡌⡍⡎⡏"  #  10  - 1F
    "⠐⠑⠒⠓⠔⠕⠖⠗⡐⡑⡒⡓⡔⡕⡖⡗"  #  20  - 2F
    "⠘⠙⠚⠛⠜⠝⠞⠟⡘⡙⡚⡛⡜⡝⡞⡟"  #  30  - 3F
    "⠠⠡⠢⠣⠤⠥⠦⠧⡠⡡⡢⡣⡤⡥⡦⡧"  #  40  - 4F
    "⠨⠩⠪⠫⠬⠭⠮⠯⡨⡩⡪⡫⡬⡭⡮⡯"  #  50  - 5F
    "⠰⠱⠲⠳⠴⠵⠶⠷⡰⡱⡲⡳⡴⡵⡶⡷"  #  60  - 6F
    "⠸⠹⠺⠻⠼⠽⠾⠿⡸⡹⡺⡻⡼⡽⡾⡿"  #  70  - 7F (127)
    "⢀⢁⢂⢃⢄⢅⢆⢇⣀⣁⣂⣃⣄⣅⣆⣇"  #  80  - 8F
    "⢈⢉⢊⢋⢌⢍⢎⢏⣈⣉⣊⣋⣌⣍⣎⣏"  #  90  - 9F
    "⢐⢑⢒⢓⢔⢕⢖⢗⣐⣑⣒⣓⣔⣕⣖⣗"  #  A0  - AF
    "⢘⢙⢚⢛⢜⢝⢞⢟⣘⣙⣚⣛⣜⣝⣞⣟"  #  B0  - BF
    "⢠⢡⢢⢣⢤⢥⢦⢧⣠⣡⣢⣣⣤⣥⣦⣧"  #  C0  - CF
    "⢨⢩⢪⢫⢬⢭⢮⢯⣨⣩⣪⣫⣬⣭⣮⣯"  #  D0  - DF
    "⢰⢱⢲⢳⢴⢵⢶⢷⣰⣱⣲⣳⣴⣵⣶⣷"  #  E0  - EF
    "⢸⢹⢺⢻⢼⢽⢾⢿⣸⣹⣺⣻⣼⣽⣾⣿"  #  F0  - FF (255)
)
# Visual map of the bits in a Braille Byte:
#    1    16
#    2    32
#    4    64
#    8   128

# Braille Characters, unmodified.
bpoints = "".join(map(chr, range(0x2800, 0x2900)))


def bytes_to_braille(b: bytes) -> str:
    return "".join(braille[ch] for ch in b)


def chunk(iterable: Iterable[T], n: int, fillvalue=None) -> Iterable[Iterable[T]]:
    """Collect data into fixed-length chunks or blocks.

    From the Itertools Recipes.
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
