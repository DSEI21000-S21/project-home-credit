import io
import zipfile
import pandas as pd
import numpy as np

def extract_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo) as thefile:
                yield zipinfo.filename, thefile
                
def extract_features_from_bureau(bureau_df, bureau_balances_df):
    bureau_df['AMT_CREDIT_SUM_DEBT'] = bureau_df['AMT_CREDIT_SUM_DEBT'].fillna(value=0)
    bureau_df['AMT_CREDIT_DEBT_RATIO'] =  bureau_df['AMT_CREDIT_SUM_DEBT']/bureau_df['AMT_CREDIT_SUM']
    bureau_df['AMT_CREDIT_DEBT_RATIO'] = bureau_df['AMT_CREDIT_DEBT_RATIO'].replace([np.inf, -np.inf, np.nan], 0)

    bureau_df = bureau_df.set_index('SK_ID_BUREAU')
    
    DPD_STATUS_MAP = {
        'C': 0, 
        'X': 0,
        '0': 0,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
    }
    def sum_of_dpd(x):
        sum = 0
        for status in x['STATUS']:
            sum += DPD_STATUS_MAP[status]
        return sum

    dpd_counts_df = bureau_balances_df.groupby(['SK_ID_BUREAU']).apply(sum_of_dpd)
    dpd_counts_df = pd.DataFrame(dpd_counts_df, columns=['DPD_COUNTS']);
    bureau_with_dpds = pd.concat([bureau_df, dpd_counts_df], axis=1)
    
    bureau_with_dpds = bureau_with_dpds[:][['SK_ID_CURR', 'AMT_CREDIT_DEBT_RATIO', 'CREDIT_DAY_OVERDUE', 'DPD_COUNTS']]
    
    # Further aggregation to make sure unique SK_ID_CURR are returned
    bureau_with_dpds = bureau_with_dpds.groupby(['SK_ID_CURR']).mean()
    
    return bureau_with_dpds.fillna(value=0)