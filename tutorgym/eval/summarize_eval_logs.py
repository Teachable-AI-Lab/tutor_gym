import pandas as pd
import glob
import pathlib
import os
import json
import argparse
import shutil

# print("START")

parser = argparse.ArgumentParser(description='Run LLM evaluation with different models')
parser.add_argument('--show-all', action='store_true',
                   help='Show all results instead of just complete ones.')
parser.add_argument('--delete-incomplete', action='store_true',
                   help='delete incomplete logs')

args = parser.parse_args()
show_all = args.show_all
delete_incomplete = args.delete_incomplete
bad_dirs_count = 0


for directory in glob.glob("./tutor_eval_logs/**/**/"):
    # print(directory)
    path_parts = pathlib.Path(directory).parts
    # directory = os.path.sep.join(path_parts[1:-1])
    time = path_parts[-1]
    profile_dir = path_parts[-2]

    

    profile_info = None
    profile_info_path = os.path.join(directory,"profile_info.json")
    if(os.path.exists(profile_info_path)):
        with open(profile_info_path, 'r') as f:
            profile_info = json.load(f)        

    a_df = pd.read_csv(os.path.join(directory,"action_check.csv")) 

    if(show_all or profile_info and len(a_df) == profile_info['profile_num_lines']):
        print(f"{profile_dir}({time}):")
        print(f"{directory}")

        counts = a_df['action_is_correct'].value_counts()
        tr,fa = counts.get(True,0), counts.get(False,0)
        print(f"Next Action:     Accuracy {100*tr/max(tr+fa,1):02.2f}% ({tr}/{(tr+fa)})")
        a_df = None # Collect early in case big

        correct_path = os.path.join(directory,"correct_check.csv")
        if(os.path.exists(correct_path)):
            with open(correct_path, 'r') as f:
                c_df = pd.read_csv(f) 
            counts = c_df['response_is_correct'].value_counts()
            # print("correct counts", counts)
            tr,fa = counts.get(True,0), counts.get(False,0)
            print(f"Correct Grade:   Accuracy {100*tr/max(tr+fa,1):02.2f}% ({tr}/{(tr+fa)})")
            c_df = None # Collect early in case big

        incorrect_path = os.path.join(directory,"incorrect_check.csv")
        if(os.path.exists(incorrect_path)):
            with open(incorrect_path, 'r') as f:
                i_df = pd.read_csv(f) 
            counts = i_df['response_is_correct'].value_counts()
            tr,fa = counts.get(True,0), counts.get(False,0)
            print(f"Incorrect Grade: Accuracy {100*tr/max(tr+fa,1):02.2f}% ({tr}/{(tr+fa)})")
            i_df = None # Collect early in case big
    else:
        if(delete_incomplete):
            shutil.rmtree(directory)
        
        bad_dirs_count += 1

if(not show_all and bad_dirs_count > 0):
    print(f"... plus {bad_dirs_count} incomplete logs. Add --show-all flag to see all logs.")

    # for f in glob.glob(os.path.join(directory,"*.csv")):
    #     df = pd.read_csv(f)

    #     if("action" in f):
    #         counts = df['action_is_correct'].value_counts()
    #         # print("action counts", counts)
    #         tr,fa = counts.get(True,0), counts.get(False,0)
    #         print(f"Next Action Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
    #     elif("incorrect" in f):
    #         counts = df['response_is_correct'].value_counts()
    #         # print("incorrect counts",counts)
    #         tr,fa = counts.get(True,0), counts.get(False,0)
    #         print(f"Incorrect Grade Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
    #     elif("correct" in f):
    #         counts = df['response_is_correct'].value_counts()
    #         # print("correct counts", counts)
    #         tr,fa = counts.get(True,0), counts.get(False,0)
    #         print(f"Correct Grade Accuracy {tr}/{(tr+fa)} {100*tr/max(tr+fa,1):.2f}%")
        

        # print(" ", df.columns)


# print("END")

