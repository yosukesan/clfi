import sys
import re
import pandas as pd
from zipfile import ZipFile
import pprint

def read_zip_file(file_path):
    file_list = []
    with ZipFile(file_path, 'r') as f:
        file_list = f.namelist()
        target = list(filter(lambda x:  '.xbrl' in x and 'PublicDoc' in x, file_list))    
        print(target)
        fp = f.open(*target, 'r')
        return *target, fp.read().decode('UTF-8')

def read_xbrls(d: dict, firm: str) -> dict:
    from ya_python_xbrl import XbrlParser

    d[firm] = {}

    df = pd.read_csv(firm, names=('firm', 'date', 'filename', 'xbrl_path','path'), skiprows=3)
    df = df[df['xbrl_path']!='None']
    df = df.sort_values('date')

    for p in df['path']:
        xbrl_file_path, text = read_zip_file(p)
        splitted = xbrl_file_path.split('_')

        period = splitted[0].split('-')[1][:-1]
        start = splitted[2]
        end = splitted[4][:-5]

        xbrl_parser : XbrlParser = XbrlParser()
        data = xbrl_parser.parse(text)
        d[firm]['{0}_{1}_{2}'.format(start, end, period)] = data

    return d

class XbrlTag:

    def __init__(self):
        pass
        self._current_year = set(['CurrentYTDDuration',
                        'CurrentYearDuration',
                        'CurrentYTDDuration_NonConsolidatedMember',
                        'CurrentYearDuration_NonConsolidatedMember'])
        self._sales = set(['NetSales',
                     'SalesOfProductsIFRS',
                     'RevenuesUSGAAPSummaryOfBusinessResults',
                     'SalesOfProductsIFRS'])

    def sales(self, res, t, data):

        print(t)
        #pprint.pprint(data)

        set_key : set= self._sales.intersection(data[t])

        # 有価証券報告書(参照方式) を回避する方法が現在これしかなかったのでこうする
        # ツルハHD の 2022/09/08 提出のやつで発覚した
        if len(set_key) == 0:
            return res

        if len(set_key) != 1:
            raise ValueError('Sales key error : {0}'.format(set_key))

        key: str = next(iter(set_key))
        set_current_year: set = self._current_year.intersection(data[t][key])

        if len(set_current_year) != 1:
            raise ValueError('Current year key error : {0}'.format(set_current_year))

        current_year : str = next(iter(set_current_year))      
        res['sales'].append(data[t][key][current_year])
        res['period'].append(t)

        return res


def yearly_change(data):
    diff = [0] * len(data)
    pct_change = [0] * len(data)
    for i in range(3,len(data)):
        diff[i] = float(data[i]) - float(data[i-4])
        pct_change[i] = 100*(float(data[i]) - float(data[i-4]))/(float(data[i-4]))
    return diff, pct_change

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    firms = [sys.argv[1]]

    d = {}
    xbrltag = XbrlTag()

    for firm in firms:
        d = read_xbrls(d, firm)

    for firm in d.keys():
        print(firm)
        res = {'firm': str(firm[:-4]), 'period': [], 'sales':[]}

        for t in d[firm].keys():
            res = xbrltag.sales(res, t, d[firm])

        #print(len(res['period']), len(res['sales']))

        diff, pct_change = yearly_change(res['sales'])
        fig, ax = plt.subplots()

        ax.bar(res['period'], res['sales'], alpha=0.5)
        ax.set_ylabel('Sales / JPY')

        i = 0
        for x, y in zip(res['period'], res['sales']):
            ax.text(i*0.97, y-y*0.1, '{:.3g}'.format(y), color='grey', size=8)
            i += 1

        plt.xticks(rotation=90)

        ax2 = ax.twinx()
        ax2.plot(pct_change, 'o-', color='red')
        ax2.set_ylabel('Yearly Change / %')

        i = 0
        for x, y in zip(res['period'], pct_change):
            ax2.text(i, y+y*0.2, '{:.2f}'.format(y), color='pink', size=8)
            i += 1

        plt.title(res['firm'])
        plt.subplots_adjust(bottom=0.5)
        plt.show()
        plt.savefig('{0}.png'.format(res['firm']))
        plt.clf()
