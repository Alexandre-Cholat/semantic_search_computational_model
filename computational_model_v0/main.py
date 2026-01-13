import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, MixedLM
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Define your experimental factors
def add_experimental_factors(df):
    """Add controlled experimental factors to the dataset"""
    
    # Starting letter distance (you'll need to map this based on your design)
    # Example mapping - adjust based on your actual distances
    letter_distances = {'G': 2000, 'D': 1500, 'V': 4800, 'R': 4000}  # example
    
    df['starting_distance'] = df['target_word'].str[0].map(letter_distances)
    df['abs_initial_distance'] = df['position_time_pairs'].apply(
        lambda x: abs(ast.literal_eval(x)[0][0])
    )
    
    # Word frequency (categorical: high, med, low)
    frequency_levels = {
        'gaspillages': 'low', 'galonner': 'med', 'guerre': 'high',
        'dindon': 'low', 'dame': 'high', 'damasquinerie': 'med', 
        'vulvaires': 'low', 'voiture': 'high', 'vestiaires': 'med',
        'rouillures': 'low', 'récurrence': 'med', 'raison': 'high'
    }
    
    df['frequency'] = df['target_word'].map(frequency_levels)
    df['frequency_code'] = df['frequency'].map({'high': 2, 'med': 1, 'low': 0})
    
    return df

# Apply to your data
df = add_experimental_factors(your_data)