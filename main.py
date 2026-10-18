import streamlit as st
import os
import database
import modules.dashboard as dash
import modules.proyecciones as proj
import modules.historico as hist
import modules.fondos as fnd
import modules.cierres as cierres
import modules.obligaciones as obs
import modules.crypto_alertas as crypto_mod

st.set_page_config(
    page_title="brá'ca Financial Core", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Colapsado por defecto para vista móvil (sándwich ☰)
)

# Estilos CSS - Paleta Estilo Binance / Nexo Pro Dark Mode
st.markdown("""
    <style>
    /* 1. Fondo Principal Pro Dark */
    .stApp {
        background-color: #0B0E11 !important;
        color: #EAECSF !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    
    /* 2. Regla General de Texto Oscuro / Claro */
    p, span, label, .stMarkdown, div {
        color: #EAECSF;
    }

    /* 3. Menú Lateral / Sidebar estilo Crypto Terminal */
    [data-testid="stSidebar"] {
        background-color: #12161C !important;
        border-right: 1px solid #2B313A !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #848E9C !important;
        font-weight: 600;
    }
    
    /* Estilo del Selector Radio en Sidebar */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #181A20;
        border: 1px solid #2B313A;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
        transition: all 0.2s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        border-color: #F0B90B;
        color: #F0B90B !important;
    }

    /* 4. Tarjetas KPIs Binance / Nexo Style */
    .brabca-card {
        background-color: #181A20 !important;
        border: 1px solid #2B313A !important;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .brabca-card:hover {
        border-color: #F0B90B !important;
        transform: translateY(-2px);
    }
    .card-label {
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #848E9C !important;
        margin-bottom: 6px;
    }
    .card-value {
        font-size: 2rem;
        font-weight: 900;
        color: #0ECB81 !important; /* Verde Ganancia Binance */
        letter-spacing: -0.5px;
    }
    .card-value-alert {
        font-size: 2rem;
        font-weight: 900;
        color: #F6465D !important; /* Rojo Bajista Binance */
        letter-spacing: -0.5px;
    }
    .card-value-gold {
        font-size: 2rem;
        font-weight: 900;
        color: #F0B90B !important; /* Dorado Binance */
        letter-spacing: -0.5px;
    }

    /* 5. Encabezado Principal */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #FFFFFF !important;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }
    .brand-sub {
        font-size: 0.85rem;
        font-weight: 700;
        color: #F0B90B !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* 6. Botones Pro Crypto */
    .stButton>button {
        background: linear-gradient(135deg, #F0B90B 0%, #D4A007 100%) !important;
        color: #0B0E11 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 18px !important;
        font-weight: 800 !important;
        width: 100%;
        box-shadow: 0 2px 8px rgba(240, 185, 11, 0.2);
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #FFC81A 0%, #F0B90B 100%) !important;
        color: #000000 !important;
        box-shadow: 0 0 12px rgba(240, 185, 11, 0.5) !important;
    }

    /* 7. Tablas y Dataframes */
    [data-testid="stDataFrame"] {
        background-color: #181A20 !important;
        border: 1px solid #2B313A !important;
        border-radius: 10px;
    }

    /* 8. Ajustes para pantallas pequeñas (móviles) */
    @media (max-width: 768px) {
        .brand-title {
            font-size: 1.7rem;
        }
        .brand-sub {
            font-size: 0.75rem;
            letter-spacing: 1px;
        }
        .card-value, .card-value-alert, .card-value-gold {
            font-size: 1.6rem;
        }
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
        st.image("logo.png", width=90)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=90)

with col_header:
    st.markdown('<div class="brand-title">bráˇca souvenir</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">SISTEMA FINANCIERO & TESORERÍA • SANTA ELENA | MONTEVERDE EXTREMO</div>', unsafe_allow_html=True)

# Menú lateral
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=120)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", width=120)

st.sidebar.markdown("### **Menú Principal**")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "📊 Dashboard Consolidado", 
        "📈 Ventas vs. Proyección 2026", 
        "📅 Análisis Financiero 2025", 
        "🏦 Control de Fondos", 
        "📥 Cierres de Caja", 
        "📝 Registro de Obligaciones",
        "⚡ Monitoreo Cripto (Binance)"
    ],
    label_visibility="collapsed"
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
    crypto_mod.run()
