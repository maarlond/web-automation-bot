"""
========================================================
  BOT DE AUTOMAÇÃO WEB - Amazon Product Scraper
  Tecnologia: Python + Playwright
  Nível: Iniciante/Intermediário
========================================================

COMO FUNCIONA NO GERAL:
  1. O Playwright abre um navegador real (Chromium, Firefox ou WebKit)
  2. Ele navega até o site como um humano faria
  3. Encontra os elementos HTML usando seletores CSS
  4. Extrai o texto/links desses elementos
  5. Exibe tudo organizado no terminal

INSTALAÇÃO (rode no terminal antes de executar):
  pip install playwright
  playwright install chromium
"""

import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import csv
import os
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES GLOBAIS
# Centralizar configs aqui facilita futuras alterações
# ============================================================

CONFIG = {
    "url_base": "https://www.amazon.com.br",
    "termo_busca": "notebook",
    "max_produtos": 5,          # Quantos produtos coletar
    "headless": False,          # False = você vê o navegador abrir
    "timeout": 15000,           # 15 segundos de espera máxima por elemento
}

# ============================================================
# FUNÇÃO 1: delay_humano()
# Por que isso existe?
#   Sites detectam bots por velocidade de ação. Um humano leva
#   1-3 segundos entre cliques. O random.uniform() gera um
#   número decimal aleatório entre os valores passados.
# ============================================================

def delay_humano(minimo: float = 1.0, maximo: float = 2.5) -> None:
    """Pausa a execução por um tempo aleatório para simular comportamento humano."""
    espera = random.uniform(minimo, maximo)
    print(f"  ⏳ Aguardando {espera:.1f}s...")
    time.sleep(espera)


# ============================================================
# FUNÇÃO 2: criar_navegador()
# O Playwright trabalha com "contextos":
#   - playwright  → motor que controla tudo
#   - browser     → a janela do navegador
#   - page        → uma aba específica
# Retornamos os 3 para poder fechar tudo no final
# ============================================================

def criar_navegador(playwright_instance):
    """
    Inicia o navegador com configurações que reduzem detecção de bot.
    
    Por que user_agent personalizado?
      O navegador padrão do Playwright se identifica como 'HeadlessChrome',
      o que alguns sites bloqueiam. Passamos um user-agent real para parecer
      um navegador comum.
    """
    browser = playwright_instance.chromium.launch(
        headless=CONFIG["headless"],
        slow_mo=50,  # Adiciona 50ms entre ações internas do Playwright
    )

    # Um "contexto" é como um perfil de navegador isolado
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 768},  # Resolução comum de monitor
        locale="pt-BR",
    )

    page = context.new_page()
    page.set_default_timeout(CONFIG["timeout"])

    return browser, context, page


# ============================================================
# FUNÇÃO 3: acessar_site()
# page.goto() navega até a URL.
# wait_until="domcontentloaded" espera o HTML básico carregar
# (mais rápido que esperar todas as imagens/scripts).
# ============================================================

def acessar_site(page, url: str) -> bool:
    """
    Navega até a URL informada.
    Retorna True se bem-sucedido, False se falhar.
    """
    try:
        print(f"\n🌐 Acessando: {url}")
        page.goto(url, wait_until="domcontentloaded")
        delay_humano(1.5, 3.0)
        print("  ✅ Site carregado com sucesso!")
        return True

    except PlaywrightTimeout:
        print(f"  ❌ ERRO: Timeout ao acessar {url}")
        print("  💡 Dica: Verifique sua conexão ou tente novamente.")
        return False

    except Exception as e:
        print(f"  ❌ ERRO inesperado ao acessar o site: {e}")
        return False


# ============================================================
# FUNÇÃO 4: realizar_busca()
# Aqui simulamos o usuário digitando na barra de pesquisa.
# 
# Como encontrar o seletor correto?
#   No Chrome: F12 → clique no elemento → botão direito no HTML
#   → "Copy" → "Copy selector"
#
# fill() limpa o campo e digita o texto.
# press("Enter") simula apertar Enter.
# wait_for_load_state() espera a página de resultados carregar.
# ============================================================

def realizar_busca(page, termo: str) -> bool:
    """
    Digita o termo na barra de busca e pressiona Enter.
    Retorna True se bem-sucedido.
    """
    try:
        print(f"\n🔍 Buscando por: '{termo}'")

        # Aguarda a caixa de busca aparecer na tela
        campo_busca = page.wait_for_selector("#twotabsearchtextbox")
        
        delay_humano(0.5, 1.0)
        
        # Clica no campo (como um humano faria antes de digitar)
        campo_busca.click()
        delay_humano(0.3, 0.7)
        
        # Digita o termo de busca
        campo_busca.fill(termo)
        delay_humano(0.5, 1.0)
        
        # Pressiona Enter
        campo_busca.press("Enter")
        
        # Espera a página de resultados carregar
        page.wait_for_load_state("domcontentloaded")
        delay_humano(2.0, 3.5)
        
        print("  ✅ Busca realizada com sucesso!")
        return True

    except PlaywrightTimeout:
        print("  ❌ ERRO: Campo de busca não encontrado.")
        print("  💡 Dica: O site pode ter mudado o layout.")
        return False

    except Exception as e:
        print(f"  ❌ ERRO inesperado na busca: {e}")
        return False


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
# FUNÇÃO 5: coletar_produtos()
# Esta é a parte principal do scraping!
#
# query_selector_all() encontra TODOS os elementos que
# correspondem ao seletor CSS e retorna uma lista.
#
# Por que [data-component-type="s-search-result"]?
#   Cada produto na Amazon tem esse atributo no seu div container.
#   É mais estável que classes CSS que mudam frequentemente.
#
# .query_selector() dentro de um elemento busca apenas
# dentro daquele elemento específico (não na página toda).
# ============================================================

def coletar_produtos(page, quantidade: int) -> list[dict]:
    """
    Extrai título, preço e link dos produtos na página de resultados.
    Retorna uma lista de dicionários com os dados de cada produto.
    """
    produtos = []

    try:
        print(f"\n📦 Coletando até {quantidade} produtos...")

        # Espera os resultados aparecerem
        page.wait_for_selector('[data-component-type="s-search-result"]')

        # Pega todos os cards de produto
        cards = page.query_selector_all('[data-component-type="s-search-result"]')
        print(f"  📊 Total de resultados encontrados na página: {len(cards)}")

        for i, card in enumerate(cards):
            # Para quando atingir o limite desejado
            if len(produtos) >= quantidade:
                break

            # Pequeno delay entre a extração de cada produto
            if i > 0:
                delay_humano(0.2, 0.5)

            # Tenta extrair cada informação com tratamento individual de erro
            # Assim, se um campo falhar, os outros ainda são coletados

            # --- TÍTULO ---
            titulo = "Título não encontrado"
            try:
                el_titulo = card.query_selector("h2 span")
                if el_titulo:
                    titulo = el_titulo.inner_text().strip()
            except Exception:
                pass

            # --- PREÇO ---
            # A Amazon divide o preço em parte inteira e centavos
            # Ex: <span class="a-price-whole">5.499</span>
            #     <span class="a-price-fraction">00</span>
            preco = "Preço não disponível"
            try:
                el_preco_inteiro = card.query_selector(".a-price-whole")
                el_preco_centavos = card.query_selector(".a-price-fraction")
                
                if el_preco_inteiro:
                    inteiro = el_preco_inteiro.inner_text().strip().replace(".", "").replace(",", "")
                    centavos = "00"
                    if el_preco_centavos:
                        centavos = el_preco_centavos.inner_text().strip()
                    preco = f"R$ {inteiro},{centavos}"
            except Exception:
                pass

            # --- LINK ---
            link = "Link não encontrado"
            try:
                el_link = card.query_selector("h2 a")
                if el_link:
                    href = el_link.get_attribute("href")
                    if href:
                        # Links da Amazon são relativos (/dp/...), completamos com a base
                        if href.startswith("/"):
                            link = CONFIG["url_base"] + href
                        else:
                            link = href
            except Exception:
                pass

            # Só adiciona se tiver ao menos título
            if titulo != "Título não encontrado":
                produtos.append({
                    "numero": len(produtos) + 1,
                    "titulo": titulo,
                    "preco": preco,
                    "link": link,
                })
                print(f"  ✅ Produto {len(produtos)} coletado.")

        return produtos

    except PlaywrightTimeout:
        print("  ❌ ERRO: Resultados de busca não carregaram.")
        return produtos

    except Exception as e:
        print(f"  ❌ ERRO ao coletar produtos: {e}")
        return produtos


# ============================================================
# FUNÇÃO 6: exibir_resultados()
# Formata e exibe os dados no terminal de forma legível.
# Truncar o título evita linhas muito longas.
# ============================================================

def exibir_resultados(produtos: list[dict], termo: str) -> None:
    """Exibe os produtos coletados de forma organizada no terminal."""

    print("\n")
    print("=" * 70)
    print(f"  🛒  RESULTADOS DA BUSCA: '{termo.upper()}'")
    print("=" * 70)

    if not produtos:
        print("  ⚠️  Nenhum produto encontrado.")
        print("  💡  Verifique o seletor CSS ou se o site mudou o layout.")
        return

    for produto in produtos:
        # Trunca títulos longos para não quebrar o layout
        titulo_curto = (produto["titulo"][:65] + "...") if len(produto["titulo"]) > 65 else produto["titulo"]

        print(f"\n  [{produto['numero']}] {titulo_curto}")
        print(f"       💰 Preço : {produto['preco']}")
        print(f"       🔗 Link  : {produto['link'][:80]}...")
        print(f"  {'-' * 66}")

    print(f"\n  📈 Total coletado: {len(produtos)} produto(s)")
    print("=" * 70)


# ============================================================
# FUNÇÃO PRINCIPAL: main()
# O bloco with sync_playwright() as p garante que o Playwright
# seja iniciado e encerrado corretamente, mesmo se houver erros.
# É como um "gerenciador de contexto" — equivalente a abrir e
# fechar um arquivo com open().
# ============================================================

def main():
    print("\n" + "=" * 70)
    print("  🤖  BOT DE AUTOMAÇÃO WEB - Amazon Scraper")
    print("  📚  Tecnologia: Python + Playwright")
    print("=" * 70)

    with sync_playwright() as p:
        browser = None
        try:
            # Passo 1: Criar o navegador
            browser, context, page = criar_navegador(p)

            # Passo 2: Acessar o site
            if not acessar_site(page, CONFIG["url_base"]):
                return  # Encerra se não conseguiu acessar

            # Passo 3: Realizar a busca
            if not realizar_busca(page, CONFIG["termo_busca"]):
                return  # Encerra se a busca falhou

            # Passo 4: Coletar os produtos
            produtos = coletar_produtos(page, CONFIG["max_produtos"])

            # Passo 5: Exibir os resultados
            exibir_resultados(produtos, CONFIG["termo_busca"])

            # Passo 6: Salvar resultados em csv
            salvar_csv(produtos, CONFIG["termo_busca"])


        except KeyboardInterrupt:
            print("\n\n  ⛔ Bot interrompido pelo usuário (Ctrl+C).")

        except Exception as e:
            print(f"\n  ❌ ERRO crítico não tratado: {e}")
            print("  💡 Dica: Verifique se o Playwright está instalado corretamente.")

        finally:
            # O bloco finally SEMPRE executa, mesmo com erros
            # Isso garante que o navegador seja sempre fechado
            if browser:
                print("\n  🔒 Fechando o navegador...")
                browser.close()
            print("  👋 Bot finalizado.\n")


# ============================================================
# PONTO DE ENTRADA
# if __name__ == "__main__" garante que main() só execute
# quando você rodar este arquivo diretamente (não quando
# importado como módulo em outro script).
# ============================================================

if __name__ == "__main__":
    main()