import csv

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
        for word in sorted(base_words):
            writer.writerow([word])

def find_base_word(word, base_words):
    for base in base_words:
        if word == base or word.startswith(base):
            return base
    return word

if __name__ == "__main__":
    input_file = "big_dictionary.csv"  # Replace with your input CSV file path
    output_file = "cleaned_dictionary.csv"  # Replace with your desired output file path
    clean_dictionary(input_file, output_file)