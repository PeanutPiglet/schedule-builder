from postprocessing import *

PERIOD_FOOD = [
    '01214', '11214', '21214', '31214', '41214',
    '01719', '11719', '21719', '31719', '41719'
]
PERIOD_AFTERNOON = [
    '01417', '11417', '21417', '31417', '41417'
]
PERIOD_DAY = [
    '00922', '10922', '20922', '30922', '40922'
]

filter_in_lunch_break = (
    lambda s: test_breaks(s, PERIOD_FOOD, 1),
    lambda x: 0,
    lambda x: all(x.has_break),
    "filter in lunch break"
)

maximize_day_breaks_duration = (
    lambda s: test_breaks(s, PERIOD_DAY, 1),
    lambda x: (sum(x.max_break_length) / len(x.max_break_length)) * -1,
    None,
    "maximize day breaks duration"
)

minimize_day_breaks_chunks = (
    lambda s: calc_breaks(s, PERIOD_DAY),
    lambda x: x.num_chunks,
    None,
    "minimize day breaks chunks"
)

filter_out_evening_CSC236G = (
    lambda s: test_intersect(s, [("CSC236G", "W1821")]),
    lambda x: 0,
    lambda x: not x.has_intersection,
    "filter out evening CSC236G"
)


LOOKUP: dict[str, ChainEntry] = {
    "filter_in_lunch_break": filter_in_lunch_break,
    "maximize_day_breaks_duration": maximize_day_breaks_duration,
    "minimize_day_breaks_chunks": minimize_day_breaks_chunks,
    "filter_out_evening_CSC236G": filter_out_evening_CSC236G
}






