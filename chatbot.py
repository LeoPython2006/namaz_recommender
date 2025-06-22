import json
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_model(questions):
    vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2))
    X = vectorizer.fit_transform(questions)
    return vectorizer, X


def find_best_match(user_query, vectorizer, X, questions):
    q_vec = vectorizer.transform([user_query])
    similarities = cosine_similarity(q_vec, X).flatten()
    best_idx = similarities.argmax()
    return best_idx, similarities[best_idx]


def main():
    data = load_data('data/faq_data.json')
    questions = [item['query'] for item in data]
    vectorizer, X = build_model(questions)

    print('NamazApp Support Chatbot. Type "exit" to quit.')
    while True:
        try:
            user_query = input('\nYou: ').strip()
        except (EOFError, KeyboardInterrupt):
            print() 
            break
        if user_query.lower() in {'exit', 'quit'}:
            break
        if not user_query:
            continue
        idx, score = find_best_match(user_query, vectorizer, X, questions)
        answer = data[idx]
        if 'response' in answer:
            print('Bot:', answer['response'])
        elif 'recommended_items' in answer:
            print('Bot:')
            for item in answer['recommended_items']:
                print(f"- {item['title']}: {item['url']}")
        else:
            print('Bot: Извините, я не знаю ответа.')


if __name__ == '__main__':
    main()
