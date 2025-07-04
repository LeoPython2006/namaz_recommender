# NamazApp Support Chatbot

This repository provides a lightweight command line chatbot for the NamazApp. The bot uses a small FAQ dataset in `data/faq_data.json` and matches user questions to predefined answers with a TF‑IDF similarity search.

## Setup

1. Install Python dependencies (requires Python 3.8+):

```bash
pip install scikit-learn flask
```

2. Run the command line chatbot:

```bash
python chatbot.py
```

Type your question in Russian and the bot will respond with the closest answer or a list of recommended links.

Type `exit` to quit the chat.

## Web Chat

A simple web interface is provided in `webapp/`. Make sure the Flask package is installed and then start the server. Visit `http://localhost:8000` in your browser (do not open the HTML file directly):
A simple web interface is provided in `webapp/`. Start the Flask server and open `http://localhost:8000`:

```bash
python webapp/app.py
```

The `docs` folder contains the same HTML page configured for GitHub Pages. Update the `BACKEND_URL` constant inside `docs/index.html` to point to your deployed server.

## Deploy

Use the `deploy.sh` script to push this project to GitHub and enable GitHub Pages for the `docs/` folder:

```bash
./deploy.sh myuser/myrepo
```

The script uses the GitHub CLI (`gh`) and will output the public Pages URL. You can then deploy `webapp/app.py` to any Python hosting service (Heroku, Render, etc.) and update `BACKEND_URL` accordingly.
## Website

A minimal static site is available in the `docs` directory. To publish it on GitHub Pages:

1. Push this repository to GitHub.
2. In the repository **Settings**, enable GitHub Pages for the `docs/` folder.
3. GitHub will provide a public URL for your site after a few minutes.
