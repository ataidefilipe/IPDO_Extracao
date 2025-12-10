# ver_banco.py
import sqlite3
import pandas as pd
from config.settings import DB_PATH
from utils.logger import log
from datetime import datetime

def mostrar_resumo():
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("           RESUMO DO BANCO ONS - IPDO")
    print("="*60)
    
    # Total de dias processados
    total_dias = pd.read_sql_query("SELECT COUNT(DISTINCT data) as qtd FROM destaques_operacao", conn).iloc[0]['qtd']
    datas = pd.read_sql_query("SELECT data FROM destaques_operacao ORDER BY data DESC LIMIT 10", conn)['data'].tolist()
    
    print(f"Total de dias no banco: {total_dias}")
    print(f"Últimas datas: {', '.join(datas)}")
    print("-" * 60)

    # Último dia completo
    ultimo_dia = datas[0] if datas else None
    if ultimo_dia:
        print(f"\nDESTAQUES DO DIA: {ultimo_dia}")
        print("\nGeração por Submercado e Tipo:")
        df_ger = pd.read_sql_query("""
            SELECT submercado, tipo_geracao, status, substr(descricao, 1, 70) || '...' as descricao
            FROM destaques_geracao 
            WHERE data = ?
            ORDER BY submercado, 
                     CASE tipo_geracao 
                       WHEN 'Hidráulica' THEN 1 
                       WHEN 'Térmica' THEN 2 
                       WHEN 'Eólica' THEN 3 
                       WHEN 'Solar' THEN 4 
                       WHEN 'Nuclear' THEN 5 ELSE 99 END
        """, conn, params=(ultimo_dia,))
        print(df_ger.to_string(index=False))

        print("\nDestaques Térmicos:")
        df_term = pd.read_sql_query("""
            SELECT unidade_geradora, desvio, substr(descricao, 1, 80) || '...' as descricao
            FROM destaques_geracao_termica 
            WHERE data = ? 
            ORDER BY desvio DESC
        """, conn, params=(ultimo_dia,))
        if len(df_term) == 0:
            print("   Nenhum destaque térmico neste dia")
        else:
            print(df_term.to_string(index=False))

    conn.close()
    print("\n" + "="*60)

def exportar_excel():
    conn = sqlite3.connect(DB_PATH)
    
    # Lê tudo
    df_op = pd.read_sql_query("SELECT data, submercado, carga_status, carga_descricao, restricoes, transferencia_status FROM destaques_operacao ORDER BY data DESC", conn)
    df_ger = pd.read_sql_query("SELECT data, submercado, tipo_geracao, status, descricao FROM destaques_geracao ORDER BY data DESC", conn)
    df_term = pd.read_sql_query("SELECT data, unidade_geradora, desvio, descricao FROM destaques_geracao_termica ORDER BY data DESC", conn)
    
    arquivo = f"IPDO_Destaques_Completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
        df_op.to_excel(writer, sheet_name="Operação e Carga", index=False)
        df_ger.to_excel(writer, sheet_name="Geração por Tipo", index=False)
        df_term.to_excel(writer, sheet_name="Destaques Térmicos", index=False)
    
    conn.close()
    print(f"\nExcel gerado com sucesso: {arquivo}")
    print("   3 abas: Operação e Carga | Geração por Tipo | Destaques Térmicos")

if __name__ == "__main__":
    print("\nEscolha uma opção:\n")
    print("1 → Ver resumo no terminal (recomendado)")
    print("2 → Exportar TUDO para Excel agora")
    print("3 → Ambos")
    
    try:
        op = input("\nDigite 1, 2 ou 3: ").strip()
        if op == "1":
            mostrar_resumo()
        elif op == "2":
            exportar_excel()
        elif op == "3":
            mostrar_resumo()
            exportar_excel()
        else:
            print("Opção inválida!")
    except KeyboardInterrupt:
        print("\nTchau!")