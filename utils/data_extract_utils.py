import io
import zipfile
import pandas as pd
import numpy as np

def extract_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo) as thefile:
                yield zipinfo.filename, thefile

EXTRACTRED_BUREAU_COLUMNS = ['AMT_CREDIT_DEBT_RATIO', 'CREDIT_DAY_OVERDUE', 'DPD_COUNTS']
                
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
    
    bureau_with_dpds = bureau_with_dpds[:][['SK_ID_CURR', *EXTRACTRED_BUREAU_COLUMNS]]
    
    # Further aggregation to make sure unique SK_ID_CURR are returned
    bureau_with_dpds = bureau_with_dpds.groupby(['SK_ID_CURR']).mean()
    
    return bureau_with_dpds.fillna(value=0)

def get_clean_credit(df_credit_raw):
    useful = ['MONTHS_BALANCE', 'AMT_BALANCE', 'AMT_CREDIT_LIMIT_ACTUAL',
       'AMT_RECEIVABLE_PRINCIPAL', 'AMT_TOTAL_RECEIVABLE','NAME_CONTRACT_STATUS_Completed','SK_ID_CURR','SK_DPD','SK_DPD_DEF']
        

        
    full_dummies = pd.get_dummies(df_credit_raw,columns = ['NAME_CONTRACT_STATUS'])
    full_trimmed = full_dummies[useful]
    dpd_counts_sum = full_trimmed.groupby(['SK_ID_CURR'])['SK_DPD'].sum().reset_index()
    dpd_df_counts_sum = full_trimmed.groupby(['SK_ID_CURR'])['SK_DPD_DEF'].sum().reset_index()
    full_trimmed['SK_DPD_SUM'] = dpd_counts_sum['SK_DPD']
    full_trimmed['SK_DPD_DEF_SUM'] = dpd_df_counts_sum['SK_DPD_DEF']
    
    full_not_nan = full_trimmed.fillna(value=0)
    
    return full_not_nan.drop(columns=['SK_DPD','SK_DPD_DEF'])