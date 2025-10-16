import tkinter as tk
import time
import csv
import random
from difflib import get_close_matches

class DictionnaireApp:
    def __init__(self, root, mots):
        self.root = root
        self.mots = mots
        self.index = 0
        self.start_time = None
        self.participant_number = None
        self.current_target_index = 0
        self.target_words = []

        self.root.title("Expérience de recherche lexicale")
        self.root.geometry("650x500")

        # Show the participant setup screen first
        self.setup_screen()
        # Bind keyboard arrow keys globally
        self.root.bind("<Left>", lambda event: self.prev_word())
        self.root.bind("<Right>", lambda event: self.next_word())

    # ----------- Screen 1 : participant setup ------------
    def setup_screen(self):
        self.clear_window()
        self.frame_setup = tk.Frame(self.root)
        self.frame_setup.pack(expand=True)

        label = tk.Label(self.frame_setup, text="Entrez le numéro du participant :", font=("Helvetica", 16))
        label.pack(pady=20)

        self.participant_entry = tk.Entry(self.frame_setup, font=("Helvetica", 14), justify="center")
        self.participant_entry.pack(pady=10)
        # Allow pressing Enter to start
        self.participant_entry.bind("<Return>", lambda event: self.start_experiment())

        start_button = tk.Button(self.frame_setup, text="Démarrer l'expérience", font=("Helvetica", 14, "bold"),
                                 bg="#4CAF50", fg="black", width=25, height=2, command=self.start_experiment)
        start_button.pack(pady=40)

    # ----------- Start experiment ------------
    def start_experiment(self):
        try:
            self.participant_number = int(self.participant_entry.get().strip())
        except ValueError:
            tk.Label(self.frame_setup, text="⚠️ Entrez un numéro valide !", fg="red", font=("Helvetica", 12)).pack()
            return

        # Hardcoded 12 target words, randomized each run
        all_targets = ["abandon", "abeille", "acheter", "amour", "article",
                       "acteur", "accident", "appeler", "analyser", "allumer",
                       "aimer", "abricot"]
        self.target_words = random.sample(all_targets, len(all_targets))
        self.current_target_index = 0
        self.clear_window()
        self.build_experiment_ui()

    # ----------- Screen 2 : experiment UI ------------
    def build_experiment_ui(self):
        self.label_instruction = tk.Label(self.root, text="", font=("Helvetica", 24, "bold"))
        self.label_instruction.pack(pady=10)

        # Current dictionary word
        self.label = tk.Label(self.root, text=self.mots[self.index], font=("Helvetica", 28))
        self.label.pack(pady=30)

        # Navigation buttons
        frame = tk.Frame(self.root)
        frame.pack()
        tk.Button(frame, text="← Précédent", width=12, bg="#1976D2", fg="black",
                  font=("Helvetica", 12, "bold"), command=self.prev_word).pack(side=tk.LEFT, padx=10)
        tk.Button(frame, text="Suivant →", width=12, bg="#1976D2", fg="black",
                  font=("Helvetica", 12, "bold"), command=self.next_word).pack(side=tk.LEFT, padx=10)

        # Scroll bar
        self.scroll = tk.Scale(self.root, from_=0, to=len(self.mots)-1, orient=tk.HORIZONTAL,
                               length=500, command=self.scroll_to)
        self.scroll.pack(pady=20)
        # Allow clicking anywhere on the scale to jump to that value
        self.scroll.bind("<Button-1>", self.jump_to_click)

        # Control buttons
        self.btn_start = tk.Button(self.root, text="Commencer", bg="#4CAF50", fg="black",
                                   font=("Helvetica", 12, "bold"), width=15, command=self.start_timer)
        self.btn_start.pack(pady=5)
        self.btn_stop = tk.Button(self.root, text="Trouvé", bg="#E53935", fg="black",
                                  font=("Helvetica", 22, "bold"), width=15, command=self.stop_timer)
        self.btn_stop.pack(pady=5)

        # Feedback label
        self.feedback = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.feedback.pack(pady=10)

        self.load_next_target()

    def jump_to_click(self, event):
        # Compute the new value based on where the user clicked
        # Works only for horizontal scale
        scale = event.widget
        new_val = int(scale["from"]) + int((int(scale["to"]) - int(scale["from"])) * event.x / scale.winfo_width())
        scale.set(new_val)
        self.scroll_to(new_val)

    # ----------- Experiment logic ------------
    def load_next_target(self):
        if self.current_target_index >= len(self.target_words):
            self.show_end_screen()
            return

        self.target_word = self.target_words[self.current_target_index]
        # Make the instruction text larger and the word even bigger and bold
        instruction_text = f"🔍 Trouvez le mot : "
        # Use a separate label for the word to allow different font size
        self.label_instruction.config(text=instruction_text)
        # If a previous target_word_label exists, destroy it
        if hasattr(self, 'target_word_label') and self.target_word_label.winfo_exists():
            self.target_word_label.destroy()
        self.target_word_label = tk.Label(self.root, text=f"« {self.target_word} »", font=("Helvetica", 36, "bold"), fg="#E53935")
        self.target_word_label.pack()
        self.feedback.config(text="")
        self.start_time = None

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
        self.start_time = time.time()
        self.feedback.config(text=f"⏱️ Recherche du mot « {self.target_word} » en cours...", fg="black")

    def stop_timer(self):
        if not self.start_time:
            self.feedback.config(text="⚠️ Appuyez sur 'Commencer' avant.", fg="red")
            return

        elapsed = round(time.time() - self.start_time, 2)
        mot_trouve = self.mots[self.index]
        erreur = "non" if mot_trouve == self.target_word else "oui"

        with open("resultats.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([self.participant_number, self.target_word, mot_trouve,
                             erreur, elapsed, time.strftime('%H:%M:%S')])

        if erreur == "oui":
            self.feedback.config(text=f"⚠️ Mauvais mot : {mot_trouve} (le chrono continue)", fg="orange")
            return  # continue until correct word
        else:
            self.feedback.config(text=f"✅ Mot trouvé en {elapsed} sec.", fg="green")
            self.current_target_index += 1
            self.root.after(1000, self.load_next_target)

    # ----------- End screen ------------
    def show_end_screen(self):
        self.clear_window()
        done_label = tk.Label(self.root, text="🎉 Expérience terminée !", font=("Helvetica", 24, "bold"))
        done_label.pack(pady=50)

        next_button = tk.Button(self.root, text="Participant suivant", bg="#4CAF50", fg="white",
                                font=("Helvetica", 16, "bold"), width=20, height=2,
                                command=self.restart_experiment)
        next_button.pack(pady=30)

    def restart_experiment(self):
        self.clear_window()
        self.setup_screen()

    # ----------- Utility ------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
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