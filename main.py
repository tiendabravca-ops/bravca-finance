import streamlit as st
import os
import database
import modules.dashboard as dash
import modules.proyecciones as proj
import modules.historico as hist
import modules.fondos as fnd
import modules.cierres as cierres
import modules.obligaciones as obs
import modules.crypto_alertas as crypto_mod  # <--- 1. Importar el módulo de criptomonedas

st.set_page_config(
    page_title="brá'ca Financial Core", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS - Paleta Oficial brá'ca Souvenir (Monteverde Clean Corporate)
st.markdown("""
    <style>
    .stApp {
        background-color: #F7F5F0;
        color: #1C2826;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #EFECE6 !important;
        border-right: 1px solid #DCD7CE;
    }
    .brabca-card {
        background-color: #FFFFFF;
        border: 1px solid #E2DED6;
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 4px 12px rgba(30, 63, 32, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .brabca-card:hover {
        box-shadow: 0 6px 18px rgba(30, 63, 32, 0.09);
        border-color: #2D5A27;
    }
    .card-label {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #52605B;
        margin-bottom: 8px;
    }
    .card-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3F20;
        letter-spacing: -0.5px;
    }
    .card-value-alert {
        font-size: 2.2rem;
        font-weight: 800;
        color: #C86D51;
        letter-spacing: -0.5px;
    }
    .card-value-gold {
        font-size: 2.2rem;
        font-weight: 800;
        color: #D97724;
        letter-spacing: -0.5px;
    }
    .brand-title {
        font-size: 2.4rem;
        font-weight: 900;
        color: #1E3F20;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }
    .brand-sub {
        font-size: 0.9rem;
        font-weight: 600;
        color: #D97724;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #1E3F20;
        color: #FFFFFF;
        border-radius: 10px;
        border: none;
        padding: 6px 14px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #2D5A27;
        color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(45, 90, 39, 0.25);
    }
    .flow-box {
        background-color: #FFFFFF;
        border: 2px solid #2D5A27;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        font-weight: bold;
        color: #1E3F20;
    }
    .flow-arrow {
        text-align: center;
        font-size: 1.5rem;
        color: #D97724;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar base de datos y rutinas automáticas
database.init_db()
database.cargar_ventas_octubre_simplifica2()
database.auto_generar_gastos_fijos()

# Encabezado visual
col_logo, col_header = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=110)

with col_header:
    st.markdown('<div class="brand-title">bráˇca souvenir</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">SISTEMA FINANCIERO & TESORERÍA • SANTA ELENA | MONTEVERDE EXTREMO</div>', unsafe_allow_html=True)

# Menú lateral
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=130)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=130)

st.sidebar.markdown("### **Menú Principal**")
opcion = st.sidebar.radio(
    "",
    [
        "📊 Dashboard Consolidado", 
        "📈 Ventas vs. Proyección 2026", 
        "📅 Análisis Financiero 2025", 
        "🏦 Control de Fondos", 
        "📥 Cierres de Caja", 
        "📝 Registro de Obligaciones",
        "⚡ Monitoreo Cripto (Binance)"  # <--- 2. Añadido a las opciones del menú
    ]
)

# Enrutador de módulos
if opcion == "📊 Dashboard Consolidado":
    dash.run()
elif opcion == "📈 Ventas vs. Proyección 2026":
    proj.run()
elif opcion == "📅 Análisis Financiero 2025":
    hist.run()
elif opcion == "🏦 Control de Fondos":
    fnd.run()
elif opcion == "📥 Cierres de Caja":
    cierres.run()
elif opcion == "📝 Registro de Obligaciones":
    obs.run()
elif opcion == "⚡ Monitoreo Cripto (Binance)":
    crypto_mod.run()  # <--- 3. Enrutado a la función del nuevo módulo