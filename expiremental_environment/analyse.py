import pandas as pd
import ast
import numpy as np
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(SCRIPT_DIR, 'experiments.csv')

# Mapping des fréquences (0: Commun, 1: Moyen, 2: Rare)
FREQ_MAP = {
    "dame": 0, "guerre": 0, "raison": 0, "voiture": 0,
    "dindon": 1, "gaspillages": 1, "récurrence": 1, "vestiaires": 1,
    "damasquinerie": 2, "galonner": 2, "rouillures": 2, "vulvaires": 2
}

def modele_cognitif_frequence():
    if not os.path.exists(FILE_NAME):
        print(f"Fichier {FILE_NAME} manquant.")
        return

    df = pd.read_csv(FILE_NAME)
    df['position_time_pairs'] = df['position_time_pairs'].apply(ast.literal_eval)

    # --- A. EXTRACTION DES PARAMÈTRES ---
    delays = [p[0][1] for p in df['position_time_pairs'] if len(p) > 0]
    A_mean = np.mean(delays)
    
    errors = [abs(p[1][0]) for p in df['position_time_pairs'] if len(p) >= 2]
    SIGMA = np.std(errors) if errors else 500

    # --- B. LE MODÈLE AVEC FRÉQUENCE ---
    def simulate_search(target_pos, word):
        # 1. Temps de mouvement (Loi de Fitts)
        t_mouvement = 0.5 * np.log2(abs(target_pos) / 100 + 1) if abs(target_pos) > 0 else 0
        
        # 2. Saut initial (Imprécision)
        landing_point = np.random.normal(0, SIGMA)
        
        # 3. Coût de vérification modulé par la Fréquence
        # On récupère le niveau (0, 1 ou 2). Si absent, on met 1 par défaut.
        f_level = FREQ_MAP.get(word, 1)
        
        # Le coût de base (0.8s) augmente si le mot est rare
        cout_par_essai = 0.6 + (f_level * 0.25) 
        
        nb_essais = abs(landing_point) / 70 
        
        # Ton équation avec tes +5s de vérification finale
        return A_mean + 4 + t_mouvement + (cout_par_essai * nb_essais)

    # --- C. EXÉCUTION ---
    human_times = [p[-1][1] for p in df['position_time_pairs']]
    model_times = [simulate_search(row['target_word_pos'], row['target_word']) for _, row in df.iterrows()]

    # --- D. CALCUL RMSE & GRAPHIQUE ---
    rmse = np.sqrt(np.mean((np.sort(human_times) - np.sort(model_times))**2))
    
    plt.figure(figsize=(10, 6))
    max_time = max(max(human_times), max(model_times))
    bins = np.linspace(0, max_time, 30)
    
    plt.hist(human_times, bins=bins, alpha=0.5, label='Humains (Réel)', color='blue', edgecolor='black')
    plt.hist(model_times, bins=bins, alpha=0.5, label='Modèle (Fréquence + Chunking)', color='red', edgecolor='black')
    
    plt.text(max_time*0.6, plt.gca().get_ylim()[1]*0.8, f'RMSE: {rmse:.2f}s', 
             fontsize=14, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))
    
    plt.title('Modèle Cognitif UGA : Impact de la Fréquence Lexicale')
    plt.xlabel('Temps de recherche total (s)')
    plt.ylabel('Nb d\'essais')
    plt.legend()
    
    plt.savefig(os.path.join(SCRIPT_DIR, 'comparaison_frequence.png'))
    print(f"RMSE Final : {rmse:.2f}s")

if __name__ == "__main__":
    modele_cognitif_frequence()