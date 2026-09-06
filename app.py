import streamlit as st
import datetime
import calendar
import json
import os
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import time

# 1. Configuração Inicial
st.set_page_config(page_title="Mídia CGOD XXXV", layout="wide", initial_sidebar_state="expanded")

ARQUIVO_DADOS = "posts_dados.json"

# Cores e Categorias
CATEGORIAS_INFO = {
    "Lote, Kit e Brindes": {"cor": "#3498db", "emoji": "🔵"},
    "Local e Hotéis do Evento": {"cor": "#2ecc71", "emoji": "🟢"},
    "Pessoas e Palestrantes": {"cor": "#e74c3c", "emoji": "🔴"},
    "Cronograma": {"cor": "#f39c12", "emoji": "🟠"},
    "Atividades": {"cor": "#9b59b6", "emoji": "🟣"}
}

# Configuração de Status
STATUS_EMOJIS = {"Programado": "🟡", "Concluído": "🟢", "Atrasado": "🔴"}
STATUS_COLORS = {"Programado": "#f1c40f", "Concluído": "#2ecc71", "Atrasado": "#e74c3c"}

def formatar_categoria(cat):
    return f"{CATEGORIAS_INFO[cat]['emoji']} {cat}"

# Função para renderizar o botão do Cronograma
def renderizar_botao_cronograma(p):
    icone_status = STATUS_EMOJIS[p['status']]
    
    if st.button(f"{icone_status} {p['titulo']}", key=f"cal_btn_{p['id']}", use_container_width=True):
        st.session_state.post_selecionado_id = p['id']
        st.session_state.edit_mode = False
        st.session_state.scroll_trigger = time.time()
        st.rerun()

# 2. Funções de Dados
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicialização de variáveis globais
if 'posts' not in st.session_state:
    st.session_state.posts = carregar_dados()
if 'post_selecionado_id' not in st.session_state:
    st.session_state.post_selecionado_id = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'scroll_trigger' not in st.session_state:
    st.session_state.scroll_trigger = 0

data_hoje = datetime.date.today()
data_evento = datetime.date(2026, 10, 10)
data_inicio_contagem = datetime.date(2026, 9, 5) 

# 3. Sidebar (Navegação e Logo)
with st.sidebar:
    logo_options = ["Logo CGOD.jpg", "logo_cgod.png", "logo_cgod.jpg"]
    logo_path = next((path for path in logo_options if os.path.exists(path)), None)
    
    if logo_path:
        try:
            st.image(logo_path, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao ler imagem: {e}")
    else:
        st.warning("Arquivo 'Logo CGOD.jpg' não encontrado.")
    
    st.title("Navegação")
    tela = st.radio("Selecione a tela:", ["📊 Dashboard Geral", "📅 Cronograma de Posts"])
    
    st.divider()
    st.markdown("### XXXV Congresso Estadual")
    st.caption("Erechim - RS | 10 e 11 de Outubro")

# 4. Diálogos Flutuantes (Cadastro e Exclusão)
@st.dialog("Cadastrar Novo Post")
def janela_adicionar_post():
    t = st.text_input("Título do Post")
    r = st.text_input("Responsável")
    c = st.selectbox("Categoria", list(CATEGORIAS_INFO.keys()), format_func=formatar_categoria)
    d = st.date_input("Data", value=data_hoje)
    
    desc = st.text_area("Descrição do Post")
    ori = st.text_area("Orientações")
    link = st.text_input("Link da Postagem (Opcional)")
    
    if st.button("Salvar", type="primary"):
        novo = {
            "id": int(datetime.datetime.now().timestamp()), 
            "titulo": t, 
            "responsavel": r, 
            "data": d.strftime("%Y-%m-%d"), 
            "categoria": c, 
            "status": "Programado",
            "descricao": desc,
            "orientacoes": ori,
            "link": link
        }
        st.session_state.posts.append(novo)
        salvar_dados(st.session_state.posts)
        st.rerun()

@st.dialog("Confirmar Exclusão")
def janela_confirmar_exclusao(post_id):
    st.warning("⚠️ Tem certeza que deseja excluir esta postagem? Essa ação não poderá ser desfeita.")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Sim, Excluir", type="primary", use_container_width=True):
            st.session_state.posts = [p for p in st.session_state.posts if p['id'] != post_id]
            salvar_dados(st.session_state.posts)
            st.session_state.post_selecionado_id = None
            st.session_state.edit_mode = False
            st.success("Postagem excluída com sucesso!")
            time.sleep(0.5)
            st.rerun()
    with col_c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()

# 5. Lógica de atualização de Atrasos
total = len(st.session_state.posts)
df = pd.DataFrame(st.session_state.posts) if total > 0 else pd.DataFrame(columns=['status', 'data', 'categoria', 'link'])

if not df.empty:
    df['data_dt'] = pd.to_datetime(df['data']).dt.date
    df.loc[(df['data_dt'] < data_hoje) & (df['status'] == 'Programado'), 'status'] = 'Atrasado'
    
    for post in st.session_state.posts:
        if datetime.datetime.strptime(post['data'], "%Y-%m-%d").date() < data_hoje and post['status'] == 'Programado':
            post['status'] = 'Atrasado'

# ================= TELA: DASHBOARD =================
if tela == "📊 Dashboard Geral":
    st.header("Dashboard Analítico de Mídia")
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        dias_faltam = (data_evento - data_hoje).days
        st.metric("⏳ Dias para o Evento", f"{dias_faltam} dias")
        
        total_dias_escala = (data_evento - data_inicio_contagem).days
        dias_passados = (data_hoje - data_inicio_contagem).days
        progresso = min(max(dias_passados / total_dias_escala if total_dias_escala > 0 else 1.0, 0.0), 1.0)
        
        if dias_faltam < 0:
            msg = "O Congresso já passou! 🎉"
        elif dias_faltam == 0:
            msg = "O Congresso é hoje! 🔥"
        elif dias_faltam == 1:
            msg = "O Congresso é amanhã! Últimos preparativos!"
        elif dias_faltam <= 7:
            msg = f"Faltam apenas {dias_faltam} dias! Reta final!"
        else:
            semanas = dias_faltam // 7
            msg = f"Estamos a {semanas} semana{'s' if semanas > 1 else ''} do congresso. Bora produzir nossos posts!"
            
        st.progress(progresso, text=msg)

    with col_m2:
        if not df.empty:
            fig = px.pie(df, names='status', title="Status das Postagens", 
                         color='status', color_discrete_map=STATUS_COLORS,
                         hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont=dict(color="white", size=14))
            fig.update_layout(height=250, margin=dict(l=0, r=0, b=0, t=30))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Adicione posts para ver os gráficos.")

    st.divider()
    
    st.subheader("🗓️ Próximas Postagens (Linha do Tempo)")
    if not df.empty:
        futuros = df[df['status'] != 'Concluído'].sort_values('data').head(5)
        col_list = st.columns(len(futuros) if len(futuros) > 0 else 1)
        
        for idx, (i, row) in enumerate(futuros.iterrows()):
            cor_categoria = CATEGORIAS_INFO[row['categoria']]['cor']
            icone_status = STATUS_EMOJIS[row['status']]
            
            with col_list[idx]:
                st.markdown(f"""
                    <div style="background-color: #262730; border-top: 5px solid {cor_categoria}; padding: 12px; border-radius: 8px; color: white; min-height: 85px; box-shadow: 2px 2px 5px rgba(0,0,0,0.15); margin-bottom: 5px;">
                        <small style="opacity: 0.8;">{datetime.datetime.strptime(row['data'], '%Y-%m-%d').strftime('%d/%m')}</small><br>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <span style="font-size: 14px;">{icone_status}</span>
                            <strong style="font-size: 14px;">{row['titulo']}</strong>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("Ver Detalhes", key=f"dash_btn_{row['id']}", use_container_width=True):
                    st.session_state.post_selecionado_id = row['id']
                    st.session_state.edit_mode = False
                    st.session_state.scroll_trigger = time.time()
                    st.rerun()
    else:
        st.info("Nenhum post futuro programado.")

# ================= TELA: CRONOGRAMA =================
else:
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1: st.header("Calendário de Postagens")
    with col_t2: 
        if st.button("➕ Adicionar Post", use_container_width=True, type="primary"):
            janela_adicionar_post()

    mes_view = st.radio("Mês:", ["Setembro 2026", "Outubro 2026"], horizontal=True)
    mes_num = 9 if "Setembro" in mes_view else 10
    
    cal = calendar.monthcalendar(2026, mes_num)
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    
    cols_header = st.columns(7)
    for i, d in enumerate(dias_semana): cols_header[i].markdown(f"**{d}**")

    for semana in cal:
        cols = st.columns(7)
        
        # 1. Identificar o número máximo de posts nos dias desta semana
        max_posts_na_semana = 0
        for dia in semana:
            if dia != 0:
                qtd = sum(1 for p in st.session_state.posts if p['data'] == f"2026-{mes_num:02d}-{dia:02d}")
                if qtd > max_posts_na_semana:
                    max_posts_na_semana = qtd
        
        # 2. Define a altura exata em pixels para nivelar todos os 7 dias da semana
        altura_container = max(130, 65 + max_posts_na_semana * 60)

        for i, dia in enumerate(semana):
            with cols[i]:
                # O container com altura explícita garante que todos os dias fiquem perfeitamente alinhados
                with st.container(height=altura_container, border=True):
                    if dia == 0:
                        st.markdown("&nbsp;")
                    else:
                        st.markdown(f"**{dia}**")
                        data_str = f"2026-{mes_num:02d}-{dia:02d}"
                        posts_dia = [p for p in st.session_state.posts if p['data'] == data_str]
                        
                        for p in posts_dia:
                            renderizar_botao_cronograma(p)

# ================= DETALHES DO POST GLOBAL =================
if st.session_state.post_selecionado_id:
    st.markdown("<div id='ancora_detalhes' style='padding-top: 20px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.scroll_trigger > 0:
        components.html(f"""
            <script>
                setTimeout(function() {{
                    const elements = window.parent.document.querySelectorAll('#ancora_detalhes');
                    if (elements.length > 0) {{
                        elements[elements.length - 1].scrollIntoView({{behavior: 'smooth', block: 'start'}});
                    }}
                }}, 300);
            </script>
        """, height=0, width=0)
        st.session_state.scroll_trigger = 0 
    
    st.divider()
    post_idx = next((i for i, item in enumerate(st.session_state.posts) if item["id"] == st.session_state.post_selecionado_id), None)
    
    if post_idx is not None:
        p = st.session_state.posts[post_idx]
        
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            with c1: 
                icone_status = STATUS_EMOJIS[p['status']]
                st.subheader(f"{icone_status} {p['titulo']}")
            with c2:
                if not st.session_state.edit_mode:
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("📝 Editar Post", use_container_width=True):
                            st.session_state.edit_mode = True
                            st.rerun()
                    with col_b2:
                        if st.button("🗑️ Excluir", use_container_width=True):
                            janela_confirmar_exclusao(p['id'])
                else:
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        if st.button("💾 Salvar", type="primary", use_container_width=True):
                            st.session_state.edit_mode = False
                            salvar_dados(st.session_state.posts)
                            st.success("Post atualizado!")
                            st.rerun()
                    with col_s2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state.edit_mode = False
                            st.rerun()

            if st.session_state.edit_mode:
                col_e1, col_e2 = st.columns(2)
                p['titulo'] = col_e1.text_input("Título", p['titulo'])
                p['responsavel'] = col_e1.text_input("Responsável", p['responsavel'])
                p['link'] = col_e1.text_input("Link da Postagem", p.get('link', ''))
                
                p['data'] = col_e2.date_input("Data", datetime.datetime.strptime(p['data'], '%Y-%m-%d')).strftime("%Y-%m-%d")
                p['categoria'] = col_e2.selectbox("Categoria", list(CATEGORIAS_INFO.keys()), index=list(CATEGORIAS_INFO.keys()).index(p['categoria']), format_func=formatar_categoria)
                p['status'] = col_e2.selectbox("Status", ["Programado", "Concluído", "Atrasado"], index=["Programado", "Concluído", "Atrasado"].index(p['status']))
                
                p['descricao'] = st.text_area("Descrição do Post", p.get('descricao', ''))
                p['orientacoes'] = st.text_area("Orientações", p.get('orientacoes', ''))
            
            else:
                col_v1, col_v2 = st.columns(2)
                col_v1.markdown(f"**Responsável:** {p['responsavel']}")
                col_v1.markdown(f"**Data:** {datetime.datetime.strptime(p['data'], '%Y-%m-%d').strftime('%d/%m/%Y')}")
                
                link_text = p.get('link', '').strip()
                if link_text:
                    col_v1.markdown(f"**Link:** [Acessar Publicação]({link_text})")
                else:
                    col_v1.markdown("**Link:** *Não informado*")
                    
                col_v2.markdown(f"**Categoria:** {formatar_categoria(p['categoria'])}")
                
                cor_status = STATUS_COLORS.get(p['status'], "white")
                col_v2.markdown(f"**Status:** <span style='background-color:{cor_status}; color:white; padding: 2px 8px; border-radius: 12px; font-weight:bold; font-size:12px;'>{p['status']}</span>", unsafe_allow_html=True)
                
                st.write("---")
                col_t1, col_t2 = st.columns(2)
                
                desc_text = p.get('descricao', '').strip()
                ori_text = p.get('orientacoes', '').strip()
                
                with col_t1:
                    st.markdown("**Descrição do Post:**")
                    if desc_text:
                        st.info(desc_text)
                    else:
                        st.info("Descrição não informada.")
                with col_t2:
                    st.markdown("**Orientações:**")
                    if ori_text:
                        st.warning(ori_text)
                    else:
                        st.warning("Orientação não informada.")
