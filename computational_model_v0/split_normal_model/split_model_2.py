import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def calculate_parameters(frequency, starting_pos):
    """
    Derives model parameters based on behavioral inputs.
    """
    max_word_dist = 5000

    # Base mean for closest word 
    close_word_base_mean = 15

    # mutplies [0;1] distance by this to get mean increase
    pos_multiplier = 10

    base_mean = close_word_base_mean + (starting_pos / max_word_dist) * pos_multiplier
    # 1. Base configurations based on Frequency
    if frequency.lower() == 'high':
        base_std = 3
        skew = 0.8
    elif frequency.lower() == 'med':
        base_std = 8
        skew = 0.7
    elif frequency.lower() == 'low':
        base_std = 12
        skew = 0.1
    else:
        raise ValueError("Frequency must be 'high', 'med', or 'low'")

    # 2. Adjust for Starting Position 
    # (Assuming starting_pos is a distance metric, e.g., 0 to 100)
    # We add a delay factor: 0.2s for every unit of distance
    pos_delay = starting_pos * 0.2
    
    final_mean = base_mean + pos_delay
    
    # Optional: Distance might slightly increase variance (std)
    final_std = base_std + (starting_pos * 0.05)

    return final_mean, final_std, skew

class TrialTimeModel:
    def __init__(self, mean, std, skew):
        self.mean = mean
        self.std = std
        self.skew = skew
        
        # Pre-calculate Split Normal parameters
        # Adjust sigma based on skew (-0.99 to 0.99)
        self.sigma_L = self.std * (1 - self.skew)
        self.sigma_R = self.std * (1 + self.skew)
        
        # Shift mode to approximate the desired mean
        # (Heuristic shift for the Split Normal)
        shift = np.sqrt(2/np.pi) * (self.sigma_R - self.sigma_L)
        self.mode = self.mean - shift
        
        # Base Normalization factor for Split Normal
        self.A = np.sqrt(2/np.pi) / (self.sigma_L + self.sigma_R)

    def _raw_pdf(self, x):
        """Calculates the un-normalized Split Normal value."""
        # Select sigma based on which side of the mode we are
        sigma_x = np.where(x < self.mode, self.sigma_L, self.sigma_R)
        return self.A * np.exp(-(x - self.mode)**2 / (2 * sigma_x**2))

    def get_pdf(self, x_points):
        """
        Returns the Probability Density Function within bounds [0, limit].
        Automatically normalizes the area to 1.0.
        """
        # 1. Calculate raw curve
        y = self._raw_pdf(x_points)
        # 2. Enforce bounds (0 to limit, e.g., 60s)
        y[x_points < 0] = 0
        
        # 3. Numeric Normalization (ensure area sums to 1)
        # We integrate using the trapezoidal rule to find the area
        if np.sum(y) > 0:
            area = np.trapz(y, x_points)
            y = y / area
            
        return y
    
    def load_trial_data(self, file_path):
        """
        Loads trial times from a file. 
        Supports .pkl (dataframe with 'total_time' column), .csv (with 'total_time' column), or .txt (raw numbers).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Handle Pickle Files (Output from previous scripts)
        if file_path.endswith('.pkl'):
            df = pd.read_pickle(file_path)
            if 'total_time' not in df.columns:
                # If feature extraction wasn't run, try to calculate it on the fly
                if 'clean_traces' in df.columns:
                     return df['clean_traces'].apply(lambda x: x[-1][1] if len(x)>0 else 0).values
                raise ValueError("The .pkl file must contain a 'total_time' column.")
            return df['total_time'].values

        # 2. Handle CSV Files
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            if 'total_time' in df.columns:
                return df['total_time'].values
            raise ValueError("The .csv file must contain a 'total_time' column.")

# --- CONFIGURATION ---
# Left Skew context: High mean, "hump" is near the right, tail to the left.
TARGET_MEAN = 20    # Most people take around 48 seconds
TARGET_STD  = 8    # Spread of results
SKEW        = 0.7

# --- EXECUTION ---
model = TrialTimeModel(TARGET_MEAN, TARGET_STD, SKEW)

# 1. Generate the theoretical curve (PDF)
x = np.linspace(0, 70, 500) # Go past 60 to show the cutoff visually
pdf = model.get_pdf(x)

# 2. load actual trials
data = model.load_trial_data("C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data\\semantic_search_train_data.pkl")

# --- PLOTTING ---
plt.figure(figsize=(10, 6))

# Plot Histogram of simulated trials
plt.hist(data, bins=50, density=True, alpha=0.4, color='gray', label='Simulated Trials')

# Plot Theoretical Curve
plt.plot(x, pdf, color='blue', linewidth=2.5, label='Model Probability')

# Visual Guides
plt.axvline(np.mean(data), color='green', linestyle=':', label='Actual Mean')

plt.title(f"Distribution of Trial Times (Max 60s)\nSkew: {SKEW} (Left Skew)")
plt.xlabel("Time (seconds)")
plt.ylabel("Probability Density")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(0, 65)
plt.show()