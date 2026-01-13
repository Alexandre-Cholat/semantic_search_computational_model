import pandas as pd
import numpy as np
import os

def prepare_data_for_lmm(input_pkl_path, output_pkl_path='lmm_ready_data.pkl'):
    """
    Loads cleaned behavioral data and calculates specific dependent variables 
    (num_jumps, total_time) for Linear Mixed Effects Modeling.
    """
    
    if not os.path.exists(input_pkl_path):
        raise FileNotFoundError(f"File not found: {input_pkl_path}")
    
    print(f"Loading data from {input_pkl_path}...")
    df = pd.read_pickle(input_pkl_path)
    
    # --- 1. Define Extraction Logic ---
    def get_dependent_variables(trace):
        """
        Input: A list of [position, time] pairs (e.g., [[-400, 1.2], [0, 5.5]])
        Output: Series with num_jumps and total_time
        """
        # Safety check for empty traces
        if not isinstance(trace, list) or len(trace) == 0:
            return pd.Series([np.nan, np.nan])
        
        # Variable 1: Number of Jumps (Count)
        # We assume every entry in the list is a 'jump' or state change
        n_jumps = len(trace)
        
        # Variable 2: Total Time (Duration)
        # The time of the very last recorded position in the sequence
        t_time = trace[-1][1]
        
        return pd.Series([n_jumps, t_time])

    # --- 2. Apply Extraction ---
    print("Calculating 'num_jumps' and 'total_time'...")
    
    # Apply the function to the 'clean_traces' column
    # This creates two new columns instantly
    df[['num_jumps', 'total_time']] = df['clean_traces'].apply(get_dependent_variables)
    
    # --- 3. Statistical Transformations (Crucial for LMMs) ---
    # LMMs assume normally distributed residuals. 
    # Time and Counts are usually log-normal (skewed). We create log versions now.
    
    # Log(Total Time) - Handle zeros by adding a tiny epsilon if needed, 
    # though total_time should usually be > 0.
    df['log_total_time'] = np.log(df['total_time'])
    
    # Log(Num Jumps)
    df['log_num_jumps'] = np.log(df['num_jumps'])

    # --- 4. Extract Independent Variables (Fixed Effects) ---
    # We need 'starting_letter' as a column for the LMM formula.
    # It is currently part of the index 'target_word'.
    
    # Reset index temporarily to access 'target_word' easily if it's in the index
    was_multi_index = isinstance(df.index, pd.MultiIndex)
    if was_multi_index:
        df_reset = df.reset_index()
    else:
        df_reset = df.copy()
        
    # Extract Starting Letter (First character of the word)
    df_reset['starting_letter'] = df_reset['target_word'].str[0]
    
    # Restore index if desired, or keep as columns for Statsmodels (easier)
    # We will return the reset version as it's easier for stats libraries to read.
    final_df = df_reset
    
    # --- 5. Save ---
    final_df.to_pickle(output_pkl_path)
    print(f"Success. Data saved to {output_pkl_path}")
    print("\n--- Data Preview ---")
    print(final_df[['target_word', 'num_jumps', 'total_time', 'starting_letter']].head())
    
    return final_df

if __name__ == "__main__":
    # Point this to your cleaned/split pickle file
    INPUT_FILE = "cleaned_data.pkl" 
    
    try:
        df_lmm = prepare_data_for_lmm(INPUT_FILE)
        
        # Optional: Check distribution roughly
        print("\nMean Time:", df_lmm['total_time'].mean())
        print("Mean Jumps:", df_lmm['num_jumps'].mean())
        
    except Exception as e:
        print(f"Error: {e}")