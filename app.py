"""
========================================================
  AMAZON BOT - Interface Streamlit
  Execução: streamlit run streamlit_app.py

  Instalação:
    pip install playwright streamlit
    playwright install chromium
========================================================
"""

import time
import random
import csv
import os
from datetime import datetime

import streamlit as st
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# Deve ser a PRIMEIRA chamada Streamlit do arquivo.
# layout="wide" usa toda a largura da tela.
# ============================================================

st.set_page_config(
    page_title="Amazon Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS PERSONALIZADO
# O Streamlit aceita HTML/CSS via st.markdown().
# unsafe_allow_html=True é necessário para injetar estilos.
# ============================================================

st.markdown(
    """
<style>
    /* Importa fonte do Google */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Cabeçalho principal */
    .main-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.6rem;
        font-weight: 500;
        letter-spacing: -0.02em;
        color: #0f0f0f;
        margin-bottom: 0.2rem;
    }
    .main-sub {
        font-size: 0.85rem;
        color: #888;
        font-family: 'IBM Plex Mono', monospace;
        margin-bottom: 1.5rem;
    }

    /* Cards de métricas */
    .metric-box {
        background: #f7f7f5;
        border: 1px solid #e8e8e4;
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    .metric-box .label {
        font-size: 0.7rem;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }
    .metric-box .value {
        font-size: 1.5rem;
        font-weight: 500;
        color: #0f0f0f;
        font-family: 'IBM Plex Mono', monospace;
    }
    .metric-box .sub {
        font-size: 0.72rem;
        color: #aaa;
        margin-top: 0.2rem;
    }

    /* Tag de preço na tabela */
    .price-tag {
        background: #edf7f2;
        color: #1a7a50;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        font-family: 'IBM Plex Mono', monospace;
        white-space: nowrap;
    }
    .price-tag.alert {
        background: #fef3e2;
        color: #b36a00;
    }
    .price-tag.unavailable {
        background: #f2f2f0;
        color: #aaa;
    }

    /* Linha de status no rodapé */
    .status-bar {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #bbb;
        padding-top: 0.8rem;
        border-top: 1px solid #f0f0ee;
        margin-top: 1rem;
    }

    /* Divider */
    .divider {
        border: none;
        border-top: 1px solid #f0f0ee;
        margin: 1.2rem 0;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# FUNÇÕES DO BOT (mesmas do amazon_bot.py, adaptadas)
# A única diferença: usamos st.session_state para comunicar
# progresso ao Streamlit em vez de print().
# ============================================================


def delay_humano(minimo=0.8, maximo=1.8):
    time.sleep(random.uniform(minimo, maximo))


def executar_bot(termo: str, quantidade: int, headless: bool) -> list[dict]:
    """
    Roda o bot completo e retorna lista de produtos.
    Usa st.status() para mostrar progresso em tempo real.
    """
    produtos = []

    with st.status("🤖 Executando bot...", expanded=True) as status:
        with sync_playwright() as p:
            browser = None
            try:
                # --- Passo 1: Navegador ---
                st.write("🌐 Iniciando navegador...")
                browser = p.chromium.launch(headless=headless, slow_mo=30)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 768},
                    locale="pt-BR",
                )
                page = context.new_page()
                page.set_default_timeout(15000)

                # --- Passo 2: Acessar site ---
                st.write("🔗 Acessando Amazon...")
                page.goto("https://www.amazon.com.br", wait_until="domcontentloaded")
                delay_humano(1.5, 2.5)

                # --- Passo 3: Buscar ---
                st.write(f"🔍 Buscando por **{termo}**...")
                campo = page.wait_for_selector("#twotabsearchtextbox")
                campo.click()
                delay_humano(0.3, 0.6)
                campo.fill(termo)
                delay_humano(0.4, 0.8)
                campo.press("Enter")
                page.wait_for_load_state("domcontentloaded")
                delay_humano(2.0, 3.0)

                # --- Passo 4: Coletar ---
                st.write("📦 Coletando produtos...")
                page.wait_for_selector('[data-component-type="s-search-result"]')
                cards = page.query_selector_all(
                    '[data-component-type="s-search-result"]'
                )

                for i, card in enumerate(cards):
                    if len(produtos) >= quantidade:
                        break

                    if i > 0:
                        delay_humano(0.1, 0.3)

                    # Título
                    titulo = "Título não encontrado"
                    try:
                        el = card.query_selector("h2 span")
                        if el:
                            titulo = el.inner_text().strip()
                    except Exception:
                        pass

                    # Preço
                    preco_texto = "Indisponível"
                    preco_num = None
                    try:
                        el_int = card.query_selector(".a-price-whole")
                        el_dec = card.query_selector(".a-price-fraction")
                        if el_int:
                            inteiro = (
                                el_int.inner_text()
                                .strip()
                                .replace(".", "")
                                .replace(",", "")
                            )
                            dec = el_dec.inner_text().strip() if el_dec else "00"
                            preco_texto = f"R$ {inteiro},{dec}"
                            preco_num = float(f"{inteiro}.{dec}")
                    except Exception:
                        pass

                    # Link
                    link = ""
                    try:
                        # el = card.query_selector("h2 a")
                        el = card.query_selector(
                            "a.a-link-normal"
                        ) or card.query_selector(
                            "a[href*='/dp/']"
                        )  # Link não estava retornando alterei para esse seletor

                        if el:
                            href = el.get_attribute("href") or ""
                            link = (
                                ("https://www.amazon.com.br" + href)
                                if href.startswith("/")
                                else href
                            )
                    except Exception:
                        pass

                    if titulo != "Título não encontrado":
                        produtos.append(
                            {
                                "numero": len(produtos) + 1,
                                "titulo": titulo,
                                "preco": preco_texto,
                                "preco_num": preco_num,
                                "link": link,
                            }
                        )
                        st.write(f"  ✅ Produto {len(produtos)} coletado.")

                status.update(
                    label=f"✅ Concluído — {len(produtos)} produto(s) encontrado(s)",
                    state="complete",
                )

            except PlaywrightTimeout:
                status.update(label="❌ Timeout — verifique sua conexão", state="error")

            except Exception as e:
                status.update(label=f"❌ Erro: {e}", state="error")

            finally:
                if browser:
                    browser.close()

    return produtos


# ============================================================
# FUNÇÃO: salvar_csv()
# Retorna os bytes do CSV para o botão de download.
# Em vez de salvar em disco, o Streamlit usa st.download_button()
# que recebe os dados como string ou bytes diretamente.
# ============================================================


def gerar_csv_bytes(produtos: list[dict]) -> bytes:
    """Gera o CSV em memória e retorna como bytes para download."""
    import io

    output = io.StringIO()
    colunas = ["numero", "titulo", "preco", "link"]
    writer = csv.DictWriter(output, fieldnames=colunas, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(produtos)
    return output.getvalue().encode("utf-8-sig")


# ============================================================
# FUNÇÕES DE ANÁLISE
# Calculam métricas a partir da lista de produtos.
# ============================================================


def calcular_metricas(produtos: list[dict], alerta: float):
    precos = [p["preco_num"] for p in produtos if p["preco_num"] is not None]
    menor = min(precos) if precos else None
    media = sum(precos) / len(precos) if precos else None
    abaixo = sum(1 for v in precos if v < alerta) if alerta else 0

    menor_nome = ""
    if menor is not None:
        for p in produtos:
            if p["preco_num"] == menor:
                menor_nome = p["titulo"][:30] + "..."
                break

    return {
        "coletados": len(produtos),
        "menor": menor,
        "menor_nome": menor_nome,
        "media": media,
        "abaixo_alerta": abaixo,
    }


def formatar_preco(valor):
    if valor is None:
        return "—"
    return f"R$ {valor:,.0f}".replace(",", ".")


# ============================================================
# INTERFACE STREAMLIT
# Tudo abaixo é a UI.
#
# st.session_state é o "estado global" do app.
# No Streamlit, toda interação re-executa o script do zero.
# O session_state persiste valores entre essas re-execuções.
# ============================================================

# Inicializa estado
if "produtos" not in st.session_state:
    st.session_state.produtos = []
if "ultima_busca" not in st.session_state:
    st.session_state.ultima_busca = None
if "termo_atual" not in st.session_state:
    st.session_state.termo_atual = ""


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    termo = st.text_input(
        "Produto",
        value="notebook",
        placeholder="ex: notebook, teclado, mouse...",
        help="Termo que será digitado na barra de busca da Amazon",
    )

    quantidade = st.slider(
        "Quantidade de resultados",
        min_value=1,
        max_value=20,
        value=8,
        help="Quantos produtos coletar da página de resultados",
    )

    alerta_preco = st.number_input(
        "Alerta de preço (R$)",
        min_value=0.0,
        value=3000.0,
        step=100.0,
        format="%.2f",
        help="Produtos abaixo desse valor serão destacados",
    )

    headless = st.toggle(
        "Modo invisível",
        value=True,
        help="Ligado = navegador roda em segundo plano. Desligado = você vê o navegador abrir.",
    )

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    executar = st.button(
        "▶ Executar busca",
        type="primary",
        use_container_width=True,
    )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Download CSV (só aparece se tiver resultados)
    if st.session_state.produtos:
        csv_bytes = gerar_csv_bytes(st.session_state.produtos)
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M")
        st.download_button(
            label="⬇ Baixar CSV",
            data=csv_bytes,
            file_name=f"amazon_{st.session_state.termo_atual}_{agora}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# --- ÁREA PRINCIPAL ---

st.markdown('<p class="main-header">🤖 Amazon Bot</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-sub">web scraping com playwright + streamlit</p>',
    unsafe_allow_html=True,
)

# Executa o bot quando o botão for clicado
if executar:
    if not termo.strip():
        st.warning("Digite um produto para buscar.")
    else:
        st.session_state.produtos = executar_bot(termo.strip(), quantidade, headless)
        st.session_state.ultima_busca = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        st.session_state.termo_atual = termo.strip()

# Exibe resultados se existirem
if st.session_state.produtos:
    produtos = st.session_state.produtos
    metricas = calcular_metricas(produtos, alerta_preco)

    # --- Métricas ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="label">Produtos coletados</div>
            <div class="value">{metricas['coletados']}</div>
            <div class="sub">de {quantidade} solicitados</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        menor_fmt = formatar_preco(metricas["menor"])
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="label">Menor preço</div>
            <div class="value">{menor_fmt}</div>
            <div class="sub">{metricas['menor_nome'] or '—'}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c3:
        media_fmt = formatar_preco(metricas["media"])
        alerta_txt = (
            f"🟡 {metricas['abaixo_alerta']} abaixo do alerta"
            if metricas["abaixo_alerta"] > 0
            else "Nenhum abaixo do alerta"
        )
        st.markdown(
            f"""
        <div class="metric-box">
            <div class="label">Média de preços</div>
            <div class="value">{media_fmt}</div>
            <div class="sub">{alerta_txt}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- Tabela de resultados ---
    # st.dataframe() é o componente nativo do Streamlit para tabelas.
    # É mais robusto que HTML manual e funciona bem em modo claro e escuro.
    # column_config permite personalizar cada coluna individualmente.
    st.markdown("**Resultados**")

    import pandas as pd

    df_produtos = pd.DataFrame(
        [
            {
                "#": p["numero"],
                "Produto": p["titulo"],
                "Preço": p["preco"],
                "Abaixo do alerta": (
                    p["preco_num"] is not None and p["preco_num"] < alerta_preco
                ),
                "Link": p["link"],
            }
            for p in produtos
        ]
    )

    st.dataframe(
        df_produtos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "Produto": st.column_config.TextColumn(width="large"),
            "Preço": st.column_config.TextColumn(width="medium"),
            "Abaixo do alerta": st.column_config.CheckboxColumn(
                "🟡 Alerta",
                width="small",
                help=f"Preço abaixo de R$ {alerta_preco:,.2f}",
            ),
            "Link": st.column_config.LinkColumn(
                "Link",
                width="small",
                display_text="↗ abrir",
            ),
        },
    )

    # --- Gráfico de preços ---
    # Definindo precos_validos aqui para usar tanto no gráfico quanto no status bar
    precos_validos = [p["preco_num"] for p in produtos if p["preco_num"] is not None]

    if len(precos_validos) >= 2:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("**Distribuição de preços**")

        # Calcula faixas dinamicamente com base nos valores reais
        p_min = min(precos_validos)
        p_max = max(precos_validos)
        n_faixas = min(6, len(precos_validos))
        tamanho_faixa = (p_max - p_min) / n_faixas if p_max > p_min else 1

        faixas = {}
        for i in range(n_faixas):
            inicio = p_min + i * tamanho_faixa
            label = f"R${inicio/1000:.1f}k"
            fim = inicio + tamanho_faixa
            faixas[label] = sum(
                1
                for v in precos_validos
                if inicio <= v < (fim + 1 if i == n_faixas - 1 else fim)
            )

        df_faixas = pd.DataFrame(
            {"Faixa": list(faixas.keys()), "Produtos": list(faixas.values())}
        )
        st.bar_chart(df_faixas.set_index("Faixa"), color="#AFA9EC", height=200)

    # --- Status bar ---
    st.markdown(
        f"""
    <div class="status-bar">
        última busca: {st.session_state.ultima_busca} · 
        termo: "{st.session_state.termo_atual}" · 
        {len(precos_validos)}/{len(produtos)} com preço disponível
    </div>
    """,
        unsafe_allow_html=True,
    )

else:
    # Estado inicial — nenhuma busca ainda
    st.markdown(
        """
    <div style="
        margin-top: 3rem;
        padding: 3rem;
        text-align: center;
        border: 1px dashed #e0e0dc;
        border-radius: 12px;
        color: #ccc;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">🔍</div>
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: #bbb;">
            Configure o produto na barra lateral e clique em <strong style="color:#999">▶ Executar busca</strong>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
