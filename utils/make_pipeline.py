import pandas as pd
from sklearn.compose import ColumnTransformer 
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

def pre_processing(numerical_columns,categorical_columns):
    numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())])

    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numerical_columns),
            ('cat', categorical_transformer, categorical_columns)])
    

def make_model_pipeline(numerical_columns,categorical_columns,keepcols):
    selector = ColumnTransformer([('selector','passthrough',keepcols)],remainder='drop')
    preprocessor = pre_processing(numerical_columns,categorical_columns)
    
    model_pipeline = Pipeline(steps=[('selector',selector),('pre_processing',preprocessor),('classifer',LogisticRegression())])
    return model_pipeline