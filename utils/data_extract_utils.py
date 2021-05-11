import io
import zipfile
import pandas as pd
import numpy as np
import dropbox

def extract_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo) as thefile:
                yield zipinfo.filename, thefile
         
# Retrieve all CSVs from dropbox
def get_home_credit_data():
    # Connect to dropbox
    dbx = dropbox.Dropbox('cHV7yAR0J6YAAAAAAAAAAVQ1NLCrOwerbaNltPWHslYXKuUTJ5_wfgJsuFcmx83o')
    
    # Download, and extract data from dropbox into memory. 
    data = {}
    for entry in dbx.files_list_folder('').entries:
        response = dbx.files_download('/{}'.format(entry.name))

        if 'zip' in entry.name:
            content = extract_zip(response[1].content)

            for file in content:
                df = pd.read_csv(file[1])
                data[entry.name.replace('.csv.zip', '')] = df
    return data

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
        min_month_balance = -96
        # Normalize by the min_month_balance, the further back the balance was the
        # lest weight we give it
        return np.sum(x['STATUS'].values * np.absolute((min_month_balance - x['MONTHS_BALANCE'].values)/min_month_balance))

    # Map statuses
    dpd_counts_df = bureau_balances_df.replace({"STATUS": DPD_STATUS_MAP})
    dpd_counts_df = dpd_counts_df.groupby(['SK_ID_BUREAU']).apply(sum_of_dpd)
    dpd_counts_df = pd.DataFrame(dpd_counts_df, columns=['DPD_COUNTS']);

    bureau_with_dpds = pd.concat([bureau_df, dpd_counts_df], axis=1)
    
    bureau_with_dpds = bureau_with_dpds[:][['SK_ID_CURR', *EXTRACTRED_BUREAU_COLUMNS]]
    
    # Further aggregation to make sure unique SK_ID_CURR are returned
    bureau_with_dpds = bureau_with_dpds.groupby(['SK_ID_CURR']).mean()
    
    return bureau_with_dpds.fillna(value=0)
                
def extract_features_from_installments_payments(installments_payments_df):
    def mis_instalment_payment(x):
        return np.mean(x['AMT_INSTALMENT'].values - x['AMT_PAYMENT'].values)

    # Let's create mis_instalment_payment attributes
    mis_instalment_payment = installments_payments_df.groupby('SK_ID_CURR').apply(mis_instalment_payment)
    mis_instalment_payment_df = pd.DataFrame(mis_instalment_payment, columns=['MIS_INSTALMENT_PAYMENTS'])
    mis_instalment_payment_df.fillna(value=0, inplace=True)
    
    return mis_instalment_payment_df

def get_clean_credit(df_credit_raw):
    useful = ['MONTHS_BALANCE', 'AMT_BALANCE', 'AMT_CREDIT_LIMIT_ACTUAL','AMT_RECEIVABLE_PRINCIPAL', 'AMT_TOTAL_RECEIVABLE','NAME_CONTRACT_STATUS_Completed','SK_ID_CURR','SK_DPD','SK_DPD_DEF']
        

        
    full_dummies = pd.get_dummies(df_credit_raw,columns = ['NAME_CONTRACT_STATUS'])
    full_trimmed = full_dummies[useful]
    dpd_counts_sum = full_trimmed.groupby(['SK_ID_CURR'])['SK_DPD'].sum().reset_index()
    dpd_df_counts_sum = full_trimmed.groupby(['SK_ID_CURR'])['SK_DPD_DEF'].sum().reset_index()
    full_trimmed['SK_DPD_SUM'] = dpd_counts_sum['SK_DPD']
    full_trimmed['SK_DPD_DEF_SUM'] = dpd_df_counts_sum['SK_DPD_DEF']
    
    full_not_nan = full_trimmed.fillna(value=0)
    
    return full_not_nan.drop(columns=['SK_DPD','SK_DPD_DEF'])

# Remove features that are highly correlated with each other for improving model simplicity
def remove_highly_correlated_columns(df_orig, threshold):
    df = df_orig.copy()
    corr = df.corr()
    col_corr = set()
    for i in range(len(corr.columns)):
        for j in range(i):
            if (corr.iloc[i, j] >= threshold) and (corr.columns[j] not in col_corr):
                column_name = corr.columns[i]
                col_corr.add(column_name)
                if column_name in df.columns:
                    print('REMOVING {} which is correlated with {}'.format(column_name, corr.columns[j]))
                    del df[column_name]
    return df