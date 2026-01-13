import pandas as pd
import ast
import numpy as np
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
# Point this to your test data or cleaned data pickle
FILE_NAME = os.path.join(
    'C:\\Users\\alexa\\OneDrive\\Documents\\tech-projects\\semantic_search_data',
    'semantic_search_test_data.pkl'
)

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

    print(f"Chargement de {FILE_NAME}...")
    df = pd.read_pickle(FILE_NAME)

    # --- 1. ADAPTATION STRUCTURE (DATA CLEANING) ---
    
    # A. Gestion de l'index (si target_word est caché dans l'index)
    if 'target_word' not in df.columns:
        df = df.reset_index()

    # B. Identification de la colonne de traces
    trace_col = 'clean_traces' if 'clean_traces' in df.columns else 'position_time_pairs'
    print(f"Utilisation de la colonne : {trace_col}")

    # C. Conversion sécurisée des traces (si ce sont des strings)
    def safe_parse(val):
        if isinstance(val, list): return val
        if isinstance(val, str):
            try: return ast.literal_eval(val)
            except: return []
        return []

    df['traces_final'] = df[trace_col].apply(safe_parse)
    
    # D. Nettoyage des mots (encodage rÃ©currence)
    # On s'assure que 'target_word' existe, sinon on essaie 'target_wo'
    word_col = 'target_word' if 'target_word' in df.columns else 'target_wo'
    
    if word_col in df.columns:
        df['clean_word'] = df[word_col].astype(str).str.replace('Ã©', 'é').str.strip().str.lower()
    else:
        print("Erreur: Colonne 'target_word' introuvable.")
        return

    # --- 2. EXTRACTION DES PARAMÈTRES (STATISTIQUES) ---
    # Récupération des temps réels (dernier timestamp de la trace)
    # On filtre les traces vides
    valid_traces = df[df['traces_final'].map(len) > 0].copy()
    
    human_times = valid_traces['traces_final'].apply(lambda x: x[-1][1]).values
    
    # Calcul du délai initial (temps du premier point)
    delays = valid_traces['traces_final'].apply(lambda x: x[0][1] if len(x)>0 else 0).values
    A_mean = np.mean(delays) if len(delays) > 0 else 0.5
    
    # Calcul de l'erreur du premier saut (position du 2ème point vs 0)
    # On suppose que le saut vise 0 (ou le target), ici on regarde la dispersion du 2ème point
    first_jumps = valid_traces['traces_final'].apply(lambda x: x[1][0] if len(x) > 1 else np.nan).dropna()
    SIGMA = np.std(first_jumps) if len(first_jumps) > 0 else 500

    print(f"Paramètres extraits -> Délai Initial (A): {A_mean:.2f}s | Sigma Saut: {SIGMA:.2f}")

    # --- 3. DÉFINITION DU MODÈLE ---
    def simulate_search(target_pos, word):
        # 1. Temps de mouvement (Loi de Fitts simplifiée)
        # target_pos est en pixels/unités, on normalise arbitrairement par 100
        t_mouvement = 0.5 * np.log2(abs(target_pos) / 100 + 1) if abs(target_pos) > 0 else 0
        
        # 2. Saut initial (Imprécision)
        # On simule où l'utilisateur atterrit (erreur par rapport à la cible idéale ou 0)
        landing_point = np.random.normal(0, SIGMA)
        
        # 3. Coût de vérification modulé par la Fréquence
        # Lookup avec le mot nettoyé
        f_level = FREQ_MAP.get(word, 1) # 1 (Moyen) par défaut si inconnu
        
        # Modèle : Plus le mot est rare (f_level élevé), plus la vérification est longue
        # Base 0.6s + Pénalité fréquence
        cout_par_essai = 0.6 + (f_level * 0.25) 
        
        # Estimation du nombre d'essais nécessaires pour corriger l'erreur de distance
        nb_essais = abs(landing_point) / 70 
        
        return A_mean + 4 + t_mouvement + (cout_par_essai * nb_essais)

    # --- 4. SIMULATION ET COMPARAISON ---
    
    model_times = []
    
    # On itère sur les données valides pour générer les prédictions
    for _, row in valid_traces.iterrows():
        # Utilisation de target_word_pos si dispo, sinon 0
        t_pos = row['target_word_pos'] if 'target_word_pos' in row else 0
        pred_time = simulate_search(t_pos, row['clean_word'])
        model_times.append(pred_time)

    model_times = np.array(model_times)

    # --- 5. VISUALISATION ---
    
    # Calcul RMSE (Root Mean Square Error)
    # Comparaison triée (Quantile-based simple) pour comparer les distributions
    rmse = np.sqrt(np.mean((np.sort(human_times) - np.sort(model_times))**2))
    
    plt.figure(figsize=(10, 6))
    
    # Définition des bins communs
    max_val = max(np.max(human_times), np.max(model_times))
    bins = np.linspace(0, max_val, 30)
    
    plt.hist(human_times, bins=bins, alpha=0.5, label='Données Humaines', color='blue', density=True)
    plt.hist(model_times, bins=bins, alpha=0.5, label='Modèle Cognitif', color='red', density=True)
    
    # Affichage du RMSE
    plt.text(0.7, 0.8, f'RMSE Distribution: {rmse:.2f}s', 
             transform=plt.gca().transAxes, 
             fontsize=12, bbox=dict(facecolor='white', alpha=0.8, edgecolor='red'))
    
    plt.title('Validation du Modèle : Impact de la Fréquence')
    plt.xlabel('Temps Total (s)')
    plt.ylabel('Densité de probabilité')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_path = os.path.join(os.path.dirname(FILE_NAME), 'comparaison_frequence.png')
    plt.savefig(output_path)
    print(f"Graphique sauvegardé sous : {output_path}")
    print(f"RMSE Final : {rmse:.2f}s")
    plt.show()

if __name__ == "__main__":
    modele_cognitif_frequence()