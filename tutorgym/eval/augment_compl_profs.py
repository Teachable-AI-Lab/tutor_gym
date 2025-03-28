import pandas as pd
import argparse
import glob
import json
from tutorgym.utils import unique_hash
from tutorgym.shared import Action


def main(profile_path, tutor_kind):
    filename, ext = profile_path.split(".")
    out_path = f"{filename}-aug.{ext}"

    profile_data = {}
    with open(profile_path, 'r') as profile:
        for line in profile:
            obj = json.loads(line)
            line_hash = unique_hash(line)
            profile_data[line_hash] = obj

    
    for csv_path in glob.glob(f"tutor_aug_data/{tutor_kind}/*.csv"):
        df = pd.read_csv(csv_path)

        for index, row in df.iterrows():
            correct = row['action_is_correct']
            line_hash = row['hash_id']
            # print(line_hash, correct, type(correct))
            if(not correct and line_hash in profile_data):
                obj = profile_data[line_hash]
                incorrect_actions = obj['incorrect_actions']

                inc_act_d = {
                    "selection" : row["selection"],
                    "action_type" : row["action_type"],
                    "input" : row["input"],
                }

                if inc_act_d not in incorrect_actions:
                    incorrect_actions.append(inc_act_d)

                print("Corrects:")
                for cor_act_d in obj['correct_actions']:
                    tup = tuple(cor_act_d.values())
                    print(tup)

                print("Incorrects:")
                for inc_act_d in incorrect_actions:
                    tup = tuple(inc_act_d.values())
                    print(tup)

    # Write the augmented completeness profile
    with open(out_path, 'w') as out_profile:
        for h, objs in profile_data.items():
            out_profile.write(json.dumps(objs)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Augment completeness profiles with LLM-generated incorrect actions.')
    parser.add_argument('--tutor-kind', type=str, default="apprentice",
                        choices=['apprentice', 'oatutor', 'ctat'],
                        help='The kind of tutor: "apprentice", "oatutor" or "ctat"')
    parser.add_argument('--profile', type=str, default="apprentice_compl.prof",
                       help='Path to the profile file (default: apprentice_compl.prof)')

    args = parser.parse_args()
    main(args.profile, args.tutor_kind)
