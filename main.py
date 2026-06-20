from scheduler import *
from postprocessing import *
import exporter

# AUXILIARY HELPERS
def construct_periods(periods: list[str], frame: Timeframe) -> list[list[Block]]:
    return [frame.gets(p) for p in periods]

# GLOBAL TEMPLATE VARIABLES
WEEK = TimeWeek()
DAY_CODE = {'M': '0', 'T': '1', 'W': '2', 'H': '3', 'F': '4'}
PERIOD_FOOD = construct_periods([
    '01214', '11214', '21214', '31214', '41214',
    '01719', '11719', '21719', '31719', '41719'
], WEEK)
PERIOD_AFTERNOON = [
    '01417', '11417', '21417', '31417', '41417'
]

# INITIAL SETTINGS
QUERY = {
    'MAT237Y': ['MTH0910', 'MTH1112', 'MTH1415', 'MTH1718'],
    'MAT237T': ['T1011', 'T1112', 'T1213', 'T1314', 'T1415', 'T1516', 'T1617', 'T1718', 'T1819'],
    'MAT244F': ['W0911F1011', 'W1113F1112', 'W1315F1415', 'W1517F1516'],
    'MAT244T': ['M0910', 'M1011', 'M1112', 'M1213', 'M1314', 'M1415', 'M1516', 'M1617', 'M1718', 'M1819'],
    'STA257F': ['M1113W1112', 'M1517W1516'],
    'STA257T': ['W1213', 'W1617', ''],
    'CSC265F': ['MWF1516'],
    'CSC207F': ['W1315', 'W1517', 'H1315', 'H1820'],
    'CSC207T': ['H0911']
}


POST_PROCESS_CHAIN: list[ChainEntry] = [
    (
    lambda s: test_breaks(s, PERIOD_FOOD, 1),
    lambda x: (sum(x.max_break_length) / len(x.max_break_length)) * -1,
    lambda x: all(x.has_break)
    ),
]


# CODE

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


def main():
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

    print("DISPLAYING RESULT")
    for i in range(len(result)):
        print(i + 1)
        print(exporter.display_week_schedule(result[i][0]))
        if input() == "q":
            break


if __name__ == "__main__":
    main()







