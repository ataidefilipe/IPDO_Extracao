# agent/cli.py
from agent_ipdo.agent import responder_pergunta
from datetime import datetime
import pytz



if __name__ == "__main__":
    print("\n🧠 Agente IPDO (digite 'sair' para encerrar)\n")

    while True:
        tz = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() in ("sair", "exit", "quit"):
            break
        
        entrada = f"[AGORA={agora}] {pergunta}"

        resposta = responder_pergunta(entrada)
        print("\nResposta:")
        print(resposta)
        print("-" * 50)
