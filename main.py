import logging
from threading import Lock
from flask import Flask, render_template, request
from clients.pan import Pan

# Inicializa o app Flask
app = Flask(__name__, static_folder="static")
# Bloqueio para garantir execução segura em múltiplas threads
execution_lock = Lock()
# Instância do objeto Pan
pan = Pan()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler("log.log")])
logging.getLogger('werkzeug').setLevel(logging.ERROR) # Silencia log do werkzeug
logger = logging.getLogger()

# Rota principal
@app.route("/")
def index():
    return render_template("index.html")

# Rota para consulta de CLT 
@app.route("/consult", methods=["POST"])
def consult():
    # Pega os dados enviados no corpo da requisição
    data = request.json
    logger.info(f"Dados de entrada: {data}")

    # Executa apenas 1 request por vez
    with execution_lock:
        # Navega até chegar em CardOferta
        while not pan.locate(data):
            pass
        
        # Verifica autorização
        authorization = pan.get_farol_title()
        
        if authorization != "Aceito":
            # Se não for autorizado, retorna mensagem de erro
            response = {
                "authorization": authorization, 
                "result": "Nenhuma oferta disponível no momento."
            }
    
            logger.info(f"Saída: {response}\n")

            return response, 200
        
        # Se autorizado, retorna o resultado da consulta
        result = pan.consult()

        response = {
            "authorization": authorization, 
            "result": result
        }

        logger.info(f"Saída: {response}")
        
        return response, 200

if __name__ == "__main__":
    app.run("0.0.0.0")