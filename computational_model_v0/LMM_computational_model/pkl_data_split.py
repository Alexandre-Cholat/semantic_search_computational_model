import pandas as pd
import ast
import os

def split_data_by_letter(df, test_letters):
    """
    Splits the dataframe into Train and Test sets based on starting letters.
    
    Args:
        df (pd.DataFrame): The cleaned dataframe with 'target_word' in the index.
        test_letters (list): List of starting letters to reserve for the TEST set.
    """
    # Get the list of words from the index
    # We use get_level_values because 'target_word' is part of the MultiIndex
    target_words = df.index.get_level_values('target_word')
    
    # Create a boolean mask: True if word starts with any letter in test_letters
    # tuple(test_letters) is required for startswith
    is_test_word = target_words.str.startswith(tuple(test_letters))
    
    # Split the data
    test_set = df[is_test_word]
    train_set = df[~is_test_word] # ~ means NOT
    
    return train_set, test_set

# --- Main Execution ---
if __name__ == "__main__":
    # Define which letters go into the TEST set
    TEST_LETTERS = ['g'] 

    # 2. Load Cleaned Data
    clean_df = pd.read_pickle(r"C:\Users\alexa\OneDrive\Documents\tech-projects\semantic_search_data\semantic_search_cleaned_data.pkl")

    # 3. Run Splitting
    train_df, test_df = split_data_by_letter(clean_df, TEST_LETTERS)
    
    # 4. Print Statistics
    print("\n--- Split Statistics ---")
    print(f"Test Letters: {TEST_LETTERS}")
    print(f"Total Trials: {len(clean_df)}")
    print(f"Train Set:    {len(train_df)} trials ({len(train_df.index.get_level_values(0).unique())} unique words)")
    print(f"Test Set:     {len(test_df)} trials ({len(test_df.index.get_level_values(0).unique())} unique words)")

    # 5. Save Outputs
    output_dir = r"C:\Users\alexa\OneDrive\Documents\tech-projects\semantic_search_data"
    train_output_path = os.path.join(output_dir, "semantic_search_train_data.pkl")
    test_output_path = os.path.join(output_dir, "semantic_search_test_data.pkl")
    
    # Save the split datasets
    train_df.to_pickle(train_output_path)
    test_df.to_pickle(test_output_path)
    
    # Optional: Verify the split
    print("\nSample Test Words:", test_df.index.get_level_values('target_word').unique().tolist())