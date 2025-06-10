"""A script to calculate your GPA"""

from __future__ import annotations

from decimal import Decimal
from enum import IntEnum

import click
import rich
from rich.console import Console


class Grade(IntEnum):
    A = 4
    B = 3
    C = 2
    D = 1
    F = 0

    @property
    def key(self) -> str:
        return self.name.lower()

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def parse(s: str) -> Grade:
        if s.isdigit():
            return Grade(int(s))
        else:
            return Grade[s]


def gpa(a: int, b: int, c: int = 0, d: int = 0, f: int = 0) -> Decimal:
    credits_by_grade: dict[Grade, int] = {Grade(4 - idx): val for idx, val in enumerate((a, b, c, d, f))}
    earned_points, total_hours = 0, 0
    for grade, hours in credits_by_grade.items():
        earned_points += hours * grade
        total_hours += hours
    assert total_hours == sum(credits_by_grade.values())
    assert earned_points <= total_hours * 4
    return Decimal(earned_points) / total_hours


def prompt_credits(grade: Grade) -> int:
    while True:
        res = click.prompt(f"How many credits were {grade}?", type=int)
        assert res >= 0
        return res


@click.command("gpa")
@click.option("--digits", type=int, default=3)
def main(*, digits: int):
    res = gpa(**{g.key: prompt_credits(g) for g in Grade})
    print()
    print(f"Total GPA: {round(res, digits)}")


if __name__ == "__main__":
    main()
