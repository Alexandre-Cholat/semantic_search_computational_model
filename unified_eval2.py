import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import ast

# --- CONFIGURATION ---
DATA_PATH = r'C:\Users\alexa\OneDrive\Documents\tech-projects\semantic_search_data\semantic_search_train_data.pkl'
FREQ_MAP = {
    "dame": 0, "guerre": 0, "raison": 0, "voiture": 0,
    "dindon": 1, "gaspillages": 1, "récurrence": 1, "vestiaires": 1,
    "damasquinerie": 2, "galonner": 2, "rouillures": 2, "vulvaires": 2
}

# --- MODEL 1: THEORETICAL PARAMETERS ---
def get_m1_params(frequency):
    """Returns (mean, std, skew) based on frequency category."""
    if frequency == 'high': return 19, 5.5, 0.8
    if frequency == 'med':  return 22, 7.5, 0.6
    return 25, 8.5, 0.7  # low

class SplitNormalModel:
    def __init__(self, mean, std, skew):
        self.mean, self.std, self.skew = mean, std, skew
        self.sigma_L = std * (1 - skew)
        self.sigma_R = std * (1 + skew)
        shift = np.sqrt(2/np.pi) * (self.sigma_R - self.sigma_L)
        self.mode = mean - shift
        self.A = np.sqrt(2/np.pi) / (self.sigma_L + self.sigma_R)

    def get_pdf(self, x):
        sigma_x = np.where(x < self.mode, self.sigma_L, self.sigma_R)
        y = self.A * np.exp(-(x - self.mode)**2 / (2 * sigma_x**2))
        y[x < 0] = 0
        return y

# --- MODEL 2: COGNITIVE SIMULATION ---
def simulate_search(target_pos, word, A_mean, SIGMA):
    t_mouvement = 0.5 * np.log2(abs(target_pos) / 100 + 1) if abs(target_pos) > 0 else 0
    f_level = FREQ_MAP.get(word, 1)
    cout_par_essai = 0.6 + (f_level * 0.25) 
    landing_point = np.random.normal(0, SIGMA)
    nb_essais = abs(landing_point) / 70 
    return A_mean + 4 + t_mouvement + (cout_par_essai * nb_essais)

# --- EXECUTION ---
def run_global_mixture_eval():
    if not os.path.exists(DATA_PATH): return print("File not found.")

    # 1. Load Data
    df = pd.read_pickle(DATA_PATH)
    if 'target_word' not in df.columns: df = df.reset_index()
    if 'total_time' not in df.columns:
        df['total_time'] = df['clean_traces'].apply(lambda x: x[-1][1] if len(x)>0 else 0)
    
    # 2. Preparation
    df['clean_word'] = df['target_word'].astype(str).str.replace('Ã©', 'é', regex=False).str.strip().str.lower()
    human_times = np.sort(df['total_time'].dropna().values)
    x_plot = np.linspace(0, 80, 1000)
    
    # 3. Build Mixture Model 1 (Weighted Theoretical Curve)
    global_pdf_m1 = np.zeros_like(x_plot)
    counts = {0: 0, 1: 0, 2: 0} # Track N for weighting
    
    # 4. Run Simulation Model 2 (Individual Trials)
    m2_times = []
    A_mean = np.mean(human_times) * 0.1
    SIGMA = 500

    for _, row in df.iterrows():
        word = row['clean_word']
        f_code = FREQ_MAP.get(word, -1)
        if f_code == -1: continue
        
        counts[f_code] += 1
        m2_times.append(simulate_search(10, word, A_mean, SIGMA))

    # Calculate M1 Weighted PDF
    total_n = sum(counts.values())
    for code, label in zip([0, 1, 2], ['high', 'med', 'low']):
        weight = counts[code] / total_n
        m, s, sk = get_m1_params(label)
        global_pdf_m1 += weight * SplitNormalModel(m, s, sk).get_pdf(x_plot)

    # 5. RMSE CALCULATION (Quantile-Based)
    percentiles = np.linspace(0, 1, 100)
    human_q = np.percentile(human_times, percentiles * 100)
    
    # M1 Quantiles
    cdf_m1 = np.cumsum(global_pdf_m1)
    cdf_m1 /= cdf_m1[-1]
    m1_q = np.interp(percentiles, cdf_m1, x_plot)
    rmse_m1 = np.sqrt(np.mean((m1_q - human_q)**2))
    
    # M2 Quantiles
    m2_times = np.sort(np.array(m2_times))
    m2_q = np.percentile(m2_times, percentiles * 100)
    rmse_m2 = np.sqrt(np.mean((m2_q - human_q)**2))

    # --- PLOTTING ---
    plt.figure(figsize=(12, 7))
    plt.hist(human_times, bins=40, density=True, alpha=0.3, color='gray', label='Human Data (All Freq)')
    
    # Model 1: The Aggregate Theoretical Mixture Curve
    plt.plot(x_plot, global_pdf_m1, color='blue', lw=3, label=f'Model 1: Theoretical Mixture (RMSE: {rmse_m1:.2f}s)')
    
    # Model 2: The Aggregate Simulation Histogram
    plt.hist(m2_times, bins=40, density=True, histtype='step', color='red', lw=2.5, label=f'Model 2: Cognitive Sim (RMSE: {rmse_m2:.2f}s)')
    
    plt.title("Global Model Comparison: Theoretical Mixture vs. Cognitive Simulation", fontsize=14)
    plt.xlabel("Search Time (seconds)")
    plt.ylabel("Probability Density")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.2)
    plt.xlim(0, 75)
    
    print(f"GLOBAL RESULTS:\nModel 1 RMSE: {rmse_m1:.2f}s\nModel 2 RMSE: {rmse_m2:.2f}s")
    plt.show()

if __name__ == "__main__":
    run_global_mixture_eval()