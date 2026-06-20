from typing import Callable, Any
from dataclasses import dataclass
from scheduler import *


@dataclass
class PostProcessOutputEntry:
    schedule: Schedule

type ChainEntry = tuple[
    Callable[[Schedule], PostProcessOutputEntry],
    Callable[[PostProcessOutputEntry], Any],
    Callable[[PostProcessOutputEntry], bool] | None
]

class SortChain:
    raw_schedules: list[Schedule]
    chain: list[ChainEntry]
    def evaluate(self, top: int = -1) -> list[Schedule]:
        arrayed: list[tuple[Schedule, list]] = [(self.raw_schedules[i], []) for i in range(len(self.raw_schedules))]
        current = self.raw_schedules
        for calc_func, selector, filtering in self.chain:
            if filtering:
                new_current = []
                new_arrayed = []
                for i in range(len(current)):
                    schedule = current[i]
                    calculated = calc_func(schedule)
                    if filtering(calculated):
                        arrayed[i][1].append(selector(calculated))
                        new_current.append(schedule)
                        new_arrayed.append(arrayed[i])
                arrayed = new_arrayed
                current = new_current
            else:
                for i in range(len(current)):
                    schedule = current[i]
                    arrayed[i][1].append(selector(calc_func(schedule)))

        arrayed.sort(key=lambda x: x[1:])
        return arrayed
        return [arr[0] for arr in arrayed]

    def __init__(self, raw_schedules: list[Schedule] = None, chain: list[ChainEntry] = None):
        self.raw_schedules = raw_schedules if raw_schedules else []
        self.chain = chain if chain else []
    def add_schedule(self, schedule):
        self.raw_schedules.append(schedule)
    def add_chain(self, func: Callable, selector: Callable, filtering: Callable | None = None):
        self.chain.append((func, selector, filtering))
    def pop_schedule(self) -> Schedule | None:
        if len(self.raw_schedules) == 0:
            return None
        return self.raw_schedules.pop()
    def pop_chain(self) -> ChainEntry | None:
        if len(self.chain) == 0:
            return None
        return self.chain.pop()


@dataclass
class TestBreaksOutputEntry(PostProcessOutputEntry):
    has_break: list[bool]
    break_length: int
    max_break_length: list[int]

def test_breaks(schedule: Schedule, periods: list[list[Block]], length: int = 1,
                force: bool = False) -> TestBreaksOutputEntry | None:
    loaded = schedule.load()
    if not loaded:
        print("ERROR: FAILED TO LOAD SCHEDULE", schedule)
        if not force:
            return None

    has_break = []
    max_break_length = []
    for period in periods:
        count = 0
        maximum = 0
        for block in period:
            if block.is_active:
                count = 0
                continue
            count += 1
            if count > maximum:
                maximum = count
        has_break.append(maximum >= length)
        max_break_length.append(maximum)

    result = TestBreaksOutputEntry(
        schedule=schedule,
        has_break=has_break,
        break_length=length,
        max_break_length=max_break_length
    )
    schedule.unload()
    return result


@dataclass
class CalcBreaksOutputEntry(PostProcessOutputEntry):
    num_total: int
    num_chunks: int

def calc_breaks(schedule: Schedule, periods: list[list[Block]], force: bool = False) -> CalcBreaksOutputEntry | None:
    loaded = schedule.load()
    if not loaded:
        print("ERROR: FAILED TO LOAD SCHEDULE", schedule)
        if not force:
            return None

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
    result = CalcBreaksOutputEntry(schedule, total, chunk)
    return result






