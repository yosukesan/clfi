from collections import OrderedDict
import pandas as pd


class APModel:

    def __init__(self):
        pass

    def generate_year(self, year, quarter, forward_year) -> list:
        """
        Estimate
        """

        quarters = ['q1', 'q2', 'q3', 'as']
        yq = [1, 0, 0, 0]

        # search the latest quarter
        qp = quarters.index(quarter, 0, len(quarters))

        indecies = []
        y = year

        for i in range(0, forward_year * len(quarters)):
            q = quarters[(qp+1) % len(quarters)]
            y += yq[(qp+1) % len(quarters)]
            indecies.append('{0}-{1} E'.format(y, q))
            qp += 1

        return indecies

    def projection(self, pseries, forward_year, params) -> OrderedDict:
        """
        Extrapolate series
        """

        penalty = params['growth_penalty']
        min_growth_rate = params['min_growth_rate']
        ch_series = pseries.pct_change(periods=4).dropna()
        ave_change = ch_series.mean() + 1.0

        d = OrderedDict()
        d[forward_year[0]] = pseries[pseries.index[-4]] * ave_change
        d[forward_year[1]] = pseries[pseries.index[-3]] * ave_change
        d[forward_year[2]] = pseries[pseries.index[-2]] * ave_change
        d[forward_year[3]] = pseries[pseries.index[-1]] * ave_change

        interval = 4

        for i in range(4, len(forward_year)):

            if i % interval == 0:
                if params['is_cost']:
                    ave_change += penalty
                else:
                    ave_change -= penalty
                ave_change = max(ave_change, min_growth_rate)
                interval += interval*2

            d[forward_year[i]] = d[forward_year[i-4]] * ave_change

        return d

    def prediction(self, df, params) -> pd.DataFrame:
        import sys
        import copy

        year = int(df.index[-1].split('-')[0])
        quarter = df.index[-1].split('-')[1]

        org_data = {}
        org_data['column'] = df.columns
        org_data['index'] = df.index
        forward_year = params['forward_year']

        indecies = self.generate_year(year, quarter, forward_year)

        cost_params = copy.copy(params)
        cost_params['is_cost'] = True

        estimated_df = pd.DataFrame(
            {'sales': self.projection(df['sales'], indecies, params),
            'COGS': self.projection(df['COGS'], indecies, cost_params),
            'gross_profit': self.projection(df['gross_profit'], indecies, params),
            'GA_expenses': self.projection(df['GA_expenses'], indecies, cost_params),
            'operating_profit': self.projection(df['operating_profit'], indecies, params),
            'profit_loss': self.projection(df['profit_loss'], indecies, params)},
            index=indecies)

        # overwrite profits
        estimated_df['gross_profit'] = estimated_df['sales'] - estimated_df['COGS']
        estimated_df['operating_profit'] = estimated_df['gross_profit'] - estimated_df['GA_expenses']

        df = pd.concat([df, estimated_df])

        for i in df.columns:
            df['{0} %'.format(i)] = df[i].pct_change(periods=4)

        return df

    def load(self, df, params):
        return self.prediction(df, params)
