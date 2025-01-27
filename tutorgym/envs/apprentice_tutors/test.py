from ref_log_tutor import Domain, htn_logarithms_power_problem

print(Domain['solve'])
Domain['solve'].preconditions = [Domain['solve'].preconditions[0]]
Domain['solve'].subtasks = [Domain['solve'].subtasks[0]]
print(Domain['solve'])


possible_selections = [x.name for x in Domain['solve'].subtasks[0]]
for idx, selection in enumerate(possible_selections):
    print(selection, idx)