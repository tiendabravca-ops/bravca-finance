import streamlit as st
import pandas as pd
import requests
import datetime

def run():
    st.markdown("##### 🤖 CENTRO DE COMANDO MULTIACTIVO: AGENTE FINANCIERO")
    st.caption("Análisis simultáneo del portafolio (BTC, ETH, SOL y USDT) con automatización inteligente en Telegram.")

    # Credenciales de Telegram configuradas
    TELEGRAM_TOKEN = "8812324406:AAGzg9hMnRDGAKYeHbJkNzE10efZgSZU1ws"
    CHAT_ID = "1667584148"

    def enviar_alerta_telegram(mensaje):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                st.success("¡Reporte multiactivo enviado con éxito a tu Telegram!")
            else:
                st.error("Error al enviar la alerta a Telegram. Verifica que hayas iniciado el bot (/start).")
        except Exception as e:
            st.error(f"Excepción de conexión con Telegram: {e}")

    # Temporalidad de análisis general para el portafolio y control de caja
    col_t1, col_t2 = st.columns([2, 2])
    with col_t1:
        intervalo = st.selectbox("Temporalidad de Análisis Global", ["1h", "4h", "1d"], index=2)
    with col_t2:
        fondo_usdt = st.number_input("Reserva Disponible en USDT (Caja)", min_value=0.0, value=1000.0, step=100.0)

    # Función para consultar datos de Binance con caché
    @st.cache_data(ttl=60)
    def obtener_datos_agente(symbol, interval):
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                return df
        except Exception:
            pass
        return pd.DataFrame()

    def calcular_rsi(data, window=14):
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    # Lista de los 3 activos operativos de mercado + 1 de liquidez
    simbolos = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    resumen_portafolio = []
    recomendaciones_activas = []
    hay_alerta_critica = False

    for simbolo in simbolos:
        df = obtener_datos_agente(simbolo, intervalo)
        if not df.empty:
            precio_actual = df['close'].iloc[-1]
            precio_anterior = df['close'].iloc[-2]
            var = ((precio_actual - precio_anterior) / precio_anterior) * 100
            df['rsi'] = calcular_rsi(df['close'])
            rsi_val = df['rsi'].iloc[-1]

            # Evaluar estado de cada activo
            if rsi_val <= 30:
                estado = "COMPRA (Sobreventa)"
                recomendaciones_activas.append(f"🟢 *{simbolo}*: Oportunidad fuerte de acumulación (RSI: {rsi_val:.1f}).")
                hay_alerta_critica = True
            elif rsi_val >= 70:
                estado = "VENTA (Sobrecompra)"
                recomendaciones_activas.append(f"🔴 *{simbolo}*: Zona alta de toma de utilidades (RSI: {rsi_val:.1f}).")
                hay_alerta_critica = True
            else:
                estado = "NEUTRAL (Esperar)"

            resumen_portafolio.append({
                "Activo": simbolo,
                "Precio (USDT)": f"$ {precio_actual:,.2f}",
                "Variación": f"{var:+.2f}%",
                "RSI (14)": f"{rsi_val:.1f}",
                "Diagnóstico": estado
            })

    # Mostrar Tabla Consolidada del Portafolio en Pantalla
    st.markdown("##### 📊 Panel Consolidado de los Activos Clave")
    if resumen_portafolio:
        df_resumen = pd.DataFrame(resumen_portafolio)
        st.dataframe(df_resumen, use_container_width=True)

    # --- SECCIÓN DE ÓRDENES Y SUGERENCIAS DEL AGENTE ---
    st.markdown("##### 🧠 Órdenes y Consejos Estratégicos del Agente")

    if recomendaciones_activas:
        for rec in recomendaciones_activas:
            st.markdown(f"- {rec}")
    else:
        st.info("ℹ️ Todos los activos se encuentran en rangos estables (Neutros). El agente recomienda proteger la liquidez en USDT y esperar a que algún activo cruce los umbrales extremos.")

    # Estado de la Caja (USDT)
    st.markdown(f"""
        <div style="background-color: rgba(59, 130, 246, 0.08); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 8px; margin-top: 15px; margin-bottom: 15px;">
            <h5 style="color: #1e3f20; margin-top: 0;">💵 Control de Liquidez Estable (USDT)</h5>
            <p style="color: #1c2826; font-size: 0.95rem; margin-bottom: 0;">
                Fondo disponible para ejecución: <strong>$ {fondo_usdt:,.2f} USDT</strong>.<br>
                <em>Regla del Agente:</em> No comprometer más del 25% de esta reserva por cada orden de compra sugerida en BTC, ETH o SOL.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- AUTOMATIZACIÓN INTELIGENTE: DISPARO ÚNICO A TELEGRAM EN ZONAS CRÍTICAS ---
    if resumen_portafolio and hay_alerta_critica:
        sesion_alerta_key = f"multialerta_enviada_{datetime.date.today()}_{intervalo}"
        if sesion_alerta_key not in st.session_state:
            lineas_texto = ["🚨 *AUTOMATIZACIÓN BRISCA: OPORTUNIDAD DETECTADA* 🚨\n"]
            for item in resumen_portafolio:
                act = item['Activo']
                pre = item['Precio (USDT)']
                rsi = item['RSI (14)']
                est = item['Diagnóstico']
                lineas_texto.append(f"• *{act}* | Precio: `{pre}` | RSI: `{rsi}` | Estado: _{est}_")
            
            lineas_texto.append(f"\n*Reserva en USDT:* `$ {fondo_usdt:,.2f}`\n\n*Sugerencias del Agente:*")
            lineas_texto.extend(recomendaciones_activas)
            
            texto_auto = "\n".join(lineas_texto)
            enviar_alerta_telegram(texto_auto)
            st.session_state[sesion_alerta_key] = True

    # --- BOTÓN MANUAL DE CONTROL GLOBAL ---
    if st.button("📲 Enviar Reporte Consolidado del Portafolio a Telegram"):
        lineas_manual = ["📲 *REPORTE GLOBAL MANUAL BRISCA* 📲\n"]
        for item in resumen_portafolio:
            act = item['Activo']
            pre = item['Precio (USDT)']
            rsi = item['RSI (14)']
            est = item['Diagnóstico']
            lineas_manual.append(f"• *{act}* | Precio: `{pre}` | RSI: `{rsi}` | Estado: _{est}_")
        
        lineas_manual.append(f"\n*Reserva en USDT:* `$ {fondo_usdt:,.2f}`\n")
        if recomendaciones_activas:
            lineas_manual.append("*Sugerencias del Agente:*")
            lineas_manual.extend(recomendaciones_activas)
        else:
            lineas_manual.append("*Sugerencia:* Mercado en zona neutral. Mantener disciplina y liquidez.")
            
        texto_manual = "\n".join(lineas_manual)
        enviar_alerta_telegram(texto_manual)
