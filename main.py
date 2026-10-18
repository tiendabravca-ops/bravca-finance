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
    initial_sidebar_state="expanded"
)

# Estilos CSS - Estética Clean SaaS / Modern Dashboard & Iconos Profesionales FontAwesome
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
    /* 1. Fondo Principal Limpio */
    .stApp {
        background-color: #F4F6F9 !important;
        color: #102A43 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 2. Regla General de Texto */
    p, span, label, .stMarkdown, div {
        color: #102A43;
    }

    /* 3. Barra Lateral en Azul Marino Profundo */
    [data-testid="stSidebar"] {
        background-color: #102A43 !important;
        border-right: none !important;
        padding-top: 15px;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    
    /* Selector Radio en Sidebar convertido a estilo SaaS limpio */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: rgba(255, 255, 255, 0.03);
        border: none;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: rgba(245, 166, 35, 0.2);
        color: #F5A623 !important;
    }

    /* Estilizado de la tarjeta del logo en la barra lateral */
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* 4. Tarjetas KPIs tipo Clean Card con sombra flotante */
    .brabca-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
        margin-bottom: 16px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .brabca-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.06);
    }
    .card-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #627D98 !important;
        margin-bottom: 8px;
    }
    .card-value {
        font-size: 2rem;
        font-weight: 800;
        color: #102A43 !important;
        letter-spacing: -0.5px;
    }
    .card-value-alert {
        font-size: 2rem;
        font-weight: 800;
        color: #D9534F !important;
        letter-spacing: -0.5px;
    }
    .card-value-gold {
        font-size: 2rem;
        font-weight: 800;
        color: #F5A623 !important;
        letter-spacing: -0.5px;
    }

    /* 5. Encabezado Principal */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #102A43 !important;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }
    .brand-sub {
        font-size: 0.8rem;
        font-weight: 700;
        color: #F5A623 !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* 6. Botones con Estilo SaaS Moderno */
    .stButton>button {
        background: #102A43 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 10px 18px !important;
        font-weight: 700 !important;
        width: 100%;
        box-shadow: 0 4px 12px rgba(16, 42, 67, 0.15);
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: #F5A623 !important;
        color: #102A43 !important;
        box-shadow: 0 6px 16px rgba(245, 166, 35, 0.3) !important;
    }

    /* 7. Tablas y Dataframes */
    [data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    }

    /* 8. Ajustes Responsivos */
    @media (max-width: 768px) {
        .brand-title {
            font-size: 1.6rem;
        }
        .brand-sub {
            font-size: 0.7rem;
            letter-spacing: 1px;
        }
        .card-value, .card-value-alert, .card-value-gold {
            font-size: 1.5rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar base de datos y rutinas automáticas
database.init_db()
database.cargar_ventas_octubre_simplifica2()
database.auto_generar_gastos_fijos()

# --- LOGO EN LA BARRA LATERAL ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("### **Menú Principal**")

# Opciones de menú con formato y vectores profesionales FontAwesome
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
    label_visibility="collapsed",
    format_func=lambda x: {
        "📊 Dashboard Consolidado": "📊  Dashboard Consolidado",
        "📈 Ventas vs. Proyección 2026": "📈  Ventas vs. Proyección 2026",
        "📅 Análisis Financiero 2025": "📅  Análisis Financiero 2025",
        "🏦 Control de Fondos": "🏦  Control de Fondos",
        "📥 Cierres de Caja": "📥  Cierres de Caja",
        "📝 Registro de Obligaciones": "📝  Registro de Obligaciones",
        "⚡ Monitoreo Cripto (Binance)": "⚡  Monitoreo Cripto (Binance)"
    }.get(x, x)
)

# Encabezado visual principal
st.markdown('<div class="brand-title">bráˇca souvenir</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">SISTEMA FINANCIERO & TESORERÍA • SANTA ELENA | MONTEVERDE EXTREMO</div>', unsafe_allow_html=True)

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
