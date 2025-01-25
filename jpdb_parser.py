import requests
from bs4 import BeautifulSoup
import json
import time
from tqdm import tqdm
import re
from datetime import datetime
import random
import os

class VocabularyParser:
    def __init__(self, progress_file='progress.json'):
        self.progress_file = progress_file
        self.url = ''
        self.offset = 0
        self.offset_step = 50
        self.total_entries = 0
        self.all_vocabulary = []
        self.debug = False

    def fetch_page(self, url, headers, retries=3, timeout=2, delay=5):
        for _ in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Error while fetching {url}: {e}")
                time.sleep(delay)
        return None

    def extract_furigana(self, element):
        furigana = ''
        for ruby in element.find_all('ruby'):
            furigana += ''.join(rt.text for rt in ruby.find_all('rt'))
            furigana += ''.join(char for char in ruby.text if not ('\u4e00' <= char <= '\u9fff'))
        return furigana.strip()

    def extract_top_details(self, top_element):
        top_details = {}
        if top_element and 'data-tooltip' in top_element.attrs:
            for item in top_element['data-tooltip'].split(' '):
                if ':' in item:
                    category, value = item.split(':')
                    top_details[category.lower()] = value.strip()
        return top_details

    def extract_translations(self, top_element):
        translation_div = top_element.find_next('div') if top_element else None
        if translation_div:
            translations = translation_div.get_text(strip=True)
            return [t.strip() for t in translations.split(';') if t.strip()]
        return []

    def parse_page(self, url, offset):
        page_url = f"{url}?offset={offset}#a"
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = self.fetch_page(page_url, headers)

        if not soup:
            return [], False

        entries = soup.find_all('div', class_='entry')
        if not entries:
            return [], False

        vocabulary = []
        for idx, entry in enumerate(entries, start=1):
            word_element = entry.find('a')
            word = word_element.text.strip() if word_element else ''
            furigana = self.extract_furigana(word_element) if word_element else ''
            top_element = entry.find('div', class_='tag tooltip')
            top_details = self.extract_top_details(top_element)
            translations = self.extract_translations(top_element)

            vocabulary.append({
                'id': offset + idx,
                'word': word,
                'reading': furigana,
                'meanings': translations,
                'top': top_details,
            })

        return vocabulary, True

    def save_words_to_json(self, data, url):
        match = re.search(r'novel/[\d]+/([^/]+)', url)
        if match:
            novel_name = match.group(1).replace('-', '_')
        else:
            novel_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        filename = f"{novel_name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def save_progress_to_json(self, progress_data):
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=4)

    def load_offset(self, url):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if url in data:
                    return data[url].get('last_offset', 0)
        return 0

    def load_existing_words(self, url):
        match = re.search(r'novel/[\d]+/([^/]+)', url)
        if match:
            novel_name = match.group(1).replace('-', '_')
            filename = f"{novel_name}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return []

    def save_offset(self, url, offset):
        data = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        data[url] = {'last_offset': offset}
        self.save_progress_to_json(data)

    def save_last_url(self, url):
        data = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        data['last_url'] = url
        self.save_progress_to_json(data)

    def load_last_url(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_url', None)
        return None

    def run(self):
        last_url = self.load_last_url()
        if last_url:
            print(f"Last URL: {last_url}")
            resume = input("Do you want to continue from the last URL? (y/n): ").strip().lower()
            if resume != 'y':
                self.url = input("Enter the new URL: ").strip()
            else:
                self.url = last_url
        else:
            self.url = input("Enter the URL: ").strip()

        if not self.url.endswith('vocabulary-list'):
            self.url = f"{self.url}/vocabulary-list"

        if not self.url:
            print("No URL provided. Exiting the program.")
            return

        self.save_last_url(self.url)
        self.offset = self.load_offset(self.url)
        existing_words = self.load_existing_words(self.url)

        if not existing_words and self.offset != 0:
            print(f"File not found for {self.url}. Starting fresh parsing.")
            self.offset = 0

        print(f"Resuming from offset: {self.offset}")

        total_existing_words = len(existing_words)
        print(f"Already parsed {total_existing_words} words for this URL.")

        self.all_vocabulary = existing_words
        self.total_entries = 0
        self.debug = False

        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = self.fetch_page(self.url, headers)
        if soup:
            total_entries_text = soup.find('p', string=re.compile(r"Showing \d+\.\.\d+ from \d+ entries"))
            if total_entries_text:
                try:
                    self.total_entries = int(re.search(r"from (\d+)", total_entries_text.text).group(1))
                except AttributeError:
                    print("Error: Unable to extract total entries count.")
                    self.total_entries = 0
            else:
                print("Error: Unable to find total entries text.")
                self.total_entries = 0
        else:
            print("Error: Unable to fetch page.")
            self.total_entries = 0

        self.total_entries -= total_existing_words

        with tqdm(total=self.total_entries, desc="Parsing words", unit="words") as pbar:
            while self.offset < self.total_entries:
                try:
                    vocabulary, has_more = self.parse_page(self.url, self.offset)

                    if not vocabulary:
                        print(f"Unable to fetch data at offset {self.offset}.")
                        break

                    self.all_vocabulary.extend(vocabulary)
                    pbar.update(len(vocabulary))

                    self.save_offset(self.url, self.offset + self.offset_step)
                    self.save_words_to_json(self.all_vocabulary, self.url)

                    delay = random.uniform(2, 5)
                    time.sleep(delay)

                    if not has_more:
                        break

                    self.offset += self.offset_step
                except Exception as e:
                    print(f"An error occurred during parsing at offset {self.offset}: {e}")
                    break

        print(f"Parsing completed. Data saved to file with name based on URL.")


if __name__ == '__main__':
    parser = VocabularyParser()
    parser.run()