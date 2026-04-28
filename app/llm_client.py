import aiohttp
import os
from cfg import DEEPSEEK_API_KEY

API_URL = "https://api.deepseek.com/chat/completions"


async def ask_llm(user_text: str, system_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = []
    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_text})
    payload = {
        "model": "deepseek-chat",
        "messages":messages,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as resp:
            data = await resp.json()

            return data["choices"][0]["message"]["content"]