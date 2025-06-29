import requests
import json
import logging

logger = logging.getLogger(__name__)

class GPTAPIClient:
    def __init__(self):
        self.api_url = "https://namazlive.herokuapp.com/gpt/generate"
        self.api_key = "jiro_dreams_of_sushi"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
    
    def generate_response(self, user_message: str, system_message: str = None) -> str:
        """Generate response using GPT API"""
        if system_message is None:
            system_message = """Ты - помощник приложения для молитв NamazApp. 
Отвечай на вопросы пользователей на русском языке, используя информацию из приложения. 
Всегда используй Markdown форматирование для ссылок и выделения.
Будь полезным, дружелюбным и информативным."""
        
        payload = {
            "user_id": "multi_agent_recommender",
            "user_message": user_message,
            "system_message": system_message,
            "llm_model": "gemini-2.0-flash",
            "response_schema": {
                "answer": "str"
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "answer" in result:
                    return result["answer"]
                else:
                    logger.error(f"Unexpected API response format: {result}")
                    return "Извините, произошла ошибка при генерации ответа."
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return "Извините, сервис временно недоступен."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return "Извините, не удалось подключиться к сервису."
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "Извините, произошла непредвиденная ошибка."
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "user_id": "multi_agent_recommender",
                    "user_message": "Привет",
                    "system_message": "Ответь кратко",
                    "llm_model": "gemini-2.0-flash",
                    "response_schema": {
                        "answer": "str"
                    }
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

def main():
    """Test the GPT API client"""
    client = GPTAPIClient()
    
    if client.test_connection():
        print("✅ API connection successful")
    else:
        print("❌ API connection failed")
        return
    
    test_questions = [
        "Как поделиться приложением с друзьями?",
        "Рекомендуйте приложения для изучения арабского алфавита",
        "Как изменить язык приложения?",
        "Где найти настройки молитв?"
    ]
    
    print("\nTesting GPT API:")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        response = client.generate_response(question)
        print(f"Response: {response}")
        print("-" * 30)

if __name__ == "__main__":
    main() 