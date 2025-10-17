import os, requests
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

class Digisac:
    def __init__(self):
        self.session = requests.Session() 
        self.base_url = os.getenv("URL") 
        self.service_id = os.getenv("SERVICE_ID") 

        # Atualiza cabeçalhos da requisição com token e tipo de conteúdo
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'{os.getenv("DIGISAC_TOKEN")}'
        })

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Optional[requests.Response]:
        try:
            # Faz a requisição e retorna a resposta
            return self.session.request(method, f"{self.base_url}{endpoint}", **kwargs)
        except Exception as e:
            pass

    def send_message(self, message: str, number: str) -> None:
        # Prepara o payload para enviar a mensagem
        payload = {
            "number": number,
            "serviceId": self.service_id,
            "type": "chat",
            "origin": "bot",
            "text": message
        }

        # Envia a mensagem via POST
        self._request("post", "/messages", json=payload)