import pandas as pd
import glob
import pathlib
import os

# print("START")
for directory in glob.glob("./tutor_eval_logs/**/**/"):
    # print(directory)
    path_parts = pathlib.Path(directory).parts
    # directory = os.path.sep.join(path_parts[1:-1])
    time = path_parts[-1]
    profile_dir = path_parts[-2]

    print(f"{profile_dir}({time}):")

    for f in glob.glob(os.path.join(directory,"*.csv")):
        df = pd.read_csv(f)

        if("action" in f):
            counts = df['action_is_correct'].value_counts()
            # print("action counts", counts)
            tr,fa = counts.get(True,0), counts.get(False,0)
            print(f"Next Action Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
        elif("incorrect" in f):
            counts = df['response_is_correct'].value_counts()
            # print("incorrect counts",counts)
            tr,fa = counts.get(True,0), counts.get(False,0)
            print(f"Incorrect Grade Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
        elif("correct" in f):
            counts = df['response_is_correct'].value_counts()
            # print("correct counts", counts)
            tr,fa = counts.get(True,0), counts.get(False,0)
            print(f"Correct Grade Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
        

        # print(" ", df.columns)


# print("END")

