import pandas as pd
import ast

def clean_and_normalize_data(file_path, output_path='cleaned_data.pkl'):
    """
    Loads raw behavioral data, cleans temporal artifacts, and groups by word.
    
    Args:
        file_path (str): Path to the raw CSV file.
        output_path (str): Path to save the processed pickle file.
    """
    
    # 1. Load Data
    # We explicitly treat position_time_pairs as a string initially to avoid parsing errors
    df = pd.read_csv(file_path, dtype={'position_time_pairs': str})
    
    print(f"Raw data loaded: {len(df)} trials found.")

    # 2. Define Cleaning Logic
    def parse_and_deduplicate(pair_string):
        """
        Parses stringified list, removes duplicate timestamps (keeping first).
        Returns a clean list of [position, time] lists.
        """
        try:
            # Safely evaluate the string literal to a Python list
            raw_pairs = ast.literal_eval(pair_string)
            
            clean_pairs = []
            seen_times = set()
            
            for pos, time in raw_pairs:
                # If we haven't seen this timestamp yet, add it
                if time not in seen_times:
                    clean_pairs.append([pos, time])
                    seen_times.add(time)
            
            # Optional: Ensure sorted by time (crucial for trajectory analysis)
            clean_pairs.sort(key=lambda x: x[1])
            
            return clean_pairs
            
        except (ValueError, SyntaxError):
            return [] # Return empty list if parsing fails

    # 3. Apply Cleaning
    # This converts the string column into actual Python list objects
    df['clean_traces'] = df['position_time_pairs'].apply(parse_and_deduplicate)
    
    # 4. Basic Validation
    # Drop rows where parsing failed (empty traces)
    initial_count = len(df)
    df = df[df['clean_traces'].map(len) > 0].copy()
    if len(df) < initial_count:
        print(f"Warning: Dropped {initial_count - len(df)} rows due to parsing errors.")

    # 5. Organization for Train/Test Splitting
    # We set the index to target_word to allow for easy grouping/slicing later
    # while keeping the participant_number as a column.
    df.set_index(['target_word', 'participant_number'], inplace=True)
    
    # Sort index to ensure all trials for "dindon" are physically adjacent in memory
    df.sort_index(inplace=True)

    # 6. Save Data
    # We use Pickle (.pkl) instead of CSV because CSV would force us to 
    # turn our nice lists back into strings. Pickle preserves the Python list objects.
    df.to_pickle(output_path)
    
    print(f"Success! Processed data saved to {output_path}")
    print("Data is grouped by target_word. Use pd.read_pickle() to load.")
    return df

# --- Usage Example ---
if __name__ == "__main__":
    # Create a dummy CSV for demonstration purposes based on your image
    from io import StringIO
    csv_data = """participant_number,target_word,target_word_pos,position_time_pairs
1,rouillures,4065,"[[-4065, 3.16], [-2537, 12.21], [-2411, 14.3], [-14, 19.08], [-14, 19.08], [-128, 28.8], [-3, 32.17], [0, 35.14]]"
1,vestiaires,4780,"[[-4780, 1.88], [-415, 5.6], [-415, 5.6], [-17, 12.28], [0, 31.9]]"
1,dindon,1466,"[[-1466, 1.33], [2, 8.74], [0, 10.2]]"
"""
    # Write dummy file
    with open('dummy_data.csv', 'w') as f:
        f.write(csv_data)

    # Run the cleaning
    cleaned_df = clean_and_normalize_data('dummy_data.csv')
    
    # Inspect a single trace to verify duplicate removal
    # In the raw data above, 'rouillures' has two entries for time 19.08. 
    # The output should only have one.
    print("\n--- Verification: Trace for 'rouillures' ---")
    print(cleaned_df.loc['rouillures']['clean_traces'].iloc[0])