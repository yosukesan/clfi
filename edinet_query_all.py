
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

    #for i in df['提出者名']:
    for i in df.index:
        print('{0}'.format(df['提出者名'][i]))
        with open('{0}.csv'.format(df['提出者名'][i]), 'w') as redirect_file:
            subprocess.run(args=['python3',
                'edinet_tools.py',
                '--target={0}'.format(i),
                '--start={0}'.format(start),
                '--end={0}'.format(end)],
                stdout=redirect_file)
            subprocess.run(args=['python3', 'analyse.py', '{0}.csv'.format(df['提出者名'][i])])
        print('-----------------------')
