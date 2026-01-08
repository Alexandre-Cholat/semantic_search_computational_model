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
    
    # Sort index
    df.sort_index(inplace=True)

    # 6. Save Data
    # We use Pickle to preserve the Python list objects.
    df.to_pickle(output_path)
    
    print(f"Success! Processed data saved to {output_path}")
    print("Data is grouped by target_word. Use pd.read_pickle() to load.")
    return df

# --- Usage  ---
if __name__ == "__main__":

    file_path = "C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data\\semantic_search_raw_experiments.csv"
    output_path = "C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data\\semantic_search_cleaned_data.pkl"

    # Run the cleaning
    clean_and_normalize_data(file_path, output_path)
    
    