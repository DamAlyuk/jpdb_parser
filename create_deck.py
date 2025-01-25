import json
import genanki
import os

class AnkiDeckCreator:
    def __init__(self, input_json_file, output_anki_file=None):
        self.input_json_file = input_json_file
        self.output_anki_file = output_anki_file or f"{os.path.splitext(input_json_file)[0]}.apkg"
        self.deck_name = os.path.splitext(os.path.basename(input_json_file))[0]

    def load_words(self):
        with open(self.input_json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def calculate_average_popularity(self, top_data):
        """Вычисляет среднюю популярность."""
        if not top_data:
            return "No data"

        popularity_values = []
        for category, value in top_data.items():
            try:
                popularity_values.append(float(value))
            except ValueError:
                continue

        if popularity_values:
            return round(sum(popularity_values) / len(popularity_values), 2)
        return "No data"

    def format_meanings(self, meanings):
        """Преобразует список значений в HTML-список."""
        if not meanings:
            return "<i>No meanings available</i>"
        return "<ol>" + "".join(f"<li>{meaning}</li>" for meaning in meanings) + "</ol>"

    def create_deck(self, words):
        # Создаем колоду и модель
        my_deck = genanki.Deck(
            2059400110,  # Уникальный идентификатор
            self.deck_name
        )

        my_model = genanki.Model(
            1607392319,  # Уникальный идентификатор
            'Simple Model',
            fields=[
                {'name': 'Word'},
                {'name': 'Reading'},
                {'name': 'Meanings'},
                {'name': 'AveragePopularity'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                        <div style="text-align: center; font-size: 48px; margin-top: 50px;">
                            {{Word}}
                        </div>
                        <div style="text-align: center; font-size: 20px; margin-top: 10px; color: gray; display: none;">
                            {{Reading}}
                        </div>
                    ''',
                    'afmt': '''
                        <div style="text-align: center; font-size: 48px; margin-top: 50px;">
                            {{Word}}
                        </div>
                        <div style="text-align: center; font-size: 20px; margin-top: 10px; color: gray;">
                            {{Reading}}
                        </div>
                        <div style="font-size: 18px; margin-top: 10px;">
                            {{Meanings}}
                        </div>
                        <hr>
                        <div style="font-size: 14px; margin-top: 10px; text-align: center;">Average Popularity: {{AveragePopularity}}</div>
                    ''',
                }
            ]
        )

        # Добавляем слова в колоду
        for word_entry in words:
            word = word_entry['word']
            reading = word_entry['reading']
            meanings = self.format_meanings(word_entry['meanings'])  # Преобразуем список значений в HTML
            average_popularity = self.calculate_average_popularity(word_entry['top'])

            note = genanki.Note(
                model=my_model,
                fields=[word, reading, meanings, str(average_popularity)]
            )
            my_deck.add_note(note)

        return my_deck

    def save_deck(self, deck):
        deck.write_to_file(self.output_anki_file)

    def run(self):
        words = self.load_words()
        anki_deck = self.create_deck(words)
        self.save_deck(anki_deck)
        print(f"Anki deck saved to {self.output_anki_file}")

if __name__ == '__main__':
    input_json_file = input("Enter the path to the JSON file with the vocabulary: ").strip()
    creator = AnkiDeckCreator(input_json_file)
    creator.run()
