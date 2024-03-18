
if __name__ == "__main__":
    import pandas as pd
    import sys
    import os
    import subprocess

    if len(sys.argv) != 4:
        print("Usage: python3 edinet_query_all.py ${filename} yyyy-mm-dd yyyy-mm-dd\n ${start} ${end}")

    filename = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    df = pd.read_csv(filename, skiprows=1, index_col='ＥＤＩＮＥＴコード')

    df = df[df['上場区分'] == '上場']
    tmp_count = 0 
    for i in df['提出者名']:
        if tmp_count > 3:
            break
        print(i)
        subprocess.run(args=['python3',
                            'edinet_tools.py',
                            '--target={0}'.format(i),
                            '--start={0}'.format(start),
                            '--end={0}'.format(end)])    
        tmp_count += 1
