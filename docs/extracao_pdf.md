# Extração de PDF — Versão 2 (pypdfium2)

Este módulo substitui a extração baseada em PyPDF2, oferecendo:

- Maior precisão em relatórios estruturados
- Suporte melhor a tabelas e textos livres
- Fallback por página (não interrompe o fluxo)
- Limpeza automática do texto para melhor uso pelo GPT
- Performance significativamente melhor

O módulo expõe apenas:

extrair_texto(pdf_path: Path) -> str
