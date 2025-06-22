# NamazApp Support Chatbot

This repository provides a lightweight command line chatbot for the NamazApp. The bot uses a small FAQ dataset in `data/faq_data.json` and matches user questions to predefined answers with a TF‑IDF similarity search.

## Setup

1. Install Python dependencies (requires Python 3.8+):

```bash
pip install scikit-learn
```

2. Run the chatbot:

```bash
python chatbot.py
```

Type your question in Russian and the bot will respond with the closest answer or a list of recommended links.

Type `exit` to quit the chat.
