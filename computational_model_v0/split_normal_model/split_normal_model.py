import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import ast  # Library to safely convert strings to lists

FREQ_MAP = {
    "dame": 0, "guerre": 0, "raison": 0, "voiture": 0,
    "dindon": 1, "gaspillages": 1, "récurrence": 1, "vestiaires": 1,
    "damasquinerie": 2, "galonner": 2, "rouillures": 2, "vulvaires": 2
}

def calculate_parameters(frequency, starting_pos):
    """Derives model parameters based on behavioral inputs."""
    max_word_dist = 5000
    close_word_base_mean = 19
    pos_multiplier = 20
    
    # base_mean = close_word_base_mean + (starting_pos / max_word_dist) * pos_multiplier

    if frequency.lower() == 'high':
        base_mean = 19
        base_std = 5.5
        skew = 0.8
    elif frequency.lower() == 'med':
        base_mean = 22
        base_std = 7.5
        skew = 0.6
    elif frequency.lower() == 'low':
        base_mean = 25
        base_std = 8.5
        skew = 0.7
    else:
        raise ValueError("Frequency must be 'high', 'med', or 'low'")

    return base_mean, base_std, skew

class TrialTimeModel:
    def __init__(self, mean, std, skew):
        self.mean = mean
        self.std = std
        self.skew = skew
        
        self.sigma_L = self.std * (1 - self.skew)
        self.sigma_R = self.std * (1 + self.skew)
        
        shift = np.sqrt(2/np.pi) * (self.sigma_R - self.sigma_L)
        self.mode = self.mean - shift
        self.A = np.sqrt(2/np.pi) / (self.sigma_L + self.sigma_R)

    def _raw_pdf(self, x):
        sigma_x = np.where(x < self.mode, self.sigma_L, self.sigma_R)
        return self.A * np.exp(-(x - self.mode)**2 / (2 * sigma_x**2))

    def get_pdf(self, x_points):
        y = self._raw_pdf(x_points)
        y[x_points < 0] = 0
        
        if np.sum(y) > 0:
            # Fix: Use trapz (or trapezoid in newer numpy versions)
            try:
                area = np.trapezoid(y, x_points) # Newer numpy
            except AttributeError:
                area = np.trapz(y, x_points)     # Older numpy
            y = y / area     
        return y
    
    def _extract_time_from_row(self, row_val):
        """
        Helper to parse the string/list and get the final time.
        Expected format: [[x, time], [x, time]...]
        """
        try:
            # 1. If it's a string (e.g., "[[-12, 1.1]]"), convert to list
            data = row_val
            if isinstance(data, str):
                data = ast.literal_eval(data)
            
            # 2. Extract last element -> second value
            if isinstance(data, list) and len(data) > 0:
                last_pair = data[-1] 
                # last_pair should be like [-1213, 1.18]
                return float(last_pair[1])
            elif isinstance(data, (int, float)):
                return float(data)
        except Exception:
            return np.nan
        return 0.0

    def load_trial_data(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load the pickle file
        df = pd.read_pickle(file_path)

        # FIX: If 'target_word' is in the index (from your cleaning script), 
        # bring it back as a column so dataLoader can find it.
        if 'target_word' not in df.columns:
            df = df.reset_index()
            
        # Ensure total_time exists (if not already calculated by your extraction script)
        if 'total_time' not in df.columns and 'clean_traces' in df.columns:
            df['total_time'] = df['clean_traces'].apply(lambda x: x[-1][1] if len(x)>0 else 0)

        return df
    
    def dataLoader(self, df, freq_str):
        freq_code_map = {'high': 0, 'med': 1, 'low': 2}
        target_code = freq_code_map.get(freq_str.lower())
        
        if target_code is None:
            return df

        # The column name from your extraction script is 'target_word'
        target_col = 'target_word'
        
        if target_col not in df.columns:
            print(f"Error: {target_col} not found. Available: {list(df.columns)}")
            return pd.DataFrame()

        # Create a cleaned version of the column to handle encoding errors (Ã© -> é)
        # and ensure case-insensitivity to match FREQ_MAP keys.
        cleaned_words = df[target_col].astype(str).str.replace('Ã©', 'é', regex=False).str.strip().str.lower()
        
        # Filter: Map cleaned words to codes and compare to target_code
        mask = cleaned_words.map(lambda x: FREQ_MAP.get(x, -1)) == target_code
        filtered_df = df[mask].copy()
        
        print(f"Filter found {len(filtered_df)} trials for '{freq_str}' group.")
        return filtered_df
       
    def visualize1(self, comparison_data=None, freq_str=None, x_limit=70):
        x = np.linspace(0, x_limit, 500)
        pdf = self.get_pdf(x)

        plt.figure(figsize=(10, 6))

        # 1. Plot Actual Data
        if comparison_data is not None and len(comparison_data) > 0:
            # Ensure data is numeric
            clean_data = np.array(comparison_data, dtype=float)
            clean_data = clean_data[~np.isnan(clean_data)] # Remove NaNs
            
            if len(clean_data) > 0:
                
                plt.hist(clean_data, bins=30, density=True, alpha=0.4, 
                         color='gray', label='Actual Trials')
                plt.axvline(np.mean(clean_data), color='green', 
                            linestyle=':', label=f'Actual Mean ({np.mean(clean_data):.2f})')
            else:
                print("Warning: Data provided but contained no valid numbers.")

        # 2. Plot Model Curve
        plt.plot(x, pdf, color='blue', linewidth=2.5, label='Model PDF')

        plt.title(f"Model param: \nMean: {self.mean:.1f} | Std: {self.std:.1f} | Skew: {self.skew}")
        if freq_str:
            plt.suptitle(f"Frequency Filter: {freq_str}")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Probability Density")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, x_limit)
        plt.show()

    def visualize(self, comparison_data=None, freq_str=None, x_limit=70):
        """
        Visualizes the model and calculates RMSE in seconds using 
        Quantile-Based Comparison.
        """
        x_plot = np.linspace(0, x_limit, 500)
        pdf_model = self.get_pdf(x_plot)

        plt.figure(figsize=(10, 6))
        rmse_seconds = None

        if comparison_data is not None and len(comparison_data) > 0:
            actual_times = np.sort(np.array(comparison_data, dtype=float))
            actual_times = actual_times[~np.isnan(actual_times)]

            # 1. Create Percentiles (Quantiles) for the Data
            # This represents the "Actual" distribution shape
            percentiles = np.linspace(0, 1, 100)
            data_quantiles = np.percentile(actual_times, percentiles * 100)

            # 2. Create Percentiles (Quantiles) for the Model
            # We use the Cumulative Distribution Function (CDF) to find model quantiles
            cdf_model = np.cumsum(pdf_model)
            cdf_model /= cdf_model[-1]  # Normalize
            
            # Find the x-values (seconds) where the model reaches each percentile
            model_quantiles = np.interp(percentiles, cdf_model, x_plot)

            # 3. Calculate RMSE in Seconds
            # This measures the horizontal distance between the two shapes
            errors_seconds = model_quantiles - data_quantiles
            rmse_seconds = np.sqrt(np.mean(errors_seconds**2))
            
            # 4. Plot Histogram
            plt.hist(actual_times, bins=30, density=True, alpha=0.4, color='gray', label='Actual Data')
            plt.axvline(np.mean(actual_times), color='green', linestyle=':', label='Data Mean')

            print(f"\n--- Quantile Evaluation ({freq_str}) ---")
            print(f"RMSE (Distribution Fit in Seconds): {rmse_seconds:.2f}s")

        # Plot Model Curve
        plt.plot(x_plot, pdf_model, color='blue', linewidth=2.5, label='Split Normal Model')
        plt.axvline(self.mean, color='blue', linestyle='--', alpha=0.5, label='Model Mean')

        if rmse_seconds is not None:
            plt.text(0.95, 0.85, f'RMSE: {rmse_seconds:.2f}s', transform=plt.gca().transAxes, 
                     ha='right', fontsize=12, bbox=dict(facecolor='white', alpha=0.8, edgecolor='blue'))

        plt.title(f"Semantic Speech Pattern Model")
        if freq_str:
            plt.suptitle(f"Frequency Filter: {freq_str}")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Probability Density")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlim(0, x_limit)
        plt.show()


# --- INPUTS ---
INPUT_FREQUENCY = input("Enter frequency ('high', 'med', or 'low'): ")
INPUT_START_POS = 10 

# --- EXECUTION ---
try:
    # 1. Calculate Stats
    calc_mean, calc_std, calc_skew = calculate_parameters(INPUT_FREQUENCY, INPUT_START_POS)
    print(f"Model Parameters -> Mean: {calc_mean:.2f}, Std: {calc_std}, Skew: {calc_skew}")

    # 2. Build Model
    model = TrialTimeModel(calc_mean, calc_std, calc_skew)

    # 3. Load Data
    # Update this path to your exact file location
    file_path = "C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data\\semantic_search_train_data.pkl"
    
    full_df = model.load_trial_data(file_path)
    print(f"Loaded {len(full_df)} rows from file.")

    # 4. Filter Data
    filtered_df = model.dataLoader(full_df, INPUT_FREQUENCY)
    
    # 5. Extract Time Values
    if 'total_time' in filtered_df.columns:
        time_values = filtered_df['total_time'].values
        print(f"Plotting {len(time_values)} trials.")
        model.visualize(comparison_data=time_values, freq_str=INPUT_FREQUENCY)
    else:
        print("Error: Could not extract time values.")
        model.visualize(comparison_data=None, freq_str=INPUT_FREQUENCY)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"An error occurred: {e}")