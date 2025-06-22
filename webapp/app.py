from flask import Flask, request, jsonify, render_template
from chatbot import load_data, build_model, find_best_match

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    """Allow browser-based clients to access the API."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

data = load_data('data/faq_data.json')
questions = [item['query'] for item in data]
vectorizer, X = build_model(questions)


def format_answer(answer):
    if 'response' in answer:
        return answer['response']
    if 'recommended_items' in answer:
        lines = []
        for item in answer['recommended_items']:
            lines.append(f"- {item['title']}: {item['url']}")
        return "\n".join(lines)
    return 'Извините, я не знаю ответа.'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        # Preflight request
        return '', 204
@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get('message', '')
    if not user_query:
        return jsonify({'response': 'Введите вопрос.'})
    idx, _ = find_best_match(user_query, vectorizer, X, questions)
    answer = data[idx]
    return jsonify({'response': format_answer(answer)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
