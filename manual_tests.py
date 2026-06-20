from scheduler import *
import postprocessing

day_code = {'M': '0', 'T': '1', 'W': '2', 'H': '3', 'F': '4'}


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
                block_buffer.extend(timeframe.gets(day_code[day] + t))
            day_buffer.clear()
            i += 4
    return Section(name, block_buffer)


def basic():
    week = TimeWeek()

    query= {
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
    SECTIONS: dict[str, Section] = {}
    GROUPS: dict[str, Group] = {}

    for group_name in query:
        section_buffer  = []
        for section_name in query[group_name]:
            if section_name in SECTIONS:
                section_buffer.append(SECTIONS[section_name])
            else:
                section_buffer.append(construct_section(section_name, week))
        group = Group(group_name, section_buffer)
        GROUPS[group_name] = group


    sol = SolverAll(week, list(SECTIONS.values()), list(GROUPS.values()))
    schedules = sol.solve()

    return schedules


def process_foods(schedules: list[Schedule]):
    filtered = filter_foods(schedules)
    if not filtered:
        print("WARNING: NOTHING LEFT AFTER FILTER")
        return []
    frame = filtered[0].timeframe
    query = [
        '01214', '11214', '21214', '31214', '41214',
        '01719', '11719', '21719', '31719', '41719'
    ]
    periods = [frame.gets(q) for q in query]
    return postprocessing.calc_breaks(filtered, periods)


def filter_foods(schedules: list[Schedule]) -> list[Schedule]:
    result = []
    for schedule in schedules:
        loaded = schedule.load()
        if not loaded:
            print("FAILED TO LOAD SCHEDULE", schedule)
            return []

        frame = schedule.timeframe
        query = [
            '01214', '11214', '21214', '31214', '41214',
            '01719', '11719', '21719', '31719', '41719'
        ]
        periods = [frame.gets(q) for q in query]
        if postprocessing.has_breaks(periods):
            result.append(schedule)

        schedule.unload()
    return result






