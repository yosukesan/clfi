import sys, re
import pandas as pd
from zipfile import ZipFile
from ya_python_xbrl import XbrlApp


def read_zip_file(file_path):
    file_list = []

    with ZipFile(file_path, 'r') as f:
        if f.testzip() == ValueError:
            sys.stderr('Error: {0} could not be read. Broken zip file'.format(file_path))

        file_list = f.namelist()
        target = list(filter(lambda x:  '.xbrl' in x and 'PublicDoc' in x, file_list))
        fp = f.open(*target, 'r')

        return *target, fp.read().decode('UTF-8')


def read_xbrls(d: dict, firm: str) -> dict:
    """
    batch read XBRL files issued by the specified firm
    """

    d[firm] = {}

    df = pd.read_csv(firm, names=('firm', 'date', 'filename', 'xbrl_path', 'path'), skiprows=3)
    df = df.sort_values('date')

    for p in df['path']:
        print(p)
        xbrl_file_path, text = read_zip_file(p)
        print(xbrl_file_path)
        splitted = xbrl_file_path.split('_')

        period = splitted[0].split('-')[1][:-1]
        start = splitted[2]
        end = splitted[4][:-5]

        xbrl_app: XbrlApp = XbrlApp()
        xbrl_app.parse(text)
        d[firm]['{0}_{1}_{2}'.format(start, end, period)] = xbrl_app.data()

    return d


def parse_file_time_stamp(file_time_stamp):
    """
    return term end year and financial quarter as string
    """

    year = re.search('([0-9]{4}).*?([0-9]{4})', file_time_stamp)
    term = file_time_stamp.split('_')[-1:]
    return '{0}-{1}'.format(year.group(1), *term)


def chart_plot(target: str, firm: str, df: pd.DataFrame, params):
    """
    wrapper for chart plot
    """
    import matplotlib.pyplot as plt

    plt.rcParams['font.family'] = 'IPAGothic'
    fig, ax = plt.subplots()
    fig.set_figheight(9)
    fig.set_figwidth(16)

    ax.bar(df.index, df[target], alpha=0.7)
    ax.set_ylabel('{0} / JPY'.format(target))

    i = 0
    for x, y in zip(df.index, df[target]):
        ax.text(i*0.97, y-y*0.1, '{:.3g}'.format(y), color='black', rotation='vertical', size=12)
        i += 1

    plt.xticks(rotation=90)

    ax2 = ax.twinx()
    ax2.plot(df[target].pct_change(periods=4), 'o-', color='red')
    ax2.set_ylabel('Yearly Change', color='red')

    i = 0
    for x, y in zip(df.index, df[target].pct_change(periods=4)):
        ax2.text(i, y+y*0.05, '{:.2f}'.format(y), color='red', rotation=70, size=12)
        i += 1

    plt.title('{0}: growth_penalty_rate={1}'.format(firm, params['dcf']['growth']['penalty_rate']))
    plt.subplots_adjust(bottom=0.2)
    # plt.show()
    plt.savefig('{0}-{1}.svg'.format(firm[:-4], target))
    plt.clf()


if __name__ == '__main__':
    from collections import OrderedDict
    from model import AssetPricingModels
    import yaml

    xbrl_app: XbrlApp = XbrlApp()
    xbrl_data: dict = {}
    firm = sys.argv[1]

    # read XBRL data from zipped .xbrl file
    xbrl_data = read_xbrls(xbrl_data, firm)

    accounting_titles = {}
    accounting_titles['PL'] = ['sales', 'COGS', 'cost_of_sales', 'gross_profit', 'GA_expenses', 'operating_profit', 'profit_loss']
    accounting_titles['BS'] = ['PPE']
    accounting_titles['CF'] = ['cashflow_from_operation']
    titles = accounting_titles['PL'] + accounting_titles['BS'] + accounting_titles['CF']

    time_stamp = OrderedDict()
    res = {}

    for k in titles:
        res[k] = OrderedDict()

    for file_time_stamp in xbrl_data[firm]:
        print(file_time_stamp)
        if 'sr' in file_time_stamp:
            continue
        if 'lv' in file_time_stamp:
            continue

        ts = parse_file_time_stamp(file_time_stamp)

        for k in titles:
            res[k][ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp][k])
            time_stamp[ts] = ts

    df = pd.DataFrame(res, index=time_stamp)
    df['FCF'] = df['cashflow_from_operation'] - df['PPE']

    print(df)

    ap_model = AssetPricingModels()
    params = {}
    with open('clfi.yml', 'r') as params_file:
        params = yaml.safe_load(params_file)

    df = ap_model.load(df, params)

    chart_plot('sales', firm, df, params)
    chart_plot('COGS', firm, df, params)
    chart_plot('GA_expenses', firm, df, params)
    chart_plot('gross_profit', firm, df, params)
    chart_plot('operating_profit', firm, df, params)
    chart_plot('FCF', firm, df, params)
    #chart_plot('profit_loss', firm, df, params)
