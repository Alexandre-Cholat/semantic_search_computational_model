import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import ast

# --- CONFIGURATION ---
FILE_NAME = os.path.join(
    'C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data',
    'semantic_search_test_data.pkl'
)

# Frequency Map
FREQ_MAP = {
    "dame": 0, "guerre": 0, "raison": 0, "voiture": 0,
    "dindon": 1, "gaspillages": 1, "récurrence": 1, "vestiaires": 1,
    "damasquinerie": 2, "galonner": 2, "rouillures": 2, "vulvaires": 2
}

# --- MODEL 1: THEORETICAL (Split Normal) ---
class SplitNormalModel:
    def __init__(self, frequency, starting_pos):
        # Hardcoded parameters (from your previous script)
        if frequency == 'high':
            self.mean, self.std, self.skew = 19, 5.5, 0.8
        elif frequency == 'med':
            self.mean, self.std, self.skew = 22, 7.5, 0.6
        else: # low
            self.mean, self.std, self.skew = 25, 8.5, 0.7
            
        # Add position impact (simplified)
        self.mean += (starting_pos / 5000) * 20

        # Split Normal Params
        self.sigma_L = self.std * (1 - self.skew)
        self.sigma_R = self.std * (1 + self.skew)
        shift = np.sqrt(2/np.pi) * (self.sigma_R - self.sigma_L)
        self.mode = self.mean - shift
        self.A = np.sqrt(2/np.pi) / (self.sigma_L + self.sigma_R)

    def get_pdf(self, x):
        sigma_x = np.where(x < self.mode, self.sigma_L, self.sigma_R)
        y = self.A * np.exp(-(x - self.mode)**2 / (2 * sigma_x**2))
        y[x < 0] = 0
        return y

# --- MODEL 2: SIMULATION (Cognitive Process) ---
def simulate_cognitive_process(target_pos, word, A_mean, SIGMA):
    # 1. Fitts' Law
    t_mouvement = 0.5 * np.log2(abs(target_pos) / 100 + 1) if abs(target_pos) > 0 else 0
    
    # 2. Initial Jump Error
    landing_point = np.random.normal(0, SIGMA)
    
    # 3. Verification Cost
    f_level = FREQ_MAP.get(word, 1)
    cout_par_essai = 0.6 + (f_level * 0.25)
    nb_essais = abs(landing_point) / 70 
    
    return A_mean + 4 + t_mouvement + (cout_par_essai * nb_essais)

# --- COMPARISON LOGIC ---
def compare_models():
    if not os.path.exists(FILE_NAME):
        print(f"File missing: {FILE_NAME}")
        return

    print("Loading Data...")
    df = pd.read_pickle(FILE_NAME)
    
    # --- Data Cleaning ---
    if 'target_word' not in df.columns: df = df.reset_index()
    
    # Extract Traces
    col_trace = 'clean_traces' if 'clean_traces' in df.columns else 'position_time_pairs'
    def parse_trace(x):
        if isinstance(x, list): return x
        try: return ast.literal_eval(x)
        except: return []
    df['traces'] = df[col_trace].apply(parse_trace)
    
    # Extract Human Times
    df = df[df['traces'].map(len) > 0].copy()
    human_times = df['traces'].apply(lambda x: x[-1][1]).values
    
    # Extract Global Parameters for Simulation
    delays = df['traces'].apply(lambda x: x[0][1]).values
    A_mean = np.mean(delays)
    
    # Extract Jump Sigma
    first_jumps = df['traces'].apply(lambda x: x[1][0] if len(x)>1 else np.nan).dropna()
    SIGMA = np.std(first_jumps)
    
    # Normalize Words
    word_col = 'target_word' if 'target_word' in df.columns else 'target_wo'
    df['clean_word'] = df[word_col].astype(str).str.replace('Ã©', 'é').str.strip().str.lower()

    # --- GENERATE PREDICTIONS ---
    
    # 1. Run Simulation Model (Model 2)
    # We simulate one trial for every real trial to match sample size
    sim_times = []
    for _, row in df.iterrows():
        t_pos = row['target_word_pos'] if 'target_word_pos' in df.columns else 0
        sim_times.append(simulate_cognitive_process(t_pos, row['clean_word'], A_mean, SIGMA))
    sim_times = np.array(sim_times)
    
    # 2. Run Theoretical Model (Model 1)
    # We generate a PDF curve representing the "average" trial configuration
    # (Using 'med' frequency as a representative baseline for the whole dataset)
    avg_pos = df['target_word_pos'].mean() if 'target_word_pos' in df.columns else 0
    theo_model = SplitNormalModel('med', avg_pos) 

    # --- CALCULATE RMSE (Quantile-Based) ---
    percentiles = np.linspace(0, 1, 100)
    
    # Human Quantiles
    human_quantiles = np.percentile(human_times, percentiles * 100)
    
    # Model 2 (Simulation) Quantiles
    sim_quantiles = np.percentile(sim_times, percentiles * 100)
    rmse_sim = np.sqrt(np.mean((sim_quantiles - human_quantiles)**2))
    
    # Model 1 (Theoretical) Quantiles
    x_plot = np.linspace(0, max(human_times)*1.2, 1000)
    pdf_vals = theo_model.get_pdf(x_plot)
    cdf_vals = np.cumsum(pdf_vals)
    cdf_vals /= cdf_vals[-1] # Normalize to 0-1
    theo_quantiles = np.interp(percentiles, cdf_vals, x_plot)
    
    rmse_theo = np.sqrt(np.mean((theo_quantiles - human_quantiles)**2))

    # --- PLOTTING ---
    plt.figure(figsize=(12, 7))
    
    # Histogram of Human Data (Ground Truth)
    plt.hist(human_times, bins=30, density=True, color='gray', alpha=0.3, label='Human Data')
    
    # Plot Model 2 (Simulation) as a Step Histogram
    plt.hist(sim_times, bins=30, density=True, color='red', histtype='step', linewidth=2, 
             label=f'Simulation Model (RMSE: {rmse_sim:.2f}s)')
    
    # Plot Model 1 (Theoretical) as a Smooth Curve
    plt.plot(x_plot, pdf_vals, color='blue', linewidth=2.5, 
             label=f'Theoretical Model (RMSE: {rmse_theo:.2f}s)')

    plt.title("Model Comparison: Theoretical vs. Simulation")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, max(human_times))
    
    print(f"\n--- PERFORMANCE REPORT ---")
    print(f"Theoretical Model RMSE: {rmse_theo:.2f}s")
    print(f"Simulation Model RMSE:  {rmse_sim:.2f}s")
    
    winner = "Theoretical" if rmse_theo < rmse_sim else "Simulation"
    print(f"Winner: {winner} Model")
    
    plt.show()

if __name__ == "__main__":
    compare_models()