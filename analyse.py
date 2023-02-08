import sys
import re
import pandas as pd
from zipfile import ZipFile

def read_zip_file(file_path):
    file_list = []
    with ZipFile(file_path, 'r') as f:
        file_list = f.namelist()
        target = list(filter(lambda x:  '.xbrl' in x and 'PublicDoc' in x, file_list))    
        fp = f.open(*target, 'r')
        return *target, fp.read().decode('UTF-8')


def read_xbrls(d: dict, firm: str) -> dict:
    from ya_python_xbrl import XbrlParser

    print(firm)
    d[firm] = {}

    df = pd.read_csv(firm, names=('firm', 'date', 'path'), skiprows=3)

    for p in df['path']:
        xbrl_file_path, text = read_zip_file(p)
        splitted = xbrl_file_path.split('_')

        periode = splitted[0].split('-')[1][:-1]
        start = splitted[2]
        end = splitted[4][:-5]

        #print(p)
        #print(xbrl_file_path)
        #print(periode, start, end)

        xbrl_parser : XbrlParser = XbrlParser()
        data = xbrl_parser.parse(text)
        d[firm]['{0}_{1}_{2}'.format(periode, start, end)] = data

    return d

def yearly_change(data):
    diff = [0] * len(data)
    pct_change = [0] * len(data)
    for i in range(3,len(data)):
        diff[i] = data[i] - data[i-4]
        pct_change[i] = 100*(data[i] - data[i-4])/data[i-4]
    return diff, pct_change

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    firms = ['freee.csv', 'plade.csv']
    #firms = ['plade.csv']

    d = {}

    for firm in firms:
        d = read_xbrls(d, firm)

    for firm in d.keys():
        print(firm)
        res = {'firm': str(firm[:-4]), 'periode': [], 'sales':[]}
        for t in d[firm].keys():
            #print(t)
            #print(d[firm][t])
            if 'CurrentYTDDuration' in d[firm][t]['NetSales']:
                #print(d[firm][t]['NetSales']['CurrentYTDDuration'])
                res['sales'].append(d[firm][t]['NetSales']['CurrentYTDDuration'])
                res['periode'].append(t)
            elif 'CurrentYTDDuration_NonConsolidatedMember' in d[firm][t]['NetSales']:
                #print(d[firm][t]['NetSales']['CurrentYTDDuration_NonConsolidatedMember'])
                res['sales'].append(d[firm][t]['NetSales']['CurrentYTDDuration_NonConsolidatedMember'])
                res['periode'].append(t)
            elif 'CurrentYearDuration_NonConsolidatedMember' in d[firm][t]['NetSales']:
                #print(d[firm][t]['NetSales']['CurrentYearDuration_NonConsolidatedMember'])
                res['sales'].append(d[firm][t]['NetSales']['CurrentYearDuration_NonConsolidatedMember'])
                res['periode'].append(t)

        diff, pct_change = yearly_change(res['sales'])

        fig, ax = plt.subplots()

        ax.bar(res['periode'], res['sales'], alpha=0.5)
        ax.set_ylabel('Sales / JPY')

        plt.xticks(rotation=60)

        ax2 = ax.twinx()
        ax2.plot(pct_change, 'o-', color='red')
        ax2.set_ylabel('Yearly Change / %')

        plt.title(res['firm'])
        plt.subplots_adjust(bottom=0.4)
        #plt.show()
        plt.savefig('{0}.png'.format(res['firm']), dpi=300)
        plt.clf()
