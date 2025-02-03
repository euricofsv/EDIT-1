import pandas as pd

file_path = r"C:\Users\Eurico\Desktop\EDIT\EDIT-1\sales.parquet" 
df = pd.read_parquet(file_path)

print(df.info())

print(df.head(15))

print(df.info())

print(df.describe())
