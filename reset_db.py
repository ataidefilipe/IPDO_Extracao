# reset_db.py
from database.models import reset_db

if __name__ == "__main__":
    print("\n⚠️ ATENÇÃO ⚠️")
    print("Você está prestes a APAGAR TODO O BANCO DE DADOS.")
    print("Esta ação é IRREVERSÍVEL.\n")

    confirm = input("Digite 'RESETAR' para confirmar: ").strip()

    if confirm == "RESETAR":
        reset_db()
        print("Banco apagado com sucesso.")
    else:
        print("Operação cancelada.")
