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

- ✅ **Sistema de Login** - 4 usuários pré-cadastrados (Cauã, Fabio, Jessica, Polyana)
- ✅ Orçamentos de adesivos (vinil branco, vinil transparente, papel couche)
- ✅ Orçamentos de apostilas
- ✅ Cálculo automático de preços com informações técnicas
- ✅ Geração de PDF com assinatura do usuário logado
- ✅ Relatório técnico completo
- ✅ **Integração Google Sheets** - Registro automático de orçamentos

## Arquivos do projeto

- `app.py` - Aplicativo principal
- `dados.json` - Configurações de preços
- `requirements.txt` - Dependências
- `README.md` - Instruções
- `.gitignore` - Arquivos ignorados pelo Git
- `cabecalho.png` / `rodape.png` - Imagens para PDF (opcional)
- `credenciais_google.json` - Credenciais do Google Cloud (não versionar!)

## Configuração Google Sheets (Opcional)

Para ativar o registro automático de orçamentos na planilha:

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com)
2. Ative as APIs: Google Sheets API e Google Drive API
3. Crie uma Service Account e baixe a chave JSON
4. Renomeie o arquivo para `credenciais_google.json`
5. Compartilhe sua planilha com o email da Service Account
6. Coloque o arquivo `credenciais_google.json` na pasta do projeto (não subir no GitHub!)

**Importante:** O arquivo `credenciais_google.json` está no `.gitignore` e não deve ser versionado por segurança.

## Usuários do Sistema

Usuários pré-cadastrados para login:
- Kauê
- Fabio
- Jessica
- Polyana

Cada usuário tem sua sessão independente. Ao sair, o carrinho é limpo automaticamente.