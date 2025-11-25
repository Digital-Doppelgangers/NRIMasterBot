import requests


CreateCharacterPrompt = """ Ты — генератор персонажей для Настольной ролевой игры. Пользователь хочет создать персонажа с такими пожеланиями:
[userprompt]
Сгенерируй подробного персонажа со следующей структурой:
- Имя
- Раса
- Класс
- Черты характера (3–5)
- Бэкграунд (короткая история)
- Боевые особенности / способности
- Нестандартная деталь (интересная фишка)

Пиши красиво, как мастер-наративщик."""


def ask_llama(prompt: str, model: str = "llama3.2"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    response.raise_for_status()

    return response.json()["response"]
