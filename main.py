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
    initial_sidebar_state="collapsed"  # <--- Colapsado por defecto para vista móvil (sándwich ☰)
)

# Estilos CSS - Paleta Oficial brá'ca Souvenir (Optimizado para legibilidad móvil)
st.markdown("""
    <style>
    /* Estilo Base y Texto */
    .stApp {
        background-color: #F7F5F0;
        color: #0D1F0D !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Asegurar alto contraste en todos los elementos de texto de Streamlit */
    p, span, label, .stMarkdown, div {
        color: #0D1F0D !important;
    }

    /* Barra Lateral / Menú Sándwich */
    [data-testid="stSidebar"] {
        background-color: #EFECE6 !important;
        border-right: 1px solid #DCD7CE;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #1E3F20 !important;
        font-weight: 600;
    }

    /* Tarjetas y Métricas */
    .brabca-card {
        background-color: #FFFFFF;
        border: 1px solid #D1CDC4;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(30, 63, 32, 0.08);
        margin-bottom: 12px;
    }
    .card-label {
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #33443E !important;
        margin-bottom: 6px;
    }
    .card-value {
        font-size: 2rem;
        font-weight: 900;
        color: #1E3F20 !important;
        letter-spacing: -0.5px;
    }
    .card-value-alert {
        font-size: 2rem;
        font-weight: 900;
        color: #B33919 !important;
        letter-spacing: -0.5px;
    }
    .card-value-gold {
        font-size: 2rem;
        font-weight: 900;
        color: #B85B00 !important;
        letter-spacing: -0.5px;
    }

    /* Encabezado Principal */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #1E3F20 !important;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }
    .brand-sub {
        font-size: 0.85rem;
        font-weight: 700;
        color: #B85B00 !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* Botones Legibles */
    .stButton>button {
        background-color: #1E3F20 !important;
        color: #FFFFFF !important;
        border-radius: 10px;
        border: none;
        padding: 8px 16px;
        font-weight: 700;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2D5A27 !important;
        color: #FFFFFF !important;
    }

    /* Ajustes para pantallas pequeñas */
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
