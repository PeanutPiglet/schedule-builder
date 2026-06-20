# schedule-builder
A course schedule builder built in Python.
Uses brute forcing along with post processing.

# Plans
* User Inferface
* More Post-Processing Functions
* Live Data Scrap for UofT Courses
* Better Manual (the following manual may induce mild confusion)

# Manual
To run the schedule builder, execute `main.py`.

To set parameters, refer to the following section.

## Settings
Open `main.py` in any code editor. Parameters/settings are at the top of the file.
* Auxiliary Helpers: functions defined for custom macros/operations
* Global Template Variables: custom variables
* Input Query: the list of courses and their possible section times
* Post Processing: the list of post-process to apply in given order

The program find all possible combination of course-to-section assignments, then apply the post-processing to sort and filter for the output.

### Input Query
Each entry is written as `<course-name>: <possible-sections>` where `possible-sections` is the list of the possible times for the course in the notation: the day of the week followed by the 24-hour clock hours.

M: Monday; T: Tuesday; W: Wednesday; H: Thursday; F: Friday

* `M0913` means Monday from 9am to 1pm.
* `HF1619` means 4pm to 7pm on both Thursday and Friday.
* `MW0910F1314` means 9am to 10am on Monday and Wednesday, and 1pm to 2pm on Friday.

### Post Processing
_see `postprocessing.py` for details_

Each post-process step is a tuple with 3 functions
1. post-process calculation function: takes a specific `Schedule` (a course-to-section assignment) and outputs its statistics wrapped in a dataclass
2. selector function: takes the output from (1) and return the measure which is used to rank (ascending-order) all the possible schedules. The final displayed output are in this ranked order.
3. filtering function [optional, use None]: takes the output from (1) and return whether to keep this schedule in the final output.

Note that the final ranking will consider ranking from prior steps with higher priority. That is, if $A$ is ranked higher than $B$ in step one, then any further post-process steps will not between influence the ranking between $A$ and $B$. Alternatively, at any given step, further steps (for ranking) will matter only if $A$ and $B$ ranked equally at the current step.

### Output
$The final output displays the ranked schedules one at a time.
Press `enter` to continue to the next one.

Input `q` and press `enter` to stop.
