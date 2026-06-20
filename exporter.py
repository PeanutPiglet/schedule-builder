from scheduler import *


def display_week_schedule(schedule: Schedule):
    assert isinstance(schedule.timeframe, TimeWeek)
    frame = schedule.timeframe
    output = []
    days = ['M', 'T', 'W', 'H', 'F']
    stamp = "   ".join([f"{k :02d}" for k in range(7, 22)])

    lookup = {}
    for group_name in schedule.assignment:
        for block in schedule.assignment[group_name].blocks:
            lookup[block.name] = group_name

    for i in range(len(days)):
        output.append(days[i])
        output.append(stamp)
        row = []
        for j in range(24 * i + 7, 24 * i + 22):
            block_name = frame.times[j].name
            if block_name in lookup:
                row.append(lookup[block_name][:2] + lookup[block_name][-2:])
            else:
                row.append("____")
        output.append(" ".join(row))

    return "\n".join(output)








