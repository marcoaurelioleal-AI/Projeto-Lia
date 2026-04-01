import os
import sys 
import streamlit as st 
import google.generativeai as genai
from dotenv import load_dotenv

# 1. CARREGAR CONFIGURAÇÕES
load_dotenv()
CHAVE_API = os.getenv("CHAVE_API")
SENHA_CORRETA = os.getenv("SENHA_ACESSO")

if not CHAVE_API or not SENHA_CORRETA:
    st.error("❌ ERRO: Verifique seu arquivo .env (A chave do Google CHAVE_API está faltando)")
    sys.exit()

genai.configure(api_key=CHAVE_API)

# 2. DESIGN E CSS (Alinhamento de Elite)
st.set_page_config(page_title="Dashboard Grupo Lia", page_icon="🍔", layout="wide")

st.markdown("""
    <style>
    /* Fundo e Fontes */
    .stApp { background: linear-gradient(180deg, #1A050A 0%, #380A15 100%); }
    
    /* Alinhamento da Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #2D0811 !important;
        border-right: 2px solid #CC2936;
        text-align: center;
    }
    
    /* Centralizando imagens na Sidebar */
    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
        border-radius: 10px;
        transition: 0.3s;
    }

    /* Estilização das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px 10px 0 0;
        padding: 10px 30px;
        color: #FBF6E9;
    }
    .stTabs [aria-selected="true"] {
        background-color: #CC2936 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>🔑 Grupo Lia</h1>", unsafe_allow_html=True)
        senha = st.text_input("Senha de Acesso:", type="password")
        if st.button("Entrar no Sistema", use_container_width=True):
            if senha == SENHA_CORRETA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha inválida!")
    st.stop()

# 3. 🧠 MENTE DA IA (VOLTANDO PARA O GEMINI 2.5 FLASH)
manual_instrucao = (
    "Você é o Diretor Operacional e Chef Executivo do Grupo Lia. Sua autoridade é máxima. "
    "Ao ser questionado por funcionários, você deve fornecer respostas diretas e objetivas, mas sempre com um toque de mentor e encorajamento. "
    "Se falarem de hambúrguer, fale de temperatura da chapa, tempo de descanso da carne e montagem. "
    "Se falarem de processos, explique o 'porquê' de cada passo. "
    "Nunca dê respostas de apenas uma linha. Use listas, negrito e tabelas se necessário. "
    "Seu tom é mentor, técnico e encorajador. Use emojis 🍕🍔🥟."
)

modelo = genai.GenerativeModel('gemini-2.5-flash', system_instruction=manual_instrucao)

# --- BARRA LATERAL ALINHADA ---
with st.sidebar:
    st.markdown("## 🏢 PAINEL")
    st.divider()
    
    col_side1, col_side2, col_side3 = st.columns([1, 4, 1])
    with col_side2:
        try:
            st.image("./assets/logo_burger.png", width=120)
            st.image("./assets/logo_salgados.png", width=120)
            st.image("./assets/logo_pizza.png", width=120)
        except: st.error("Logos não encontradas")
    
    st.divider()
    if st.button("🚪 Encerrar Turno", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# --- ÁREA PRINCIPAL COM ABAS ---
aba_chat, aba_receitas, aba_tarefas = st.tabs(["💬 CONSULTORIA IA", "📚 MANUAIS TÉCNICOS", "📋 TAREFAS"])

with aba_chat:
    st.markdown("<h2 style='text-align: center;'>Assistente Operacional Lia</h2>", unsafe_allow_html=True)
    
    if "chat" not in st.session_state:
        st.session_state.chat = modelo.start_chat(history=[])
    
    for msg in st.session_state.chat.history:
        papel = "assistant" if msg.role == "model" else "user"
        with st.chat_message(papel): st.markdown(msg.parts[0].text)
    
    pergunta = st.chat_input("Dúvida técnica ou operacional?")
    if pergunta:
        with st.chat_message("user"): st.markdown(pergunta)
        with st.chat_message("assistant"):
            try:
                resposta = st.session_state.chat.send_message(pergunta)
                st.markdown(resposta.text)
            except Exception as e:
                st.error(f"⚠️ Erro ao processar sua pergunta: {str(e)}")
                st.warning("💡 Dica: Se for erro de cota excedida (429), aguarde alguns minutos antes de tentar novamente.")

with aba_receitas:
    st.header("📚 Livro de Procedimentos")
    st.markdown("---")
    escolha = st.selectbox("Selecione a Unidade:", ["Lia Burguer", "Lia Pizza", "Lia Salgados"])
    
    if escolha == "Lia Burguer":
        st.subheader("🔥 Procedimento de Chapa")
        st.write("- **Temperatura:** 200°C constante.")
        st.write("- **Tempos:** 2:30 min de cada lado para ponto médio.")
        st.info("Dica: Nunca pressione a carne com a espátula para não perder o suco.")

with aba_tarefas:
    tab_limpeza, tab_delivery = st.tabs(["🧹 LIMPEZA DA LOJA", "🚚 ATENDIMENTO DELIVERY"])
    
    with tab_limpeza:
        st.header("📋 CHECKLIST LIMPEZA DA LOJA")
        st.divider()
        
        st.subheader("📅 SEGUNDA-FEIRA")
        col1, col2 = st.columns([0.05, 0.95])
        with col1: st.write("")
        with col2:
            st.checkbox("🧊 LIMPEZA DAS GELADEIRAS DE REFRIGERANTE (NO DOMINGO NÃO DEVE ABASTECER PARA QUE FACILITE NA LIMPEZA)")
            st.checkbox("📦 RETIRAR ITENS DO ARMÁRIO PRETO E FAZER A LIMPEZA DO MESMO")
            st.checkbox("🥤 ORGANIZAR E VERIFICAR VALIDADE DAS BEBIDAS")
        
        st.divider()
        
        st.subheader("⭐ DIARIAMENTE")
        col1, col2 = st.columns([0.05, 0.95])
        with col1: st.write("")
        with col2:
            st.checkbox("🏪 A FRENTE DA LOJA DEVE SER LAVADA")
            st.checkbox("🧹 BALCÕES LIMPOS NO INÍCIO, DURANTE E FIM DO EXPEDIENTE")
            st.checkbox("🧽 LIMPEZA DAS PAREDES, CASO NECESSÁRIO")
            st.checkbox("🔧 ORGANIZAÇÃO E LIMPEZA NA PARTE DEBAIXO DO BALCÃO")
        
        st.divider()
        
        st.subheader("🎉 SEXTA-FEIRA")
        col1, col2 = st.columns([0.05, 0.95])
        with col1: st.write("")
        with col2:
            st.checkbox("🧹 LAVAGEM DAS DUAS LOJAS")
            st.checkbox("🍽️ LAVAR BANDEJAS")
            st.checkbox("🛡️ LAVAR PORTA MOLHOS/GUARDANAPOS")
    
    with tab_delivery:
        st.header("📋 CHECKLIST ATENDIMENTO DELIVERY")
        st.divider()
        
        st.subheader("⭐ DIARIAMENTE")
        col1, col2 = st.columns([0.05, 0.95])
        with col1: st.write("")
        with col2:
            st.checkbox("💬 Verificar mensagens pendentes")
            st.checkbox("⏱️ Verificar Tempo de entrega")
            st.checkbox("📋 Verificar Cardápio da pizza e salgado")
            st.checkbox("📊 Preparar relatórios e Planilha de motoboys")
            st.checkbox("💵 Abrir os 3 caixas")
            st.checkbox("⭐ Enviar avaliações do iFood e WhatsApp")
            st.checkbox("📢 Mandar Falaaê pendentes do dia anterior")
            st.checkbox("💰 Pedir dinheiro a Geise para pagamento de motoboys (na sexta pedir a mais para o fim de semana)")
            st.checkbox("🥫 Fazer molho (mínimo de duas caixas na loja)")
            st.checkbox("🔄 Verificar se tem máquinas para troca")
            st.checkbox("❄️ Aos fins de semana colocar refrigerantes no freezer da fábrica")
            st.checkbox("☔ Encapar maquininhas em dias de chuva")
            st.checkbox("🔌 Colocar máquinas para carregar")
        
        st.divider()
        
        st.subheader("🔒 FECHAMENTO")
        col1, col2 = st.columns([0.05, 0.95])
        with col1: st.write("")
        with col2:
            st.checkbox("💳 Iniciar o fechamento dos caixas a partir de 22:30")
            st.checkbox("💸 Fazer o pagamento dos motoboys")
            st.checkbox("📧 Enviar relatórios")
            st.checkbox("🗑️ Retirar o lixo")
            st.checkbox("❌ Desligar o ar-condicionado")
            st.checkbox("📦 Organização para o próximo dia")
