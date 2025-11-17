import csv
import unicodedata

def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def clean_dictionary(input_file, output_file):
    base_words = set()

    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:  # Ensure the row is not empty
                word = row[0].strip()
                base_word = find_base_word(word, base_words)
                base_words.add(base_word)

    with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for word in sorted(base_words, key=lambda w: strip_accents(w).lower()):
            writer.writerow([word])

def find_base_word(word, base_words):
    for base in base_words:
        if word == base or word.startswith(base):
            return base
    return word

import csv

def insert_word(csv_file, new_word):
    # Read all words
    with open(csv_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f]

    # Check if exists (case-insensitive)
    if new_word.lower() in (w.lower() for w in words):
        print(f"'{new_word}' already exists.")
        return

    # Insert and sort
    words.append(new_word)
    words = sorted(words, key=lambda w: strip_accents(w).lower())

    # Write back to the file
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        for word in words:
            f.write(word + "\n")

    print(f"Inserted '{new_word}' zombie.")
    

# Example usage
#insert_word("petit_dictionaire.csv", "gars")  # Replace with your CSV file path and the word to insert
    

# if __name__ == "__main__":
#     input_file = "big_dictionary.csv"  # Replace with your input CSV file path
#     output_file = "cleaned_dictionary.csv"  # Replace with your desired output file path
#     clean_dictionary(input_file, output_file)

mots = [
    ["zombie", "gaspillages", "galonner", "yoga"],
    ["yaourt", "xylophone", "whisky", "wagon"],
    ["wifi", "boursouflés", "sorbier", "pays"],
    ["bourdon", "boursoufler", "cerisier", "présence"],
    ["bourdonner", "boursicoteurs", "pommier", "framboise"],
    ["bourdonnera", "bourse", "prunier", "fraise"],
    ["bourdonnés", "boursicoter", "poirier", "framboisier"],
    ["boursouflée", "boursicotage", "pêcher", "fraises"],
    ["boursouflent", "boursicotant", "sorbiers", "fraiseur"],
    ["boursouflera", "boursicote", "cerisiers", ""],
    ["boursouflés", "boursicotiez", "pommiers", ""],
    ["boursouflons", "boursicotons", "pruniers", ""]]

for row in mots:
    for w in row:
        if w.strip() != "":
            insert_word("petit_dictionaire.csv", w)
