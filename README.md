# 🛒 Web Automation Bot

Projeto de automação web desenvolvido em Python utilizando Playwright para coleta de dados de produtos.

---

## 📌 Descrição

Este projeto realiza buscas automatizadas na Amazon, coletando informações como título e preço dos produtos, com opção de exportação dos dados.

---

## ⚙️ Funcionalidades

### ✅ Implementadas
- Busca de produtos na Amazon
- Coleta de título e preço
- Exibição dos resultados no terminal
- Exportação para CSV

### 🚧 Em desenvolvimento
- Sistema de logs
- Alertas automáticos (Telegram / E-mail)
- Execução agendada (cron)
- Exportação em JSON
- Interface para o usuário (futuro)

---

## 🧰 Tecnologias utilizadas

- Python
- Playwright

---

## 🚀 Como executar

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/web-automation-bot.git

# Entrar na pasta
cd web-automation-bot

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers do Playwright
playwright install

# Executar o projeto
python src/main.py
