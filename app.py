import streamlit as st
import json
import math
import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# --- FUNÇÕES DE SISTEMA ---
def carregar_dados():
    if not os.path.exists('dados.json'): return {}
    try:
        with open('dados.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def salvar_dados(dados):
    with open('dados.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

if 'lista_pedidos' not in st.session_state:
    st.session_state.lista_pedidos = []
if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None
if 'contador_orcamentos' not in st.session_state:
    st.session_state.contador_orcamentos = 0

# Lista de usuários pré-cadastrados
USUARIOS = ["Kauê", "Fabio", "Jessica", "Polyana"]

def formatar_rs(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- FUNÇÕES DE PREÇO (NOVA ESTRUTURA) ---
def get_preco_corte(dados, formato_folha, tipo_corte, qtd_adesivos):
    """Busca preço de corte baseado na quantidade de adesivos"""
    precos = dados.get("preco_corte_por_quantidade_adesivos", [])
    formato_busca = "Super A3" if "SUPER" in formato_folha.upper() else "A4"
    
    for preco in precos:
        if (preco.get("formato_folha") == formato_busca and 
            preco.get("tipo_corte") == tipo_corte):
            faixa = preco.get("faixa_quantidade_adesivos", "")
            # Extrair min e max da faixa
            if "A partir de" in faixa:
                min_qtd = int(faixa.replace("A partir de ", "").replace("+", "").strip())
                if qtd_adesivos >= min_qtd:
                    return preco.get("preco_por_adesivo", 0)
            elif "De" in faixa and "a" in faixa:
                partes = faixa.replace("De ", "").replace(" a ", "-").split("-")
                if len(partes) == 2:
                    min_qtd = int(partes[0].strip())
                    max_qtd = int(partes[1].strip())
                    if min_qtd <= qtd_adesivos <= max_qtd:
                        return preco.get("preco_por_adesivo", 0)
    return 0

def get_preco_impressao(dados, formato_folha, tipo_material, qtd_folhas):
    """Busca preço de impressão baseado na quantidade de folhas"""
    if "vinil" in tipo_material.lower():
        precos = dados.get("preco_impressao_por_folha_vinil", [])
    else:
        precos = dados.get("preco_impressao_por_folha_couche", [])
    
    formato_busca = "Super A3" if "SUPER" in formato_folha.upper() else "A4"
    
    for preco in precos:
        if preco.get("formato_folha") == formato_busca:
            faixa = preco.get("faixa_quantidade_folhas", "")
            # Extrair min e max da faixa
            if "A partir de" in faixa:
                min_folhas = int(''.join(filter(str.isdigit, faixa.split()[3])))
                if qtd_folhas >= min_folhas:
                    return preco.get("preco_por_folha", 0)
            elif "De" in faixa and "a" in faixa:
                partes = faixa.replace("De ", "").replace(" a ", "-").split("-")
                if len(partes) == 2:
                    min_folhas = int(''.join(filter(str.isdigit, partes[0])))
                    max_folhas = int(''.join(filter(str.isdigit, partes[1])))
                    if min_folhas <= qtd_folhas <= max_folhas:
                        return preco.get("preco_por_folha", 0)
            elif "Até" in faixa:
                max_folhas = int(''.join(filter(str.isdigit, faixa)))
                if qtd_folhas <= max_folhas:
                    return preco.get("preco_por_folha", 0)
    return 0

# --- FUNÇÕES GOOGLE SHEETS ---
def get_next_id(worksheet):
    """Retorna próximo ID disponível na planilha"""
    try:
        values = worksheet.get_all_values()
        if len(values) <= 1:  # Só cabeçalho ou vazio
            return 1
        last_row = values[-1]
        last_id = int(last_row[0]) if last_row[0].isdigit() else 0
        return last_id + 1
    except:
        return 1

def registrar_orcamento_sheets(usuario, cliente, categoria, qtd_itens, valor_total, detalhes=""):
    """Registra orçamento no Google Sheets"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        if not os.path.exists('credenciais_google.json'):
            return False, "Arquivo de credenciais não encontrado"
        
        creds = Credentials.from_service_account_file('credenciais_google.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Abrir planilha pelo ID
        spreadsheet = client.open_by_key('17RHfcFEooYtfx6D5L_AEKVvos1RP5MuOZa9RAuVfMBY')
        worksheet = spreadsheet.sheet1
        
        # Verificar/criar cabeçalhos se planilha estiver vazia
        if len(worksheet.get_all_values()) == 0:
            worksheet.append_row(["ID", "Data", "Hora", "Usuário", "Cliente", 
                                 "Categoria", "Qtd Itens", "Valor Total", "Status", "Detalhes"])
        
        # Gerar próximo ID
        next_id = get_next_id(worksheet)
        
        # Dados do registro
        dados = [
            next_id,
            datetime.now().strftime("%d/%m/%Y"),
            datetime.now().strftime("%H:%M:%S"),
            usuario,
            cliente,
            categoria,
            qtd_itens,
            valor_total,
            "Concluído",
            detalhes
        ]
        
        worksheet.append_row(dados)
        return True, f"Registrado com ID {next_id}"
        
    except Exception as e:
        return False, str(e)

# --- GERAR PDF PERSONALIZADO ---
def gerar_pdf_cliente(lista_itens, valor_total, nome_cliente="", emissor=""):
    pdf = FPDF()
    pdf.add_page()
    
    try:
        if os.path.exists("cabecalho.png"):
            pdf.image("cabecalho.png", x=0, y=0, w=210)
    except:
        pass
    
    pdf.set_y(68) 
    pdf.set_font("Arial", "I", 10)
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 10, f"São Paulo, {data_hoje}", ln=True, align="R")
    
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 0, 0) 
    pdf.cell(0, 10, "ORÇAMENTO", ln=True, align="C")
    
    if nome_cliente:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, f"Cliente: {nome_cliente.upper()}", ln=True, align="L")
    
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(20, 8, "Qtd", border=0, fill=True, align='C')
    pdf.cell(130, 8, "Descrição", border=0, fill=True, align='L')
    pdf.cell(40, 8, "Subtotal", border=0, fill=True, align='R')
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 9)
    for item in lista_itens:
        if item.get("Categoria") == "Adesivos":
            desc = f"Adesivo {item['Tamanho']}cm {item['Formato']} - {item['Material']} ({item['Corte']})"
        elif item.get("Categoria") == "Apostilas":
            desc = f"Apostila {item['Formato']} - {item['Gramatura']} {item['Cor']} ({item['Páginas']}p) - {item['Encadernação']}"
        else:
            desc = "Item genérico"
        
        desc_safe = desc.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(20, 7, str(item['Qtd']), align='C')
        pdf.cell(130, 7, desc_safe, align='L')
        pdf.cell(40, 7, formatar_rs(item['Subtotal']), align='R')
        pdf.ln(7)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(1)
    
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "VALOR TOTAL:", align="R")
    pdf.cell(40, 10, formatar_rs(valor_total), align="R", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "CONDIÇÕES DE PAGAMENTO E PRAZOS:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, (
        "Pagamento: 50% de sinal e 50% na retirada\n"
        "Prazo: 01 dia útil após envio das artes e confirmação do pagamento do sinal\n"
        "Orçamento válido por 15 dias."
    ))
    
    pdf.set_y(255)
    pdf.set_font("Arial", "I", 10)
    texto_assinatura = f"Att. {emissor}" if emissor else "Att. Jéssica Camargo"
    pdf.cell(0, 10, texto_assinatura, ln=True, align="R")
    
    try:
        if os.path.exists("rodape.png"):
            pdf.set_auto_page_break(False, margin=0)
            pdf.image("rodape.png", x=0, y=265, w=210)
    except:
        pass
    
    # Salvar em arquivo temporário e ler como bytes
    pdf.output('temp_orcamento.pdf')
    with open('temp_orcamento.pdf', 'rb') as f:
        return f.read()

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Sistema Camargo Cópias", layout="wide")
dados = carregar_dados()

# --- TELA DE LOGIN ---
if not st.session_state.usuario_atual:
    st.title("🔐 Sistema de Orçamentos - Camargo Cópias")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 👤 Selecione seu usuário")
        
        usuario_selecionado = st.selectbox(
            "Selecione o usuário:", 
            USUARIOS,
            index=None,
            placeholder="Escolha seu nome...",
            label_visibility="collapsed"
        )
        
        if usuario_selecionado:
            if st.button("🔓 Entrar no Sistema", use_container_width=True, type="primary"):
                st.session_state.usuario_atual = usuario_selecionado
                st.success(f"Bem-vindo(a), {usuario_selecionado}!")
                st.rerun()
        else:
            st.info("Selecione um usuário para continuar")
    
    # Rodapé informativo
    st.markdown("---")
    st.caption("Sistema interno de orçamentos • Camargo Cópias")
    
    st.stop()

# --- INTERFACE PRINCIPAL (USUÁRIO LOGADO) ---
col_header1, col_header2 = st.columns([3, 1])

with col_header1:
    st.title("🎯 Sistema de Orçamentos")
    st.markdown(f"👤 **Usuário:** `{st.session_state.usuario_atual}`")

with col_header2:
    st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.usuario_atual = None
        st.session_state.lista_pedidos = []  # Limpa carrinho
        st.info("Você saiu do sistema. Até logo!")
        st.rerun()

aba_orc, aba_relatorio, aba_config = st.tabs(["📊 Calculadora", "📋 Relatório Técnico", "⚙️ Painel de Preços"])

with aba_orc:
    if not dados:
        st.error("Erro: arquivo dados.json não encontrado.")
    else:
        col_inf1 = st.columns(1)[0]
        with col_inf1:
            nome_c = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        
        # Seletor de Categoria
        categoria = st.selectbox("Categoria", ["Adesivos", "Apostilas"])
        
        if categoria == "Adesivos":
            c1, c2 = st.columns(2)
            with c1:
                qtd = st.number_input("Quantidade de Adesivos", min_value=1, value=100)
                tipo_corte = st.selectbox("Tipo de Corte", ["MEIO CORTE", "CORTE TOTAL"])
                opcoes_tamanho = list(dados.get("rendimentos", {}).get("A4", {}).get(tipo_corte, {}).keys())
                tamanho = st.selectbox("Tamanho (cm)", opcoes_tamanho) if opcoes_tamanho else "Erro"
                formato = st.selectbox("Formato", ["Quadrado", "Redondo"])
            with c2:
                material = st.selectbox("Material", ["papel couche", "vinil branco", "vinil transparente"])
                tem_arte = st.radio("Precisa de Arte?", ["SIM", "NÃO"], horizontal=True, index=1)
        
        elif categoria == "Apostilas":
            c1, c2 = st.columns(2)
            with c1:
                qtd_apostila = st.number_input("Quantidade de Apostilas", min_value=1, value=50)
                paginas = st.number_input("Número de Páginas", min_value=1, value=20)
                formato_apostila = st.selectbox("Formato", ["A4", "A5"])
                gramatura = st.selectbox("Gramatura do Papel", ["75g/m²", "90g/m²", "120g/m²", "180g/m²"])
            with c2:
                cor = st.selectbox("Impressão", ["Preto e Branco", "Colorido"])
                encadernacao = st.selectbox("Encadernação", ["Espiral", "Capa dura", "Grampeado", "Colado"])
                miolo_colorido = st.radio("Miolo colorido?", ["NÃO", "SIM"], horizontal=True, index=0) if cor == "Colorido" else None
                tem_capa = st.radio("Precisa de Capa Personalizada?", ["SIM", "NÃO"], horizontal=True, index=1)
        
        # CÁLCULO
        if categoria == "Adesivos":
            try:
                larg_cm = float(tamanho.split('x')[0].replace(',', '.'))
                papel = "SUPER A3" if (qtd >= 100 and larg_cm >= 6.5) else "A4"
                rend = dados["rendimentos"][papel][tipo_corte][tamanho]
                folhas = math.ceil(qtd / rend)
                # Novas funções de preço
                p_c = get_preco_corte(dados, papel, tipo_corte, qtd)
                tipo_material_preco = "vinil" if "vinil" in material else "couche"
                p_i = get_preco_impressao(dados, papel, tipo_material_preco, folhas)
                
                total_item = (qtd * p_c) + (folhas * p_i)
                if tem_arte == "SIM": total_item += dados["configuracoes"]["taxa_arte"]

                # Mostrar informações técnicas antes de adicionar
                st.info(f"📋 **Informações Técnicas:**\n\n📄 **Papel:** {papel}\n📃 **Folhas necessárias:** {folhas} folhas\n\n💰 **Cálculo:**\n• Corte: {formatar_rs(p_c)} x {qtd} un = {formatar_rs(qtd * p_c)}\n• Impressão: {formatar_rs(p_i)} x {folhas} folhas = {formatar_rs(folhas * p_i)}\n• Taxa Arte: {formatar_rs(dados['configuracoes']['taxa_arte']) if tem_arte == 'SIM' else 'R$ 0,00'}")

                if st.button("➕ Adicionar este Item", use_container_width=True):
                    st.session_state.lista_pedidos.append({
                        "Usuario": st.session_state.usuario_atual,
                        "Categoria": "Adesivos", "Qtd": qtd, "Tamanho": tamanho, "Formato": formato,
                        "Material": material, "Corte": tipo_corte, "Papel": papel, "Folhas": folhas,
                        "Rendimento": rend, "Preco_Corte_Un": p_c, "Preco_Impressao_Folha": p_i,
                        "Subtotal": total_item
                    })
                    st.rerun()
            except: pass
        
        elif categoria == "Apostilas":
            try:
                # Preço base por cópia
                preco_base = dados.get("apostilas", {}).get("preco_base", {}).get(cor.lower().replace(" ", "_"), 0.15)
                
                # Acréscimo por gramatura
                acrescimo_gramatura = dados.get("apostilas", {}).get("acrescimo_gramatura", {}).get(gramatura, 0)
                
                # Custo encadernação por unidade
                custo_encadernacao = dados.get("apostilas", {}).get("custo_encadernacao", {}).get(encadernacao.lower(), 2.0)
                
                # Custo capa personalizada
                custo_capa = dados.get("apostilas", {}).get("custo_capa", 5.0) if tem_capa == "SIM" else 0
                
                # Cálculo total
                total_item = (qtd_apostila * paginas * (preco_base + acrescimo_gramatura)) + (qtd_apostila * custo_encadernacao) + custo_capa

                if st.button("➕ Adicionar este Item", use_container_width=True):
                    st.session_state.lista_pedidos.append({
                        "Usuario": st.session_state.usuario_atual,
                        "Categoria": "Apostilas", "Qtd": qtd_apostila, "Páginas": paginas, 
                        "Formato": formato_apostila, "Gramatura": gramatura, "Cor": cor,
                        "Encadernação": encadernacao, "Capa Personalizada": tem_capa, "Subtotal": total_item
                    })
                    st.rerun()
            except: pass

    if st.session_state.lista_pedidos:
        st.divider()
        st.subheader("📋 Itens Selecionados")
        
        # --- TABELA COM OPÇÃO DE APAGAR ITEM POR ITEM ---
        for i, item in enumerate(st.session_state.lista_pedidos):
            col_item, col_btn = st.columns([9, 1])
            if item.get("Categoria") == "Adesivos":
                desc_v = f"{item['Qtd']}x Adesivo {item['Tamanho']}cm {item['Formato']} - {item['Material']} ({item['Corte']}) | **{formatar_rs(item['Subtotal'])}**"
            elif item.get("Categoria") == "Apostilas":
                desc_v = f"{item['Qtd']}x Apostilas ({item['Páginas']}p) - {item['Formato']} {item['Gramatura']} {item['Cor']} | **{formatar_rs(item['Subtotal'])}**"
            else:
                desc_v = f"{item.get('Qtd', 1)}x Item | **{formatar_rs(item['Subtotal'])}**"
            
            col_item.write(desc_v)
            if col_btn.button("🗑️", key=f"del_{i}"):
                st.session_state.lista_pedidos.pop(i)
                st.rerun()
        
        total_g = sum(item["Subtotal"] for item in st.session_state.lista_pedidos)
        st.divider()
        c_t, c_p, c_l = st.columns([2, 1, 1])
        c_t.metric("VALOR TOTAL", formatar_rs(total_g))
        
        with c_p:
            # Gera PDF com assinatura do usuário logado
            pdf_bytes = gerar_pdf_cliente(
                st.session_state.lista_pedidos, 
                total_g, 
                nome_c, 
                st.session_state.usuario_atual  # Usa usuário logado como emissor
            )
            
            # Botão de download
            if st.download_button("📄 Baixar PDF", data=pdf_bytes, 
                                file_name=f"orcamento_{nome_c}.pdf", 
                                mime="application/pdf"):
                # Registra no Google Sheets (não bloqueia se der erro)
                tipos_itens = ", ".join(set([item.get("Categoria", "Item") for item in st.session_state.lista_pedidos]))
                detalhes_resumo = f"{len(st.session_state.lista_pedidos)} itens: {tipos_itens}"
                
                sucesso, msg = registrar_orcamento_sheets(
                    st.session_state.usuario_atual,
                    nome_c,
                    tipos_itens,
                    len(st.session_state.lista_pedidos),
                    formatar_rs(total_g),
                    detalhes_resumo
                )
                
                if not sucesso:
                    st.warning(f"⚠️ PDF baixado! Mas não foi registrado no Sheets: {msg}")
                else:
                    st.success("✅ Orçamento registrado com sucesso!")
        
        if c_l.button("❌ Limpar Tudo"):
            st.session_state.lista_pedidos = []
            st.rerun()

with aba_relatorio:
    st.header("📋 Relatório Técnico")
    
    if not st.session_state.lista_pedidos:
        st.info("Nenhum item no orçamento. Adicione itens na aba Calculadora.")
    else:
        total_geral = sum(item["Subtotal"] for item in st.session_state.lista_pedidos)
        
        # Resumo compacto
        col1, col2, col3 = st.columns(3)
        col1.metric("Itens", len(st.session_state.lista_pedidos))
        col2.metric("Total", formatar_rs(total_geral))
        
        qtd_adesivos = sum(1 for item in st.session_state.lista_pedidos if item.get("Categoria") == "Adesivos")
        col3.metric("Adesivos", qtd_adesivos)
        
        st.divider()
        
        # Lista compacta de itens
        for i, item in enumerate(st.session_state.lista_pedidos, 1):
            if item.get("Categoria") == "Adesivos":
                with st.expander(f"Item {i}: {item['Qtd']}x Adesivo {item['Tamanho']}cm - {formatar_rs(item['Subtotal'])}"):
                    cols = st.columns([1, 1, 1, 1])
                    cols[0].write(f"**Papel:** {item.get('Papel', '-')}")
                    cols[1].write(f"**Folhas:** {item.get('Folhas', '-')}")
                    cols[2].write(f"**Material:** {item['Material']}")
                    cols[3].write(f"**Corte:** {item['Corte']}")
            elif item.get("Categoria") == "Apostilas":
                with st.expander(f"Item {i}: {item['Qtd']}x Apostila - {formatar_rs(item['Subtotal'])}"):
                    cols = st.columns([1, 1, 1, 1])
                    cols[0].write(f"**Páginas:** {item['Páginas']}")
                    cols[1].write(f"**Formato:** {item['Formato']}")
                    cols[2].write(f"**Gramatura:** {item['Gramatura']}")
                    cols[3].write(f"**Encadernação:** {item['Encadernação']}")

with aba_config:
    if dados:
        nova_arte = st.number_input("Valor da Arte (R$)", value=float(dados["configuracoes"]["taxa_arte"]))
        if st.button("Salvar Configuração"):
            dados["configuracoes"]["taxa_arte"] = nova_arte
            salvar_dados(dados)
            st.success("Salvo com sucesso!")