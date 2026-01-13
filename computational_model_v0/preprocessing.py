import pandas as pd
import ast
import numpy as np
from sklearn.preprocessing import StandardScaler

def parse_position_time_pairs(pairs_str):
    """Parse the string representation of position-time pairs"""
    return ast.literal_eval(pairs_str)

def extract_search_features(row):
    """Extract features from position-time pairs"""
    pairs = parse_position_time_pairs(row['position_time_pairs'])
    positions = np.array([p[0] for p in pairs])
    times = np.array([p[1] for p in pairs])
    
    features = {
        'search_duration': times[-1] - times[0],
        'num_steps': len(pairs),
        'final_position': positions[-1],
        'initial_position': positions[0],
        'total_distance_traveled': np.sum(np.abs(np.diff(positions))),
        'avg_speed': np.mean(np.abs(np.diff(positions)) / np.diff(times)) if len(times) > 1 else 0,
        'max_speed': np.max(np.abs(np.diff(positions)) / np.diff(times)) if len(times) > 1 else 0,
        'position_variance': np.var(positions),
        'time_variance': np.var(times),
        'search_efficiency': abs(positions[0]) / (times[-1] - times[0]) if times[-1] > times[0] else 0,
        'hesitation_ratio': len([p for p in positions if abs(p) < 100]) / len(positions),
        'overshoot_count': len([i for i in range(1, len(positions)) 
                              if np.sign(positions[i]) != np.sign(positions[i-1])])
    }
    return features