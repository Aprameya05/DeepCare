import pandas as pd
import os

path = r"c:\Users\Aprameya\OneDrive\Desktop\Breast-Cancer-Detection-master\Dataset\Brest Cancer Dataset.csv"
print(f"Checking path: {path}")
print(f"Exists: {os.path.exists(path)}")

try:
    df = pd.read_csv(path)
    print("Loaded successfully!")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
