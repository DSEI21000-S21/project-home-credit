import pandas as pd
from sklearn.utils import resample
def getUnionOnApplication(df_minority,df_application):
    return pd.merge(
        df_minority,
        df_application, #here the differance
        on='SK_ID_CURR',
        how='left' #and add the how='left'
    )

def downsample(full_dataset):
    df_majority = full_dataset[full_dataset.TARGET==0]
    df_minority = full_dataset[full_dataset.TARGET==1]
    df_majority_downsampled = resample(df_majority, 
                                    replace=False,    # sample without replacement
                                    n_samples=len(df_minority),     # to match minority class
                                    random_state=123) 
    
    # Combine minority class with downsampled majority class
    df_downsampled = pd.concat([df_majority_downsampled, df_minority])
    df_downsampled