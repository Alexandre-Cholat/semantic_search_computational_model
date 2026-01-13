import numpy as np
import matplotlib.pyplot as plt

def split_normal_model(x, target_mean, target_std, skew_intensity):
    """
    Generates a PDF using the Split Normal (Two-Piece) method.
    
    Parameters:
    - skew_intensity: float between -0.99 and 0.99. 
      Negative = Left Skew (Long tail left)
      Positive = Right Skew (Long tail right)
    """
    
    # 1. Heuristic Mapping
    # We split the total standard deviation into Left and Right based on skew intensity.
    # If skew is negative (left), we make sigma_left larger.
    
    sigma_L = target_std * (1 - skew_intensity)
    sigma_R = target_std * (1 + skew_intensity)
    
    # We need to shift the mode (peak) so the *mathematical mean* lands where you want it.
    # For a Split Normal, Mean = Mode + sqrt(2/pi)*(sigma_R - sigma_L)
    shift_correction = np.sqrt(2/np.pi) * (sigma_R - sigma_L)
    mode = target_mean - shift_correction

    # 2. The Modified Gaussian Function
    # We use numpy.where to switch sigmas based on x position relative to mode
    sigma_x = np.where(x < mode, sigma_L, sigma_R)
    
    # The Normalization Constant A
    A = np.sqrt(2/np.pi) / (sigma_L + sigma_R)
    
    # Calculate PDF
    pdf = A * np.exp(-(x - mode)**2 / (2 * sigma_x**2))
    
    return pdf

# --- CONFIGURATION ---
MEAN = 25
STD = 10
SKEW_INTENSITY = 0.2  # Positive for Right Skew

# --- EXECUTION ---
x = np.linspace(0, 80, 1000)
y = split_normal_model(x, MEAN, STD, SKEW_INTENSITY)

# Plot
plt.plot(x, y, linewidth=2, label=f"Skew: {SKEW_INTENSITY}")
plt.axvline(MEAN, color='r', linestyle='--', alpha=0.5, label='Target Mean')

# Visual Check
plt.title("Split Normal (Modified Gaussian)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()