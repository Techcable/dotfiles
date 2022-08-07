from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Union

ALLOW_OVER_100 = False

GradeLike = Union["Grade", tuple[float, float]]
Grades = Union[GradeLike, Iterable[GradeLike]]


@dataclass
class Grade:
    points: float
    maximum: float

    def __post_init__(self):
        assert self.points >= 0
        assert self.maximum >= 0
        if self.points > self.maximum:
            global ALLOW_OVER_100
            if not ALLOW_OVER_100:
                raise ValueError("Bad grade: {self.points}/{self.maximum}")

    @property
    def letter(self) -> str:
        grd = float(self)
        if grd >= 0.9:
            return "A"
        elif grd >= 0.8:
            return "B"
        elif grd >= 0.7:
            return "C"
        elif grd >= 0.6:
            return "D"
        else:
            return "F"

    @property
    def approx(self) -> float:
        return float(self)

    def __float__(self):
        return self.points / self.maximum

    def __str__(self):
        return f"{self.points}/{self.maximum}"

    def __repr__(self):
        return f"Grade({self.points}, {self.maximum}, letter={self.letter}, approx={self.approx})"

    def __add__(self, other):
        if isinstance(other, Grade):
            return Grade(self.points + other.points, self.maximum + other.maximum)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return Grade(self.points * other, self.maximum * other)
        else:
            return NotImplemented

    @staticmethod
    def combine(g: Grades) -> Grade:
        if isinstance(g, Grade):
            return g
        elif isinstance(g, tuple):
            return Grade(*g)
        else:
            total = Grade(0, 0)
            for val in g:
                if isinstance(val, tuple):
                    val = Grade(*val)
                else:
                    assert isinstance(val, Grade), repr(val)
                total += val
            return total

    @staticmethod
    def weight(weights: dict[float, Grades]) -> Grade:
        total_weight = 0.0
        total = Grade(0, 0)
        assert math.isclose(sum(weights.keys()), 1.0)
        for w, grades in weights.items():
            assert w > 0 and w <= 1
            total += Grade.combine(grades) * w
            total_weight += w
        return total
