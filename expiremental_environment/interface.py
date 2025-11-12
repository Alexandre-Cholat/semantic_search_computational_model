# interface officielle avec un csv par participant, sauvegarde automatique dans dossier results

import tkinter as tk
import time
import csv
import random
import os
from datetime import datetime


class DictionnaireApp:
    def __init__(self, root, mots):
        self.root = root
        self.mots = mots
        self.index = 0
        self.start_time = None
        self.participant_number = None
        self.current_target_index = 0
        self.target_words = []
        self.current_experiment_data = []  # Store [position, time] pairs
        self.experiment_start_time = None
        self.csv_file = None
        self.csv_writer = None
        self.last_direction = None  # 'left', 'right', or None
        self.last_position = None  # Track last position for direction detection

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

        # Create new CSV file for this run
        timestamp = datetime.now().strftime("%H%M%S")
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"p{self.participant_number}-{timestamp}.csv")
        self.csv_file = open(filename, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)
        # Write header if needed
        self.csv_writer.writerow(["participant_number", "target_word", "target_word_pos", "position_time_pairs"])

        # Hardcoded target words, randomized each run
        all_targets = ["damasquinerie", "dindon", "dame", "rouillures", "récurrence", "raison",
                       "vulvaires", "vestiaires", "voiture", "guerre", "gaspillages", "galonner"]
        available_targets = [w for w in all_targets if w in self.mots]
        missing_targets = [w for w in all_targets if w not in self.mots]
        if not available_targets:
            tk.Label(self.frame_setup, text="⚠️ Aucun des mots-cibles n'est présent dans le dictionnaire.", fg="red", font=("Helvetica", 12)).pack()
            return
        if missing_targets:
            # Show a one-time notice; experiment can proceed with available targets
            tk.Label(self.frame_setup, text=f"ℹ️ Mots absents ignorés: {', '.join(missing_targets)}", fg="orange", font=("Helvetica", 10)).pack()
        self.target_words = random.sample(available_targets, len(available_targets))
        self.current_target_index = 0
        self.last_direction = None
        self.last_position = None
        self.clear_window()
        self.build_experiment_ui()

    # ----------- Screen 2 : experiment UI ------------
    def build_experiment_ui(self):
        self.label_instruction = tk.Label(self.root, text="", font=("Helvetica", 24, "bold"))
        self.label_instruction.pack(pady=10)

        # Center first letter by adding left padding
        from tkinter import font as tkFont
        screen_width = 650  # matches self.root.geometry
        word = self.mots[self.index]
        label_font = tkFont.Font(family="Helvetica", size=28)
        # Measure width of first letter
        first_letter_width = label_font.measure(word[0]) if word else 0
        # Calculate left padding so first letter is centered
        left_pad = int(screen_width / 2 - first_letter_width / 2)
        self.label = tk.Label(self.root, text=word, font=("Helvetica", 28), anchor="w", justify="left", padx=left_pad)
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

        # Track word viewing time
        self.current_word_start_time = None
        self.word_view_times = {}  # Track viewing time per word
        self.last_position_update_time = None
        
        self.load_next_target()

    def jump_to_click(self, event):
        scale = event.widget
        min_v = int(scale["from"]) if "from" in scale.keys() else 0
        max_v = int(scale["to"]) if "to" in scale.keys() else len(self.mots) - 1
        width = max(scale.winfo_width(), 1)
        new_val = min_v + int((max_v - min_v) * event.x / width)
        # clamp
        new_val = max(min_v, min(max_v, new_val))
        scale.set(new_val)
        self.scroll_to(new_val)

    # ----------- Experiment logic ------------
    def load_next_target(self):
        if self.current_target_index >= len(self.target_words):
            self.show_end_screen()
            return

        # Reset to first dictionary word when starting new target
        self.index = 0
        self.label.config(text=self.mots[self.index])
        self.scroll.set(self.index)
        
        self.target_word = self.target_words[self.current_target_index]
        # Reset experiment data for new target word
        self.current_experiment_data = []
        self.experiment_start_time = None
        self.last_direction = None
        self.last_position = self.index  # Set to current position
        
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
        self.update_word_view_time()
        self.detect_direction_change(-1)  # Moving left
        self.index = max(0, self.index - 1)
        self.label.config(text=self.mots[self.index])
        self.scroll.set(self.index)
        self.current_word_start_time = time.time()

    def next_word(self):
        self.update_word_view_time()
        self.detect_direction_change(1)  # Moving right
        self.index = min(len(self.mots) - 1, self.index + 1)
        self.label.config(text=self.mots[self.index])
        self.scroll.set(self.index)
        self.current_word_start_time = time.time()

    def scroll_to(self, val):
        self.update_word_view_time()
        new_index = int(val)
        # Detect direction based on position change
        if self.last_position is not None:
            direction = 1 if new_index > self.last_position else -1 if new_index < self.last_position else 0
        else:
            direction = 0
        self.index = new_index
        if direction != 0:
            self.detect_direction_change(direction)
        self.label.config(text=self.mots[self.index])
        self.current_word_start_time = time.time()

    def detect_direction_change(self, current_direction):
        """Detect if the participant changed direction and log the position"""
        if self.experiment_start_time is None:
            return
            
        current_time = time.time()
        direction_name = "left" if current_direction == -1 else "right"
        
        # Check if direction changed
        if self.last_direction is not None and self.last_direction != direction_name:
            # Direction changed! Log this position even if <1 second
            target_pos = self.mots.index(self.target_word) if self.target_word in self.mots else -1
            relative_position = self.index - target_pos
            time_from_start = round(current_time - self.experiment_start_time, 2)
            
            # Add to experiment data (simple [position, time] tuple, no marker)
            self.current_experiment_data.append([relative_position, time_from_start])
            
            # Update last position update time
            self.last_position_update_time = current_time
        
        # Update direction and position tracking
        self.last_direction = direction_name
        self.last_position = self.index

    def update_word_view_time(self):
        """Update viewing time for current word and log position if viewed for more than 1 second"""
        if self.current_word_start_time is not None and self.experiment_start_time is not None:
            current_time = time.time()
            view_duration = current_time - self.current_word_start_time
            
            if view_duration >= 1.0:  # Only log if viewed for at least 1 second
                # Calculate position relative to target word
                target_pos = self.mots.index(self.target_word) if self.target_word in self.mots else -1
                current_pos = self.index
                relative_position = current_pos - target_pos
                
                # Calculate time relative to experiment start
                time_from_start = round(current_time - self.experiment_start_time, 2)
                
                # Add to experiment data
                self.current_experiment_data.append([relative_position, time_from_start])
                
                # Update last position update time
                self.last_position_update_time = current_time
        
        # Reset for next word
        self.current_word_start_time = time.time()

    def start_timer(self):
        self.start_time = time.time()
        self.experiment_start_time = time.time()  # Start of experiment for this target word
        self.current_word_start_time = time.time()  # Start viewing current word
        self.current_experiment_data = []  # Reset data for new experiment
        self.last_direction = None  # Reset direction tracking
        self.last_position = self.index  # Set initial position
        self.feedback.config(text=f"⏱️ Recherche du mot « {self.target_word} » en cours...", fg="black")

    def stop_timer(self):
        if not self.start_time:
            self.feedback.config(text="⚠️ Appuyez sur 'Commencer' avant.", fg="red")
            return

        # Update final word view time
        self.update_word_view_time()

        elapsed = round(time.time() - self.start_time, 2)
        mot_trouve = self.mots[self.index]
        erreur = "non" if mot_trouve == self.target_word else "oui"

        # Find target word position in dictionary
        target_word_pos = self.mots.index(self.target_word) if self.target_word in self.mots else -1

        # Write to the participant-specific CSV file
        if self.csv_writer:
            self.csv_writer.writerow([
                self.participant_number,
                self.target_word,
                target_word_pos,
                self.current_experiment_data
            ])
            self.csv_file.flush()  # Ensure data is written immediately

        if erreur == "oui":
            self.feedback.config(text=f"⚠️ Mauvais mot : {mot_trouve} (le chrono continue)", fg="orange")
            return  # continue until correct word
        else:
            self.feedback.config(text=f"✅ Mot trouvé en {elapsed} sec.", fg="green")
            self.current_target_index += 1
            self.root.after(1000, self.load_next_target)

    # ----------- End screen ------------
    def show_end_screen(self):
        # Close the CSV file
        if self.csv_file:
            self.csv_file.close()
            
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
    # Load dictionary words as list from CSV
    mots = []
    with open("petit_dictionaire.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        mots = [row[0].strip() for row in reader if row and len(row) > 0 and row[0].strip()]

    root = tk.Tk()
    app = DictionnaireApp(root, mots)
    root.mainloop()