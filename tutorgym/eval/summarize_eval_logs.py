import pandas as pd
import glob
import pathlib
import os

for f in glob.glob("tutor_eval_logs/**/*.csv"):
    df = pd.read_csv(f)
    path_parts = pathlib.Path(f).parts
    directory = os.path.sep.join(path_parts[1:-1])
    file = path_parts[-1]

    print(directory, file)
    print(df.columns)



