"""
Main script for the schedule builder.
Refer to README for instructions.
"""
from scheduler import *
from postprocessing import *
import exporter
import json

# AUXILIARY HELPERS
def construct_periods(periods: list[str], frame: Timeframe) -> list[list[Block]]:
    return [frame.gets(p) for p in periods]


""" -- SETTINGS -- """


# GLOBAL TEMPLATE VARIABLES
WEEK = TimeWeek()
DAY_CODE = {'M': '0', 'T': '1', 'W': '2', 'H': '3', 'F': '4'}
PERIOD_FOOD = construct_periods([
    '01214', '11214', '21214', '31214', '41214',
    '01719', '11719', '21719', '31719', '41719'
], WEEK)
PERIOD_AFTERNOON = construct_periods([
    '01417', '11417', '21417', '31417', '41417'
], WEEK)
PERIOD_DAY = construct_periods([
    '00922', '10922', '20922', '30922', '40922'
], WEEK)

# INPUT QUERY
INITIAL_QUERY = "data/J26F.json"
# INITIAL_QUERY = {
#     'MAT237Y': ['MTH0910', 'MTH1112', 'MTH1415', 'MTH1718'],
#     'MAT237T': ['T1011', 'T1112', 'T1213', 'T1314', 'T1415', 'T1516', 'T1617', 'T1718', 'T1819'],
#     'MAT244H': ['W0911F1011', 'W1113F1112', 'W1315F1415', 'W1517F1516'],
#     'MAT244T': ['M0910', 'M1011', 'M1112', 'M1213', 'M1314', 'M1415', 'M1516', 'M1617', 'M1718', 'M1819'],
#     'STA257H': ['M1113W1112', 'M1517W1516'],
#     'STA257T': ['W1213', 'W1617'],
#     'CSC265H': ['MWF1516'],
#     'CSC207H': ['W1315', 'W1517', 'H1315', 'H1820'],
#     'CSC207T': ['H0911'],
#     'PHY250H': ['MW0910'],
#     'PHY250T': ['T1516', 'W1617', 'F1415', 'F1617']
# }

# POST PROCESSING
INITIAL_POST_PROCESS_CHAIN: list[ChainEntry] = [
    (
        lambda s: test_breaks(s, PERIOD_FOOD, 1),
        lambda x: 0, # (sum(x.max_break_length) / len(x.max_break_length)) * -1,
        lambda x: all(x.has_break)
    ),
    (
        lambda s: test_breaks(s, PERIOD_DAY, 1),
        lambda x: (sum(x.max_break_length) / len(x.max_break_length)) * -1,
        None
    ),
    (
        lambda s: calc_breaks(s, PERIOD_DAY),
        lambda x: x.num_chunks,
        None
    ),
    (
        lambda s: test_intersect(s, [("CSC236G", "W1821")]),
        lambda x: 0,
        lambda x: not x.has_intersection
        #lambda x: ("CSC236G" not in x.assignment) or (x.assignment["CSC236G"].name != "W1821")
    )
]


""" -- CODE -- """

""" SYSTEMATICS """


def load_from_file(filename: str) -> list | None:
    with open(filename, 'r') as f:
        data = json.load(f)

        # sanity check
        if isinstance(data, list):
            return None
        for entry in data:
            if not isinstance(data[entry], list):
                return None

        global QUERY
        QUERY = data
        return QUERY


RESULTS: dict[str, list[tuple[Schedule, list]]] = {}
QUERY = load_from_file(INITIAL_QUERY) if isinstance(INITIAL_QUERY, str) else INITIAL_QUERY.copy()
POST_PROCESS_CHAIN = INITIAL_POST_PROCESS_CHAIN.copy()
NUM_RES_COUNTER = 1


def get_schedule_from_results(entry: str, index: int) -> Schedule | None:
    if entry not in RESULTS:
        return None
    if index >= len(RESULTS[entry]):
        return None
    return RESULTS[entry][index][0]


def construct_section(name: str, timeframe: Timeframe):
    block_buffer = []
    day_buffer = []
    i = 0
    while i < len(name):
        if name[i] in "MTWHF":
            day_buffer.append(name[i])
            i += 1
        else:
            t = name[i:i+4]
            for day in day_buffer:
                block_buffer.extend(timeframe.gets(DAY_CODE[day] + t))
            day_buffer.clear()
            i += 4
    return Section(name, block_buffer)


def solve():
    # initialization
    sections: dict[str, Section] = {}
    groups: dict[str, Group] = {}

    for group_name in QUERY:
        section_buffer = []
        for section_name in QUERY[group_name]:
            if section_name in sections:
                section_buffer.append(sections[section_name])
            else:
                section_buffer.append(construct_section(section_name, WEEK))
        group = Group(group_name, section_buffer)
        groups[group_name] = group

    # solving
    sol = SolverAll(WEEK, list(sections.values()), list(groups.values()))
    schedules = sol.solve()

    # post process
    sort_chain = SortChain(raw_schedules=schedules)
    for func, sel, fil in POST_PROCESS_CHAIN:
        sort_chain.add_chain(func=func, selector=sel, filtering=fil)
    result = sort_chain.evaluate()

    # saving
    global NUM_RES_COUNTER
    NUM_RES_COUNTER += 1
    result_name = str(NUM_RES_COUNTER)
    RESULTS[result_name] = result

    return result


""" TOOL FUNCTIONS """


def diff_assignment(ass1: dict[str, Section], ass2: dict[str, Section]) -> tuple[int, float, float]:
    """
    Return tuple of the number of matching section-assignments, the ratio of matching to union,
    and the ratio of matching to intersection.
    """
    intersect = 0
    matching = 0
    for group in ass1:
        if group in ass2:
            intersect += 1
            if ass1[group].name == ass2[group].name:
                matching += 1
    union = len(ass1) + len(ass2) - intersect
    return matching, matching / union, matching / intersect


def diff_results(res1: str, res2: str) -> list[tuple[tuple[str, str], tuple[int, float]]]:
    if res1 not in RESULTS:
        print(f"ERROR: result '{res1}' not found")
    if res2 not in RESULTS:
        print(f"ERROR: result '{res2}' not found")
    result1 = RESULTS[res1]
    result2 = RESULTS[res2]
    arrayed = []
    for i in range(len(result1)):
        r1 = result1[i]
        for j in range(len(result2)):
            r2 = result2[j]
            diff = diff_assignment(r1[0].assignment, r2[0].assignment)
            arrayed.append(((i, j), (diff[0] * -1, (i + j) / 2 )))

    arrayed.sort(key=lambda x: x[1])
    return arrayed


def diff_schedule(sch1: Schedule, sch2: Schedule) -> tuple[list[tuple[str, str, str]], list[str], list[str]]:
    d_sections: list[tuple[str, str, str]] = []
    only2: list[str] = []
    visited: set[str] = set()
    for group_name in sch1.assignment:
        visited.add(group_name)
        if group_name in sch2.assignment:
            ass1 = sch1.assignment[group_name].name
            ass2 = sch2.assignment[group_name].name
            if ass1 != ass2:
                d_sections.append((group_name, ass1, ass2))
    for group_name in sch2.assignment:
        if group_name in visited:
            visited.remove(group_name)
            continue
        only2.append(group_name)
    only1 = [group_name for group_name in visited]
    return d_sections, only1, only2


""" EDIT FUNCTIONS """


def cut_result(res: str, limit: int) -> bool:
    if res not in RESULTS:
        print(f"Result '{res}' not found")
        return False
    RESULTS[res] = RESULTS[res][:limit]
    return True


""" DISPLAY """


def main_loop() -> None:
    while True:
        inputted = input().strip()
        if not inputted:
            continue

        splitted = inputted.split(" ")
        cmd = splitted[0]
        arguments = splitted[1:]

        match cmd:
            case 'solve':
                solve()
            case 'show':
                if len(arguments) < 1:
                    display_results_list()
                else:
                    if len(arguments) < 2:
                        display_result(arguments[0])
                    else:
                        display_result(arguments[0], arguments[1])
            case 'query':
                display_query()
            case 'load':
                if len(arguments) < 1:
                    continue
                load_from_file(arguments[0])
            case 'diff':
                if len(arguments) < 2:
                    continue
                if len(arguments) < 4:
                    diff = diff_results(arguments[0], arguments[1])
                    display_list(diff)
                    continue
                try:
                    display_diff_schedule(diff_schedule(
                        get_schedule_from_results(arguments[0], int(arguments[1])),
                        get_schedule_from_results(arguments[2], int(arguments[3]))
                    ))
                except:
                    continue
            case 'cut':
                if len(arguments) < 2:
                    continue
                try:
                    cut_result(arguments[0], int(arguments[1]))
                except:
                    continue


def display_list(lst: list, size: int = 5) -> None:
    n = len(lst)
    i = 0
    while i < n - size:
        for j in range(i, i + 5):
            print(lst[j])
        print(f"-- {i + size} / {n} --")
        i += size
        if input() == 'q':
            return
    for j in range(i * size, n):
        print(lst[j])
    return


def display_query():
    for group in QUERY:
        print(f"{group} : {QUERY[group]}")
    return


def display_results_list():
    print("Results: ")
    for res_name in RESULTS:
        print(f"{res_name} : {len(RESULTS[res_name])} schedules")
    return


def display_result(res: str, index: str = "") -> bool:
    if res not in RESULTS:
        print(f"ERROR: no result '{res}' found")
        return False
    result = RESULTS[res]
    if index == "":
        print(f"DISPLAYING RESULT - {res} - {len(result)} schedules")
        for i in range(len(result)):
            print(f"schedule # {i + 1}")
            print(exporter.display_week_schedule(result[i][0]))
            if input("enter 'q' to stop") == 'q':
                break
        return True
    print(f"DISPLAYING RESULT - {res} - entry {index}")
    print(exporter.display_week_schedule(result[int(index)][0]))
    return True


def display_diff_schedule(result: tuple[list[tuple[str, str, str]], list[str], list[str]]) -> None:
    d_sections, only1, only2 = result
    for group_name, ass1, ass2 in d_sections:
        print(f"{group_name} : {ass1} <-> {ass2}")
    for group_name in only1:
        print(f"first: {group_name}")
    for group_name in only2:
        print(f"second: {group_name}")
    return


if __name__ == "__main__":
    main_loop()







