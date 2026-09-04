import streamlit as st
import datetime
import calendar
import json
import os

# 1. Configuração Inicial da Página
st.set_page_config(page_title="Dashboard - Mídia CGOD", layout="wide")

ARQUIVO_DADOS = "posts_dados.json"

# 2. Funções para salvar e carregar os dados
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# 3. Inicialização de Variáveis de Sessão
if 'posts' not in st.session_state:
    st.session_state.posts = carregar_dados()

if 'post_selecionado' not in st.session_state:
    st.session_state.post_selecionado = None

# Paleta de Cores/Emojis das Categorias
CATEGORIAS = {
    "Lote, Kit e Brindes": "🔵",
    "Local e Hotéis do Evento": "🟢",
    "Pessoas e Palestrantes": "🔴",
    "Cronograma": "🟠",
    "Atividades": "🟣"
}

data_hoje = datetime.date.today()
data_evento = datetime.date(2026, 10, 10)

# Sidebar para Logo
try:
    st.sidebar.image("Logo CGOD.jpg", use_column_width=True)
except:
    st.sidebar.warning("Arquivo 'Logo CGOD.jpg' não encontrado na pasta.")
st.sidebar.markdown("### XXXV Congresso Estadual")
st.sidebar.markdown("**Erechim - RS | 10 e 11 de Outubro**")

# 4. Janela Flutuante (Dialog) para Adicionar Post
@st.dialog("Cadastrar Novo Post")
def janela_adicionar_post():
    titulo = st.text_input("Título do Post")
    responsavel = st.text_input("Responsável")
    data_post = st.date_input("Data da Postagem", value=data_hoje)
    categoria = st.selectbox("Categoria", list(CATEGORIAS.keys()))
    
    if st.button("Salvar Post", type="primary"):
        if titulo and responsavel:
            novo_post = {
                "id": len(st.session_state.posts) + 1,
                "titulo": titulo,
                "responsavel": responsavel,
                "data": data_post.strftime("%Y-%m-%d"),
                "categoria": categoria,
                "status": "Programado"
            }
            st.session_state.posts.append(novo_post)
            salvar_dados(st.session_state.posts)
            st.success("Post adicionado com sucesso!")
            st.rerun()
        else:
            st.error("Preencha o título e o responsável.")

# 5. Divisão em Abas (Dashboard e Cronograma)
aba1, aba2 = st.tabs(["📊 Dashboard Geral", "📅 Cronograma de Posts"])

# ================= ABA 1: DASHBOARD =================
with aba1:
    st.header("Visão Geral das Postagens")
    
    # Contadores lógicos
    total_programados = 0
    total_concluidos = 0
    total_atrasados = 0
    
    # Atualiza virtualmente o status caso a data tenha passado
    for p in st.session_state.posts:
        data_p = datetime.datetime.strptime(p['data'], "%Y-%m-%d").date()
        if p['status'] == 'Concluído':
            total_concluidos += 1
        elif data_p < data_hoje and p['status'] != 'Concluído':
            total_atrasados += 1
            p['status'] = 'Atrasado'
        else:
            total_programados += 1

    dias_restantes = (data_evento - data_hoje).days
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📌 Posts Programados", total_programados)
    col2.metric("⚠️ Posts Atrasados", total_atrasados)
    col3.metric("✅ Posts Concluídos", total_concluidos)
    col4.metric("⏳ Dias para o Evento", dias_restantes if dias_restantes >= 0 else 0)
    
    st.divider()
    
    st.subheader("Próximas 5 Postagens")
    # Filtra as não concluídas e ordena pelas mais próximas
    posts_pendentes = [p for p in st.session_state.posts if p['status'] != 'Concluído']
    posts_pendentes.sort(key=lambda x: datetime.datetime.strptime(x['data'], "%Y-%m-%d").date())
    
    if not posts_pendentes:
        st.info("Nenhuma postagem pendente no momento!")
    else:
        for p in posts_pendentes[:5]:
            icone = CATEGORIAS.get(p['categoria'], "⚪")
            data_formatada = datetime.datetime.strptime(p['data'], "%Y-%m-%d").strftime("%d/%m/%Y")
            st.markdown(f"**{icone} {data_formatada}** — **{p['titulo']}** | *Responsável: {p['responsavel']}* ({p['status']})")

# ================= ABA 2: CRONOGRAMA =================
with aba2:
    topo_esq, topo_dir = st.columns([4, 1])
    with topo_esq:
        st.header("Calendário de Publicações")
    with topo_dir:
        if st.button("➕ Adicionar Post", use_container_width=True, type="primary"):
            janela_adicionar_post()

    # Seleção de mês específico para renderizar o grid
    mes_opcao = st.radio("Selecione o mês para visualizar:", ["Setembro 2026", "Outubro 2026"], horizontal=True)
    
    ano_alvo = 2026
    mes_alvo = 9 if mes_opcao == "Setembro 2026" else 10
    
    # Criar a estrutura do calendário nativamente em blocos
    cal = calendar.monthcalendar(ano_alvo, mes_alvo)
    dias_da_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    
    # Cabeçalho dos dias da semana
    colunas_semana = st.columns(7)
    for i, nome_dia in enumerate(dias_da_semana):
        colunas_semana[i].markdown(f"<div style='text-align: center; font-weight: bold;'>{nome_dia}</div>", unsafe_allow_html=True)
    st.write("---")
    
    # Renderizando as semanas e os dias
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia != 0: # Dia válido do mês
                    # Cria um container/bloco visual
                    container_dia = st.container(border=True)
                    container_dia.markdown(f"**{dia}**")
                    
                    data_str = f"{ano_alvo}-{mes_alvo:02d}-{dia:02d}"
                    posts_do_dia = [p for p in st.session_state.posts if p['data'] == data_str]
                    
                    # Exibe botão para cada post agendado naquele dia
                    for p in posts_do_dia:
                        icone = CATEGORIAS.get(p['categoria'], "📄")
                        # Se houver mais de um post no mesmo dia, os botões empilham verticalmente
                        if container_dia.button(f"{icone} {p['titulo']}", key=f"btn_{p['id']}", help=p['categoria'], use_container_width=True):
                            st.session_state.post_selecionado = p

    # Janela inferior de Informações do Post Clicado
    if st.session_state.post_selecionado:
        st.divider()
        st.subheader("Detalhes da Postagem Selecionada")
        p = st.session_state.post_selecionado
        
        info_col1, info_col2 = st.columns(2)
        info_col1.markdown(f"**Título:** {p['titulo']}")
        info_col1.markdown(f"**Data Agendada:** {datetime.datetime.strptime(p['data'], '%Y-%m-%d').strftime('%d/%m/%Y')}")
        info_col1.markdown(f"**Responsável:** {p['responsavel']}")
        
        icone_cat = CATEGORIAS.get(p['categoria'], "")
        info_col2.markdown(f"**Categoria:** {icone_cat} {p['categoria']}")
        
        novo_status = info_col2.selectbox(
            "Atualizar Status", 
            ["Programado", "Concluído", "Atrasado"], 
            index=["Programado", "Concluído", "Atrasado"].index(p['status']),
            key="status_post"
        )
                                   
        if st.button("Salvar Alteração de Status"):
            # Procura o post na base e altera
            for idx, post in enumerate(st.session_state.posts):
                if post['id'] == p['id']:
                    st.session_state.posts[idx]['status'] = novo_status
                    st.session_state.post_selecionado['status'] = novo_status
                    salvar_dados(st.session_state.posts)
            st.success("Status atualizado com sucesso!")
            st.rerun()
