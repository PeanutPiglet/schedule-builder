from __future__ import annotations


class Timeframe:
    times: list[Block]
    def __init__(self):
        self.times = []
    def gets(self, t: str) -> list[Block]:
        raise NotImplementedError


class TimeWeek(Timeframe):
    def __init__(self):
        super().__init__()
        for i in range(121):
            self.times.append(Block(name=f"{i // 24} | {i % 24 :02d}"))
    def gets(self, t: str) -> list[Block]:
        day = 24 * int(t[0])
        return self.times[day + int(t[1:3]) : day + int(t[3:5])]
    def __str__(self):
        output = []
        days = ['M', 'T', 'W', 'H', 'F']
        stamp = " ".join([f"{k :02d}" for k in range(7, 22)])
        for i in range(len(days)):
            output.append(days[i])
            output.append(stamp)
            row = []
            for j in range(24 * i + 7, 24 * i + 22):
                if self.times[j].is_active:
                    row.append("##")
                else:
                    row.append("__")
            output.append(" ".join(row))
        return "\n".join(output)


class Block:
    name: str
    is_active: bool
    usages: list[Section]

    def __init__(self, name: str, is_active: bool = False, usages: list[Section] | None = None):
        self.name = name
        self.is_active = is_active
        self.usages = usages if usages is not None else []

    def __str__(self):
        return self.name

    def activate(self, caller: Section):
        self.is_active = True
        for section in self.usages:
            if section is caller:
                continue
            section.add_conflict()

    def deactivate(self, caller: Section):
        self.is_active = False
        for section in self.usages:
            if section is caller:
                continue
            section.remove_conflict()


class Section:
    name: str
    blocks: list[Block]
    conflicts: int
    usages: list[Group]
    def __init__(self, name: str, blocks: list[Block] | None = None, conflicts: int = 0,
                 usages: list[Group] | None = None):
        self.name = name
        self.blocks = blocks if blocks is not None else []
        self.conflicts = conflicts
        self.usages = usages if usages is not None else []
        for block in blocks:
            block.usages.append(self)

    def __str__(self):
        return self.name

    def add_conflict(self):
        if self.conflicts == 0:
            for group in self.usages:
                group.remove_avail()
        self.conflicts += 1

    def remove_conflict(self):
        self.conflicts -= 1
        if self.conflicts == 0:
            for group in self.usages:
                group.add_avail()

    def add_block(self, block: Block):
        assert block not in self.blocks
        self.blocks.append(block)
        block.usages.append(self)
        if block.is_active:
            self.add_conflict()


class Group:
    name: str
    sections: list[Section]
    num_available: int
    is_assigned: bool
    def __init__(self, name: str, sections: list[Section] = None, is_assigned: bool = False):
        self.name = name
        self.sections = sections if sections is not None else []
        self.num_available = sum(1 for x in self.sections if x.conflicts == 0)
        self.is_assigned = is_assigned
        for sec in sections:
            sec.usages.append(self)

    def __str__(self):
        return self.name

    def add_avail(self):
        self.num_available += 1

    def remove_avail(self):
        self.num_available -= 1

    def add_section(self, section: Section):
        assert section not in self.sections
        self.sections.append(section)
        section.usages.append(self)
        if section.conflicts == 0:
            self.add_avail()

    def assign(self, sec: Section) -> bool:
        """
        :param sec: the target section to assign
        :return: whether the assignment caused dead-conflict
        """
        if sec.conflicts > 0:
            return True

        self.is_assigned = True
        for block in sec.blocks:
            block.activate(sec)

        #TODO: check dead-conflict
        return False

    def unassign(self, sec: Section) -> bool:
        """
        :param sec: the target section to unassign
        :return: the unassignment was successful
        """
        if not self.is_assigned:
            return False

        self.is_assigned = False
        for block in sec.blocks:
            block.deactivate(sec)

        return True


class Schedule:
    """
    A schedule/assignment of groups to sections
    Use Schedule.load() before Block-dependent methods!
    Use Schedule.unload() after Block-dependent methods to clean-up!
    """
    timeframe: Timeframe
    assignment: dict[str, Section]
    def __init__(self, timeframe: Timeframe, assignment: dict[str, Section] = None):
        self.timeframe = timeframe
        self.assignment = assignment if assignment is not None else {}

    def __str__(self):
        return str(self.timeframe)

    def load(self, reconstructs: bool = False) -> bool:
        if reconstructs:
            temp = []
            for block in self.timeframe.times:
                temp.append(Block(name=block.name, is_active=False, usages=block.usages))
            self.timeframe = Timeframe()
            self.timeframe.times = temp
        else:
            if any(block.is_active for block in self.timeframe.times):
                print("ERROR: cannot load schedule on active blocks. Use reconstructs=True to force clean blocks.")
                return False
        for section in self.assignment.values():
            for block in section.blocks:
                block.activate(section)
        return True

    def unload(self):
        for section in self.assignment.values():
            for block in section.blocks:
                if block.is_active:
                    block.deactivate(section)
                else:
                    print("WARNING: trying to deactivate inactive Block")


class Solver:
    frame: Timeframe
    sections: list[Section]
    groups: list[Group]

    def __init__(self, frame: Timeframe, sections: list[Section], groups: list[Group]):
        self.frame = frame
        self.sections = sections
        self.groups = groups

    def solve(self) -> list[Schedule]:
        raise NotImplementedError


class SolverAll(Solver):
    def solve(self):
        result: list[Schedule] = []
        queue: list[Group] = self.groups.copy()
        queue.sort(key=lambda x: x.num_available, reverse=True)

        self._solve(queue, result, {})

        return result

    def _solve(self, queue: list[Group], result: list[Schedule], ass: dict[str, Section | None]):
        if len(queue) == 0:
            # print("ZERO")
            schedule = Schedule(self.frame, ass.copy())
            result.append(schedule)
            return

        curr_group = queue.pop()

        for sec in curr_group.sections:
            conflicted = curr_group.assign(sec)
            ass[curr_group.name] = sec
            if not conflicted:
                # print(f"continuing {curr_group.name} -> {sec.name}")
                self._solve(queue, result, ass)
            curr_group.unassign(sec)
            ass[curr_group.name] = None

        queue.append(curr_group)


def test1():
    week = TimeWeek()

    query_sections = {
        'CSC1': ['00912', '20912'],
        'CSC2': ['01314', '21314'],
        'MAT1': ['00912', '30912'],
        'MAT2': ['10912', '40912'],
        'PHY1': ['01214', '41214'],
        'PHY2': ['11314', '41314']
    }
    SECTIONS: dict[str, Section] = {}
    for section in query_sections:
        blocks = []
        for chunk in query_sections[section]:
            blocks.extend(week.gets(chunk))
        SECTIONS[section] = Section(section, blocks)

    query_groups = {
        'CSC': ['CSC1', 'CSC2'],
        'MAT': ['MAT1', 'MAT2'],
        'PHY': ['PHY1', 'PHY2']
    }
    GROUPS = {}
    for group in query_groups:
        group_sections = [SECTIONS[sec] for sec in query_groups[group]]
        GROUPS[group] = Group(group, group_sections)

    sol = SolverAll(week, list(SECTIONS.values()), list(GROUPS.values()))
    schedules = sol.solve()

    return schedules