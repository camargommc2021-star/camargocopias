# Sistema de Orçamentos - Camargo Cópias

Sistema web para criação de orçamentos de adesivos e apostilas.

## Deploy no Streamlit Cloud

### Passo 1: Criar repositório no GitHub

1. Acesse https://github.com/new
2. Nome do repositório: `sistema-orcamentos` (ou qualquer nome)
3. Deixe público
4. Clique em "Create repository"

### Passo 2: Enviar código para o GitHub

No terminal, dentro da pasta do projeto, execute:

```bash
git init
git add .
git commit -m "Primeiro commit"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/sistema-orcamentos.git
git push -u origin main
```

Substitua `SEU-USUARIO` pelo seu nome de usuário do GitHub.

### Passo 3: Deploy no Streamlit Cloud

1. Acesse https://streamlit.io/cloud
2. Faça login com sua conta GitHub
3. Clique em "Create app"
4. Selecione:
   - Repository: `SEU-USUARIO/sistema-orcamentos`
   - Branch: `main`
   - Main file path: `app.py`
5. Escolha um nome para o app (ex: `sistema-orcamentos`)
6. Clique em "Deploy"

Pronto! Seu app estará online em poucos segundos!

## Funcionalidades

- ✅ Orçamentos de adesivos (vinil branco, vinil transparente, papel couche)
- ✅ Orçamentos de apostilas
- ✅ Cálculo automático de preços
- ✅ Geração de PDF
- ✅ Relatório técnico completo

## Arquivos do projeto

- `app.py` - Aplicativo principal
- `dados.json` - Configurações de preços
- `requirements.txt` - Dependências
- `cabecalho.png` / `rodape.png` - Imagens para PDF (opcional)