from itertools import chain
from typing import Callable

from scheduler import *


class SortChain:
    raw_schedules: list[Schedule]
    chain: list[tuple[Callable, Callable]]
    def evaluate(self) -> list[Schedule]:
        table = []
        for calc_func, selector in self.chain:
            table.append([selector(calc_func(schedule)) for schedule in self.raw_schedules])
        arrayed = []
        for i in range(len(self.raw_schedules)):
            schedule = self.raw_schedules[i]
            selections = [table[j][i] for j in range(len(table))]
            arrayed.append([schedule] + [selections])
        arrayed.sort()
        return arrayed #TODO TEST THIS


def has_breaks(periods: list[list[Block]], length: int = 1) -> bool:
    for period in periods:
        count = 0
        for block in period:
            if block.is_active:
                count = 0
                continue
            count += 1
            if count >= length:
                break
        if count < length:
            return False
    return True


def calc_breaks(schedules: list[Schedule], periods: list[list[Block]]) -> list[tuple[Schedule, int, int]]:
    result = []
    for schedule in schedules:
        loaded = schedule.load()
        if not loaded:
            print("ERROR: FAILED TO LOAD SCHEDULE", schedule)
            return []

        total = 0
        previous = True
        chunk = 0

        for period in periods:
            for block in period:
                if block.is_active:
                    previous = False
                    continue
                total += 1
                if not previous:
                    chunk += 1
                    previous = True
            previous = True

        schedule.unload()
        result.append((schedule, total, chunk))
    return result






