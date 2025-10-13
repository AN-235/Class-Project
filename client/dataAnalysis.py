import pandas as pd
import numpy as np
import streamlit as st
from scipy import stats

#loading csv file
df = pd.read_csv("../data/2022-nov16.csv")

#seeing the column names
print(df.columns.tolist())

#computing z-score for numeric fields temperature, salinity, and odo
numeric_cols = ['Temperature (c)', 'Salinity (ppt)', 'ODO mg/L']
z_scores = np.abs(stats.zscore(df[numeric_cols], nan_policy='omit'))

#identifying outliers with z-scores greater than 3
outlier_mask = (z_scores > 3).any(axis=1)

#getting rows
total_rows = len(df)
rows_removed = outlier_mask.sum()
rows_remaining = total_rows - rows_removed

#printing row information
print(f"Original number of rows: {total_rows}")
print(f"Removed rows: {rows_removed}")
print(f"Remaining rows: {rows_remaining}")

#removing outliers
df_cleaned = df[~outlier_mask]

#saving cleaned data file
df_cleaned.to_csv('data_cleaned.csv', index=False)