"""
========================================================
  ADIÇÃO AO BOT: Salvar resultados em CSV
  Adicione este código ao seu amazon_bot.py existente
========================================================
"""

import csv
import os
from datetime import datetime


# ============================================================
# FUNÇÃO: salvar_csv()
#
# Como o csv.DictWriter funciona:
#   - fieldnames define a ordem e o nome das colunas
#   - writeheader() escreve a primeira linha (cabeçalho)
#   - writerows() escreve todas as linhas de uma vez
#
# Por que 'newline=""' no open()?
#   O módulo csv do Python controla as quebras de linha
#   internamente. Se não passar newline="", o Windows
#   adiciona linhas em branco extras entre cada registro.
#
# Por que encoding="utf-8-sig"?
#   O "-sig" adiciona um BOM (Byte Order Mark) invisível
#   no início do arquivo. Isso faz o Excel abrir o CSV
#   com acentos corretos automaticamente.
# ============================================================

def salvar_csv(produtos: list[dict], termo: str) -> str | None:
    """
    Salva a lista de produtos em um arquivo CSV.
    
    O nome do arquivo inclui o termo buscado e a data/hora,
    então cada execução gera um arquivo novo sem sobrescrever
    os anteriores — útil para comparar preços ao longo do tempo.
    
    Retorna o caminho do arquivo salvo, ou None se falhar.
    """
    if not produtos:
        print("  ⚠️  Nenhum produto para salvar.")
        return None

    # Cria um nome de arquivo com timestamp
    # Ex: resultados_notebook_2024-01-15_14-32-00.csv
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    termo_slug = termo.replace(" ", "_").lower()
    nome_arquivo = f"resultados_{termo_slug}_{agora}.csv"

    # Opcional: salva numa subpasta "resultados/"
    # Se a pasta não existir, cria automaticamente
    pasta = "resultados"
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome_arquivo)

    try:
        # Define as colunas na ordem que aparecerão no CSV
        colunas = ["numero", "titulo", "preco", "link"]

        with open(caminho, mode="w", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.DictWriter(arquivo, fieldnames=colunas)

            # Linha 1: cabeçalho (numero, titulo, preco, link)
            writer.writeheader()

            # Linhas seguintes: um produto por linha
            writer.writerows(produtos)

        print(f"\n  💾 Resultados salvos em: {caminho}")
        print(f"  📊 {len(produtos)} produto(s) exportado(s).")
        return caminho

    except PermissionError:
        print(f"  ❌ ERRO: Sem permissão para salvar em '{caminho}'.")
        print("  💡 Dica: Feche o arquivo se estiver aberto no Excel.")
        return None

    except Exception as e:
        print(f"  ❌ ERRO ao salvar CSV: {e}")
        return None


# ============================================================
# COMO INTEGRAR NO SEU amazon_bot.py:
#
# 1. Adicione os imports no topo do arquivo:
#       import csv
#       import os
#       from datetime import datetime
#
# 2. Cole a função salvar_csv() acima no arquivo
#
# 3. No main(), após exibir_resultados(), adicione:
#       salvar_csv(produtos, CONFIG["termo_busca"])
#
# Ficará assim no main():
#
#   produtos = coletar_produtos(page, CONFIG["max_produtos"])
#   exibir_resultados(produtos, CONFIG["termo_busca"])
#   salvar_csv(produtos, CONFIG["termo_busca"])   # <-- nova linha
#
# ============================================================


# ============================================================
# BÔNUS: ler_csv()
# Lê um CSV salvo anteriormente e retorna como lista de dicts.
# Útil para comparar preços entre execuções diferentes.
# ============================================================

def ler_csv(caminho: str) -> list[dict]:
    """
    Lê um arquivo CSV gerado pelo bot e retorna os dados.
    
    csv.DictReader usa a primeira linha como chave dos dicionários,
    então cada linha vira um dict com as mesmas chaves do cabeçalho.
    """
    try:
        with open(caminho, mode="r", newline="", encoding="utf-8-sig") as arquivo:
            reader = csv.DictReader(arquivo)
            produtos = list(reader)

        print(f"  📂 {len(produtos)} produto(s) lidos de '{caminho}'.")
        return produtos

    except FileNotFoundError:
        print(f"  ❌ ERRO: Arquivo '{caminho}' não encontrado.")
        return []

    except Exception as e:
        print(f"  ❌ ERRO ao ler CSV: {e}")
        return []


# ============================================================
# TESTE RÁPIDO (rode este arquivo diretamente para testar
# sem precisar executar o bot completo)
# ============================================================

if __name__ == "__main__":
    # Dados fictícios para testar
    produtos_teste = [
        {
            "numero": 1,
            "titulo": "Notebook Samsung Book X40 Intel Core i5",
            "preco": "R$ 2.799,00",
            "link": "https://www.amazon.com.br/dp/XXXXXXX1",
        },
        {
            "numero": 2,
            "titulo": "Notebook Dell Inspiron 15 AMD Ryzen 5",
            "preco": "R$ 3.199,00",
            "link": "https://www.amazon.com.br/dp/XXXXXXX2",
        },
        {
            "numero": 3,
            "titulo": "Notebook Lenovo IdeaPad 3i Core i3",
            "preco": "Preço não disponível",
            "link": "https://www.amazon.com.br/dp/XXXXXXX3",
        },
    ]

    print("=== Testando salvar_csv() ===")
    caminho_salvo = salvar_csv(produtos_teste, "notebook")

    if caminho_salvo:
        print("\n=== Testando ler_csv() ===")
        dados_lidos = ler_csv(caminho_salvo)
        for p in dados_lidos:
            print(f"  [{p['numero']}] {p['titulo'][:50]} | {p['preco']}")