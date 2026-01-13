import numpy as np
import matplotlib.pyplot as plt

class TrialTimeModel:
    def __init__(self, mean, std, skew, time_limit=60):
        self.mean = mean
        self.std = std
        self.skew = skew
        self.limit = time_limit
        
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
        
        # 2. Apply Hard Constraints (0 to Limit)
        mask = (x_points >= 0) & (x_points <= self.limit)
        y[~mask] = 0
        
        # 3. Numeric Normalization (ensure area sums to 1)
        # We integrate using the trapezoidal rule to find the area
        if np.sum(y) > 0:
            area = np.trapz(y, x_points)
            y = y / area
            
        return y

    def generate_trials(self, n_trials=1000):
        """
        Generates N random trial times using Rejection Sampling.
        This fits the custom curve perfectly.
        """
        samples = []
        
        # Find the max height of the curve to set rejection ceiling
        test_x = np.linspace(0, self.limit, 200)
        max_pdf_val = np.max(self._raw_pdf(test_x)) * 1.5 # buffer
        
        while len(samples) < n_trials:
            # 1. Pick a random time and a random height
            t_rand = np.random.uniform(0, self.limit)
            h_rand = np.random.uniform(0, max_pdf_val)
            
            # 2. Evaluate curve at that time
            curve_val = self._raw_pdf(t_rand)
            
            # 3. Accept if height is under the curve
            if h_rand <= curve_val:
                samples.append(t_rand)
                
        return np.array(samples)

# --- CONFIGURATION ---
# Left Skew context: High mean, "hump" is near the right, tail to the left.
TARGET_MEAN = 48    # Most people take around 48 seconds
TARGET_STD  = 10    # Spread of results
SKEW        = -0.6  # Negative = Tail drags to the left (fast trials are rare)
MAX_TIME    = 60

# --- EXECUTION ---
model = TrialTimeModel(TARGET_MEAN, TARGET_STD, SKEW, time_limit=MAX_TIME)

# 1. Generate the theoretical curve (PDF)
x = np.linspace(0, 70, 500) # Go past 60 to show the cutoff visually
pdf = model.get_pdf(x)

# 2. Simulate 5000 actual trials
simulated_data = model.generate_trials(n_trials=5000)

# --- PLOTTING ---
plt.figure(figsize=(10, 6))

# Plot Histogram of simulated trials
plt.hist(simulated_data, bins=50, density=True, alpha=0.4, color='gray', label='Simulated Trials')

# Plot Theoretical Curve
plt.plot(x, pdf, color='blue', linewidth=2.5, label='Model Probability')

# Visual Guides
plt.axvline(MAX_TIME, color='red', linestyle='--', linewidth=2, label='60s Limit')
plt.axvline(np.mean(simulated_data), color='green', linestyle=':', label='Actual Mean')

plt.title(f"Distribution of Trial Times (Max 60s)\nSkew: {SKEW} (Left Skew)")
plt.xlabel("Time (seconds)")
plt.ylabel("Probability Density")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(0, 65)
plt.show()