"""
Main script for the schedule builder.
Refer to README for instructions.
"""
from scheduler import *
from postprocessing import *
import exporter
import json
import pp_template

""" -- SETTINGS -- """


# GLOBAL TEMPLATE VARIABLES
WEEK = TimeWeek()
DAY_CODE = {'M': '0', 'T': '1', 'W': '2', 'H': '3', 'F': '4'}

# INPUT QUERY
INITIAL_QUERY = "data/J26F.json"

# POST PROCESSING
INITIAL_POST_PROCESS_CHAIN: list[ChainEntry] = [
    pp_template.filter_in_lunch_break,
    pp_template.maximize_day_breaks_duration,
    pp_template.minimize_day_breaks_chunks,
    pp_template.filter_out_evening_CSC236G,
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
NUM_RES_COUNTER = 0


def get_schedule_from_results(entry: str, index: int) -> Schedule | None:
    if entry not in RESULTS:
        return None
    if index >= len(RESULTS[entry]):
        return None
    return RESULTS[entry][index][0]


def get_pp_from_template(pp: str) -> ChainEntry | None:
    if pp not in pp_template.LOOKUP:
        return None
    return pp_template.LOOKUP[pp]


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
    for func, sel, fil, name in POST_PROCESS_CHAIN:
        sort_chain.add_chain(func=func, selector=sel, filtering=fil, name=name)
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


def diff_assignments(assignments: list[dict[str, Section]]) -> int:
    """
    Return the number of common matching section-assignments.
    """
    if not assignments:
        return 0
    if len(assignments) == 1:
        return len(assignments[0])
    intersect = 0
    first = assignments[0]
    rests = assignments[1:]
    for group_name in first:
        is_common = True
        for other in rests:
            if group_name not in other:
                is_common = False
                break
            if other[group_name].name != first[group_name].name:
                is_common = False
                break
        if is_common:
            intersect += 1
    return intersect


def diff_results_rank(results: list[str]) -> list[tuple[tuple, tuple[int, float]]]:
    result_entries = []
    for res in results:
        if res not in RESULTS:
            print(f"ERROR: result '{res}' not found")
            continue
        result_entries.append(RESULTS[res])
    n = len(result_entries)
    if n == 0:
        return []
    counter = [0] * n
    lengths = [len(r) for r in result_entries]
    lengths[0] += 1
    arrayed = []
    while counter[0] < lengths[0] - 1:
        current = tuple(counter[i] for i in range(n))
        assignments = [result_entries[i][counter[i]][0].assignment for i in range(n)]
        intersect = diff_assignments(assignments)
        arrayed.append((current, intersect * -1, sum(current) / n))
        k = n - 1
        while True:
            counter[k] += 1
            if counter[k] >= lengths[k]:
                counter[k] = 0
                k -= 1
            else:
                break
    # diff = diff_assignment(r1[0].assignment, r2[0].assignment)
    # arrayed.append(((i, j), (diff[0] * -1, (i + j) / 2 )))
    arrayed.sort(key=lambda x: x[1])
    return arrayed


def diff_result(res1: str, res2: str) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    if res1 not in RESULTS:
        print(f"ERROR: result '{res1}' not found")
    if res2 not in RESULTS:
        print(f"ERROR: result '{res2}' not found")
    common: list[tuple[int, int]] = []
    first: list[int] = []
    second: list[int] = []
    ignore_second: set[int] = set()
    for i in range(len(RESULTS[res1])):
        a1 = RESULTS[res1][i][0].assignment
        is_matched = False
        for j in range(len(RESULTS[res2])):
            delta = diff_assignment(a1, RESULTS[res2][j][0].assignment)
            if delta[1] == 1.0:
                common.append((i, j))
                ignore_second.add(j)
                is_matched = True
                break
        if not is_matched:
            first.append(i)
    for i in range(len(RESULTS[res2])):
        if i not in ignore_second:
            second.append(i)
    return common, first, second


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


def pp_add(pp: ChainEntry, index: int) -> None:
    POST_PROCESS_CHAIN.insert(index, pp)
    return


def pp_pop(index: int) -> bool:
    if index >= len(POST_PROCESS_CHAIN):
        return False
    POST_PROCESS_CHAIN.pop(index)
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
            case 'pp':
                display_pp_chain()
            case 'pp-add':
                if len(arguments) < 1:
                    continue
                pp = get_pp_from_template(arguments[0])
                if not pp:
                    continue
                if len(arguments) < 2:
                    pp_add(pp, 999999)
                    continue
                try:
                    pp_add(pp, int(arguments[1]))
                except:
                    continue
            case 'pp-pop':
                if len(arguments) < 1:
                    pp_pop(-1)
                try:
                    pp_pop(int(arguments[0]))
                except:
                    continue
            case 'load':
                if len(arguments) < 1:
                    continue
                load_from_file(arguments[0])
            case 'diff':
                if len(arguments) < 2:
                    continue
                if len(arguments) < 4:
                    display_diff_result(diff_result(arguments[0], arguments[1]))
                    continue
                try:
                    display_diff_schedule(diff_schedule(
                        get_schedule_from_results(arguments[0], int(arguments[1])),
                        get_schedule_from_results(arguments[2], int(arguments[3]))
                    ))
                except:
                    continue
            case 'diff-sort':
                if len(arguments) < 1:
                    continue
                diff = diff_results_rank(arguments)
                display_list(diff)
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
        for j in range(i, i + size):
            print(lst[j])
        print(f"-- {i + size} / {n} --")
        i += size
        if input() == 'q':
            return
    for j in range(i, n):
        print(lst[j])
    print(f"-- {n} / {n} --")
    return


def display_query():
    for group in QUERY:
        print(f"{group} : {QUERY[group]}")
    return


def display_pp_chain():
    for i in range(len(POST_PROCESS_CHAIN)):
        print(f"{i}) {POST_PROCESS_CHAIN[i][3]}")
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
            print(f"schedule # {i + 1}  |  {result[i][1]}")
            print(exporter.display_week_schedule(result[i][0]))
            if input("enter 'q' to stop") == 'q':
                break
        return True
    print(f"DISPLAYING RESULT - {res} - entry {index}  |  {result[int(index)][1]}")
    print(exporter.display_week_schedule(result[int(index)][0]))
    return True


def display_diff_result(diffed: tuple[list[tuple[int, int]], list[int], list[int]]):
    common, first, second = diffed
    print(f"num common: {len(common)}")
    print(f"num first only: {len(first)}")
    print(f"num second only: {len(second)}")
    print("common:")
    display_list(common, 10)
    print("first only:")
    display_list(first, 10)
    print("second only:")
    display_list(second, 10)
    return


def display_diff_schedule(diffed: tuple[list[tuple[str, str, str]], list[str], list[str]]) -> None:
    d_sections, only1, only2 = diffed
    for group_name, ass1, ass2 in d_sections:
        print(f"{group_name} : {ass1} <-> {ass2}")
    for group_name in only1:
        print(f"first: {group_name}")
    for group_name in only2:
        print(f"second: {group_name}")
    return


if __name__ == "__main__":
    main_loop()







