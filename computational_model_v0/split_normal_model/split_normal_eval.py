import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from split_normal_model import TrialTimeModel, calculate_parameters # Assuming your class is in split_normal_model.py

def run_evaluation(data_path, frequency_labels=['high', 'med', 'low'], x_limit=70):
    """
    Evaluates the model across multiple frequency groups and generates 
    a comparative visualization with Distribution and QQ-plots.
    """
    fig, axes = plt.subplots(len(frequency_labels), 2, figsize=(15, 5 * len(frequency_labels)))
    
    # Handle single frequency case for indexing
    if len(frequency_labels) == 1:
        axes = np.expand_dims(axes, axis=0)

    for i, freq in enumerate(frequency_labels):
        try:
            # 1. Setup Model (Assuming starting_pos 10 as baseline)
            mean, std, skew = calculate_parameters(freq, 10)
            model = TrialTimeModel(mean, std, skew)
            
            # 2. Load and Filter Data
            df = model.load_trial_data(data_path)
            filtered_df = model.dataLoader(df, freq)
            actual_times = np.sort(filtered_df['total_time'].dropna().values)
            
            if len(actual_times) == 0:
                print(f"No data found for {freq}")
                continue

            # 3. Calculate Distribution and Quantiles
            x_plot = np.linspace(0, x_limit, 500)
            pdf_model = model.get_pdf(x_plot)
            cdf_model = np.cumsum(pdf_model)
            cdf_model /= cdf_model[-1]
            
            percentiles = np.linspace(0, 1, 100)
            model_quantiles = np.interp(percentiles, cdf_model, x_plot)
            data_quantiles = np.percentile(actual_times, percentiles * 100)
            
            rmse = np.sqrt(np.mean((model_quantiles - data_quantiles)**2))

            # --- PLOT 1: Distribution Fit ---
            ax_dist = axes[i, 0]
            ax_dist.hist(actual_times, bins=30, density=True, alpha=0.3, color='gray', label='Test Data')
            ax_dist.plot(x_plot, pdf_model, color='blue', lw=2, label='Model PDF')
            ax_dist.set_title(f"Group: {freq.upper()} | Distribution Fit")
            ax_dist.set_xlabel("Seconds")
            ax_dist.legend()

            # --- PLOT 2: QQ Plot (Quantile Comparison) ---
            ax_qq = axes[i, 1]
            ax_qq.scatter(model_quantiles, data_quantiles, alpha=0.6, color='blue', s=20)
            # 45-degree line (Ideal Fit)
            lims = [0, x_limit]
            ax_qq.plot(lims, lims, 'r--', alpha=0.75, zorder=0, label='Perfect Fit')
            ax_qq.set_title(f"QQ Plot | RMSE: {rmse:.2f}s")
            ax_qq.set_xlabel("Model Predicted Quantiles (s)")
            ax_qq.ylabel("Actual Data Quantiles (s)")
            ax_qq.set_xlim(lims)
            ax_qq.set_ylim(lims)
            ax_qq.grid(True, alpha=0.2)
            ax_qq.legend()

            print(f"Evaluated {freq}: RMSE = {rmse:.2f}s")

        except Exception as e:
            print(f"Could not evaluate {freq}: {e}")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Point this to your new test/evaluation data
    TEST_DATA_PATH = "C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data\\semantic_search_test_data.pkl"
    run_evaluation(TEST_DATA_PATH)