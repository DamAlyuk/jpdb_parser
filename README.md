# jpdb_parser

This program pulls words from jpdb.io and saves them into a JSON file. The site doesn’t allow downloading words for personal use and forces you to use their platform, which I find a bit inconvenient. I personally prefer Anki for studying since it's much easier and more effective. The program collects details like words, readings (furigana), meanings, and usage stats from things like anime, books, and news. It saves everything into a file named after the novel or anime, and each word includes its ID, reading, meanings, and usage info. Plus, it keeps track of where you left off, so you can resume if something interrupts the process.

Example of the saved data:

```json
{
  "id": 1,
  "word": "まったい",
  "reading": "まったい",
  "meanings": ["complete", "whole", "perfect", "safe"],
  "top": {
    "anime": "18600",
    "news": "31000",
    "books": "6000"
  }
},
{
  "id": 2,
  "word": "そのこと",
  "reading": "そのこと",
  "meanings": ["that", "the issue at hand"],
  "top": {
    "anime": "1800",
    "news": "7800",
    "books": "1000"
  }
}
```
