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
    xbrl_data = read_xbrls(xbrl_data, firm)

    # temporary dict storage for plot. In Xbrl file, time stamp is stored as string tags,
    # this need to be converted into numeral
    res = {}

    # Profit Loss
    sales_container = OrderedDict()
    cost_of_sales = OrderedDict()
    gross_profit = OrderedDict()
    GA_expenses = OrderedDict()
    operating_profit = OrderedDict()
    net_profit = OrderedDict()
    profit_loss = OrderedDict()
    cashflow_from_operation = OrderedDict()
    ppe = OrderedDict()

    # Balance Sheet
    PPE = OrderedDict()

    time_stamp = OrderedDict()

    for file_time_stamp in xbrl_data[firm]:
        print(file_time_stamp)
        if 'sr' in file_time_stamp:
            continue
        if 'lv' in file_time_stamp:
            continue

        ts = parse_file_time_stamp(file_time_stamp)

        # Profit Loss
        sales_container[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['sales'])
        cost_of_sales[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['COGS'])
        gross_profit[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['gross_profit'])
        GA_expenses[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['GA_expenses'])
        operating_profit[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['operating_profit'])
        profit_loss[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['profit_loss'])

        # Balance sheet
        ppe[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['PPE'])
        # depriciation[ts] = xbrl_app.current_year(d[firm][file_time_stamp]['depriciation'])
        # amortisation[ts] = xbrl_app.current_year(d[firm][file_time_stamp]['amortisation'])

        # cash_flow
        cashflow_from_operation[ts] = xbrl_app.current_year(xbrl_data[firm][file_time_stamp]['cashflow_from_operation'])

        time_stamp[ts] = ts

    res['sales'] = sales_container
    res['COGS'] = cost_of_sales
    res['gross_profit'] = gross_profit
    res['GA_expenses'] = GA_expenses
    res['operating_profit'] = operating_profit
    res['profit_loss'] = profit_loss
    res['cashflow_from_operation'] = cashflow_from_operation
    res['PPE'] = ppe

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
