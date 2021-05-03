import pandas as pd
def getUnionOnApplication(df_minority,df_application):
    return pd.merge(
        df_minority,
        df_application, #here the differance
        on='SK_ID_CURR',
        how='left' #and add the how='left'
    )
