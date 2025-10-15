import tkinter as tk
import time
import csv
from difflib import get_close_matches

class DictionnaireApp:
    def __init__(self, root, mots):
        self.root = root
        self.mots = mots
        self.index = 0
        self.start_time = None
        self.target_word = None
        self.participant_name = None



        self.root.title("Recherche dans le dictionnaire")
        self.root.geometry("550x450")

        # Entrée nom du participant
        self.name_label = tk.Label(root, text="Nom du participant :", font=("Helvetica", 12))
        self.name_label.pack()
        self.name_entry = tk.Entry(root, font=("Helvetica", 12))
        self.name_entry.pack(pady=5)

        # Label affichant le mot courant
        self.label = tk.Label(root, text=self.mots[self.index], font=("Helvetica", 28))
        self.label.pack(pady=30)

        # Barre de navigation
        frame = tk.Frame(root)
        frame.pack()
        tk.Button(frame, text="← Précédent", width=12, command=self.prev_word).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="Suivant →", width=12, command=self.next_word).pack(side=tk.LEFT, padx=10)

        # Barre de défilement
        self.scroll = tk.Scale(root, from_=0, to=len(self.mots)-1, orient=tk.HORIZONTAL,
                               length=400, command=self.scroll_to)
        self.scroll.pack(pady=20)

        # Zone d'entrée du mot cible
        self.entry_label = tk.Label(root, text="Mot à rechercher :", font=("Helvetica", 12))
        self.entry_label.pack()
        self.entry = tk.Entry(root, font=("Helvetica", 12))
        self.entry.pack(pady=5)

        # Boutons chrono
        self.btn_start = tk.Button(root, text="Commencer", bg="#4CAF50", fg="black", command=self.start_timer)
        self.btn_start.pack(pady=5)
        self.btn_stop = tk.Button(root, text="Trouvé", bg="#f44336", fg="black", command=self.stop_timer)
        self.btn_stop.pack(pady=5)

        # Label de feedback
        self.feedback = tk.Label(root, text="", font=("Helvetica", 12))
        self.feedback.pack(pady=10)

    def prev_word(self):
        self.index = max(0, self.index - 1)
        self.label.config(text=self.mots[self.index])
        self.scroll.set(self.index)

    def next_word(self):
        self.index = min(len(self.mots) - 1, self.index + 1)
        self.label.config(text=self.mots[self.index])
        self.scroll.set(self.index)

    def scroll_to(self, val):
        self.index = int(val)
        self.label.config(text=self.mots[self.index])

    def start_timer(self):
        mot = self.entry.get().strip().lower()
        if not mot:
            self.feedback.config(text="⚠️ Entrez d'abord un mot à rechercher.", fg="red")
            return
        if mot not in self.mots:
            suggestion = get_close_matches(mot, self.mots, n=1)
            suggestion_txt = f" (peut-être vouliez-vous dire '{suggestion[0]}')" if suggestion else ""
            self.feedback.config(text=f"❌ Le mot '{mot}' n'existe pas dans le dictionnaire.{suggestion_txt}", fg="red")
            return

        self.target_word = mot
        self.start_time = time.time()
        self.feedback.config(text=f"⏱️ Recherche du mot « {mot} » en cours...", fg="black")

    def stop_timer(self):
        if not self.start_time:
            self.feedback.config(text="⚠️ Appuyez sur 'Commencer' avant.", fg="red")
            return

        elapsed = round(time.time() - self.start_time, 2)
        mot_trouve = self.mots[self.index]

        participant = self.name_entry.get().strip() or "Anonyme"

        # Cas d'erreur : mauvais mot
        if mot_trouve != self.target_word:
            erreur = "oui"
            message = f"⚠️ Erreur : mot '{mot_trouve}' au lieu de '{self.target_word}'. Temps = {elapsed}s (chronomètre continue)"
            self.feedback.config(text=message, fg="orange")
            with open("resultats.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([participant, self.target_word, mot_trouve, erreur, elapsed, time.strftime('%H:%M:%S')])
            return  # ne pas arrêter le chrono

        # Cas correct : bon mot
        erreur = "non"
        message = f"✅ Mot trouvé en {elapsed} sec."
        self.feedback.config(text=message, fg="green")
        with open("resultats.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([participant, self.target_word, mot_trouve, erreur, elapsed, time.strftime('%H:%M:%S')])

        # Stop le chrono
        self.start_time = None

if __name__ == "__main__":
    # Mini dictionnaire de test
    mots = [
        "abaisser", "abandon", "abattre", "abeille", "abolir",
        "abricot", "absence", "accident", "accorder", "acheter",
        "acteur", "admirer", "affaire", "agacer", "aider",
        "aimer", "ajouter", "alarme", "aller", "allumer",
        "amener", "amour", "analyser", "animal", "année",
        "appeler", "apporter", "apprendre", "arriver", "article"
    ]

    root = tk.Tk()
    app = DictionnaireApp(root, mots)
    root.mainloop()