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

def formatar_rs(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

st.title("🎯 Sistema de Orçamentos")

aba_orc, aba_relatorio, aba_config = st.tabs(["📊 Calculadora", "📋 Relatório Técnico", "⚙️ Painel de Preços"])

with aba_orc:
    if not dados:
        st.error("Erro: arquivo dados.json não encontrado.")
    else:
        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            nome_c = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        with col_inf2:
            nome_emissor = st.text_input("Nome para assinatura (Att.)", value="Jéssica Camargo")
        
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
                p_c = next((f["valor"] for f in dados["precos_corte"] if f["formato"] == papel and f["tipo"] == tipo_corte and f["min"] <= qtd <= f["max"]), 0)
                # Mapear material para tipo de preço (vinil branco e transparente usam preço de vinil)
                tipo_material_preco = "vinil" if "vinil" in material else "couche"
                p_i = next((f["valor"] for f in dados["precos_impressao"][tipo_material_preco][papel] if f["min"] <= folhas <= f["max"]), 0)
                
                total_item = (qtd * p_c) + (folhas * p_i)
                if tem_arte == "SIM": total_item += dados["configuracoes"]["taxa_arte"]

                # Mostrar informações técnicas antes de adicionar
                st.info(f"📋 **Informações Técnicas:**\n\n📄 **Papel:** {papel}\n📃 **Folhas necessárias:** {folhas} folhas\n\n💰 **Cálculo:**\n• Corte: {formatar_rs(p_c)} x {qtd} un = {formatar_rs(qtd * p_c)}\n• Impressão: {formatar_rs(p_i)} x {folhas} folhas = {formatar_rs(folhas * p_i)}\n• Taxa Arte: {formatar_rs(dados['configuracoes']['taxa_arte']) if tem_arte == 'SIM' else 'R$ 0,00'}")

                if st.button("➕ Adicionar este Item", use_container_width=True):
                    st.session_state.lista_pedidos.append({
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
            pdf_bytes = gerar_pdf_cliente(st.session_state.lista_pedidos, total_g, nome_c, nome_emissor)
            st.download_button("📄 Baixar PDF", data=pdf_bytes, file_name=f"orcamento_{nome_c}.pdf", mime="application/pdf")
        
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