"""
SatAgro — Sistema Web de Apoio a Decisao Agricola com Dados de Observacao da Terra da NASA
NASA Space Apps Challenge 2026
Desafio: Field Shift: Adapting Farms with NASA Data
Equipe: Latino Party
Regiao-Piloto: Sertaozinho (SP) | Cultura de Referencia: Cana-de-acucar
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from satagro.nasa_power import (
    fetch_climatology,
    load_verified_pilot_dataset,
    NasaPowerError,
    NasaPowerConnectionError,
    NasaPowerAPIError,
    NasaDataValidationError,
)
from satagro.indicators import calculate_climatic_summary
from satagro.alerts import evaluate_agroclimatic_signals
from satagro.rotation_engine import compute_rotation_rankings
from satagro.agronomic_data import CRITERIA_METADATA


st.set_page_config(
    page_title="SatAgro — NASA Space Apps 2026",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilizacao sobria e profissional (paleta oficial azul/laranja/fundo neutro)
st.markdown("""
<style>
    /* Cores Oficiais SatAgro:
       Azul Profundo: #0B3D91
       Azul Medio: #2E6FD8
       Laranja Destaque: #F57C00
       Fundo: #F5F7FA
       Texto: #1F2937
    */
    .main {
        background-color: #F5F7FA;
    }
    .satagro-header {
        background: #0B3D91;
        padding: 20px 26px;
        border-radius: 8px;
        color: #FFFFFF;
        margin-bottom: 18px;
    }
    .satagro-header h1 {
        color: #FFFFFF;
        margin: 0;
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .satagro-header p {
        color: #E2E8F0;
        margin: 6px 0 0 0;
        font-size: 13px;
    }
    .badge-prototype {
        display: inline-block;
        background: #F57C00;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .provenance-card {
        background: #FFFFFF;
        border-left: 4px solid #2E6FD8;
        border-top: 1px solid #E5E7EB;
        border-right: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 14px 18px;
        font-size: 13px;
        color: #374151;
        margin-bottom: 18px;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .metric-title {
        color: #6B7280;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #0B3D91;
        font-size: 22px;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-caption {
        color: #4B5563;
        font-size: 12px;
    }
    .signal-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .signal-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        color: #FFFFFF;
        display: inline-block;
        margin-bottom: 6px;
    }
    .four-layer-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .layer-tag {
        font-weight: 700;
        color: #0B3D91;
        display: block;
        margin-bottom: 4px;
        text-transform: uppercase;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# Cabecalho Principal Sobrio (sem emojis)
st.markdown("""
<div class="satagro-header">
    <span class="badge-prototype">NASA Space Apps Challenge 2026 · Field Shift · Equipe Latino Party</span>
    <h1>SatAgro — Apoio a Decisao na Reforma do Canavial com Dados da NASA</h1>
    <p>Prototipo demonstrativo combinando series climatologicas da NASA POWER com ordenacao heuristica transparente baseada nas prioridades do produtor.</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# BARRA LATERAL (SIDEBAR): Modos, Presets e Sincronizacao de Coordenadas
# ==============================================================================
ONLINE_PRESETS = {
    "Ribeirao Preto — SP (Polo Regional)": (-21.1775, -47.8103),
    "Piracicaba — SP (Centro Tradicional)": (-22.7253, -47.6492),
    "Rio Verde — GO (Expansao Centro-Oeste)": (-17.7924, -50.9192),
    "Sertaozinho — SP (Consulta Ao Vivo)": (-21.1378, -47.9897),
    "Coordenadas Personalizadas": (None, None)
}

# Inicializacao do estado de sessao para modo online
if "online_lat_input" not in st.session_state:
    st.session_state["online_lat_input"] = -21.1775
if "online_lon_input" not in st.session_state:
    st.session_state["online_lon_input"] = -47.8103
if "online_preset_select" not in st.session_state:
    st.session_state["online_preset_select"] = "Ribeirao Preto — SP (Polo Regional)"


def on_preset_change():
    """Atualiza latitude e longitude imediatamente ao mudar o preset."""
    selected = st.session_state.get("online_preset_select")
    coords = ONLINE_PRESETS.get(selected)
    if coords and coords[0] is not None:
        st.session_state["online_lat_input"] = float(coords[0])
        st.session_state["online_lon_input"] = float(coords[1])


def on_coords_change():
    """Detecta se as coordenadas digitadas coincidem com algum preset ou se sao personalizadas."""
    cur_lat = st.session_state.get("online_lat_input", -21.1775)
    cur_lon = st.session_state.get("online_lon_input", -47.8103)
    matched = "Coordenadas Personalizadas"
    for name, coords in ONLINE_PRESETS.items():
        if coords[0] is not None and abs(cur_lat - coords[0]) < 1e-4 and abs(cur_lon - coords[1]) < 1e-4:
            matched = name
            break
    st.session_state["online_preset_select"] = matched


with st.sidebar:
    st.markdown("### Modo de Operacao")

    operation_mode = st.radio(
        "Selecione o modo:",
        options=[
            "Demonstracao (Piloto Sertaozinho - SP)",
            "Consulta Online (API NASA POWER)"
        ],
        index=0,
        help="O modo Demonstracao utiliza dados verificados e coordenadas fixas de Sertaozinho (100% offline). O modo Consulta Online permite buscar coordenadas ao vivo."
    )

    is_demo_mode = (operation_mode == "Demonstracao (Piloto Sertaozinho - SP)")

    st.markdown("---")
    st.markdown("### Localizacao da Propriedade")

    if is_demo_mode:
        active_lat = -21.1378
        active_lon = -47.9897
        location_label = "Sertaozinho — SP (Piloto Cana-de-Acucar)"

        st.text_input("Localidade Fixa:", value="Sertaozinho — SP", disabled=True, key="demo_loc_name")
        col_dlat, col_dlon = st.columns(2)
        with col_dlat:
            st.number_input("Latitude Fixa:", value=active_lat, format="%.4f", disabled=True, key="demo_lat_fix")
        with col_dlon:
            st.number_input("Longitude Fixa:", value=active_lon, format="%.4f", disabled=True, key="demo_lon_fix")

        st.info("Modo Demonstracao: Coordenadas e dados estritamente fixados no dataset verificado do piloto (garantia de execucao offline).")
        btn_online_query = False
        use_cache_online = True

    else:
        st.selectbox(
            "Selecionar local:",
            options=list(ONLINE_PRESETS.keys()),
            key="online_preset_select",
            on_change=on_preset_change
        )

        col_olat, col_olon = st.columns(2)
        with col_olat:
            st.number_input(
                "Latitude:",
                format="%.4f",
                step=0.01,
                disabled=False,
                key="online_lat_input",
                on_change=on_coords_change
            )
        with col_olon:
            st.number_input(
                "Longitude:",
                format="%.4f",
                step=0.01,
                disabled=False,
                key="online_lon_input",
                on_change=on_coords_change
            )

        active_lat = float(st.session_state.online_lat_input)
        active_lon = float(st.session_state.online_lon_input)
        location_label = f"Coordenadas ({active_lat:.4f}, {active_lon:.4f})"

        use_cache_online = st.checkbox(
            "Permitir leitura de cache local em recarregamentos",
            value=True,
            help="Se desmarcado ou ao clicar no botao de consulta, forca requisicao a API da NASA POWER.",
            key="online_use_cache_box"
        )

        # Botao explícito para forçar consulta real à API da NASA
        btn_online_query = st.button("Consultar dados da NASA", type="primary", key="btn_online_consult")

    st.markdown("---")
    st.markdown("### Prioridades do Produtor")
    st.caption("Ajuste o peso relativo de cada criterio (1 = Menor importancia, 5 = Maxima prioridade). O motor de decisao normaliza os pesos e recalcula as notas heuristicas.")

    weight_soil = st.slider("Protecao do Solo (Cobertura)", min_value=1, max_value=5, value=5, key="w_soil")
    weight_n = st.slider("Fixacao de N / Materia Organica", min_value=1, max_value=5, value=4, key="w_n")
    weight_pests = st.slider("Quebra de Pragas e Nematoides", min_value=1, max_value=5, value=4, key="w_pests")
    weight_water = st.slider("Tolerancia Teorica a Deficit Hidrico", min_value=1, max_value=5, value=3, key="w_water")
    weight_income = st.slider("Renda Direta na Entressafra", min_value=1, max_value=5, value=3, key="w_income")
    weight_ops = st.slider("Simplicidade Operacional", min_value=1, max_value=5, value=2, key="w_ops")

    producer_priorities = {
        "protecao_solo": weight_soil,
        "fixacao_nitrogenio": weight_n,
        "quebra_pragas": weight_pests,
        "resiliencia_hidrica": weight_water,
        "renda_adicional": weight_income,
        "simplicidade_operacional": weight_ops,
    }

    st.markdown("---")
    st.caption("Privacidade: O SatAgro nao armazena dados de propriedades rurais em servidores remotos sem consentimento.")


# ==============================================================================
# CARREGAMENTO DOS DADOS NASA COM SEPARACAO ESTRITA DE MODOS
# ==============================================================================
nasa_data = None
fetch_error = None

if is_demo_mode:
    try:
        nasa_data = load_verified_pilot_dataset()
    except Exception as e:
        fetch_error = f"Erro ao carregar dataset verificado do piloto: {e}"
else:
    # Se o usuario clicou explicitamente no botao, forcar requisicao ignorando o cache
    force_live_request = bool(btn_online_query or not use_cache_online)
    spinner_text = "Consultando API da NASA POWER ao vivo..." if force_live_request else "Carregando dados climatologicos..."

    with st.spinner(f"{spinner_text} para ({active_lat:.4f}, {active_lon:.4f})"):
        try:
            nasa_data = fetch_climatology(
                lat=active_lat,
                lon=active_lon,
                use_cache=not force_live_request,
                force_pilot_demo=False
            )
        except NasaDataValidationError as dve:
            fetch_error = f"Dados da NASA Invalidos ou Incompletos: {dve}"
        except NasaPowerConnectionError as nce:
            fetch_error = f"Falha de Conexao com a NASA: {nce}"
        except NasaPowerAPIError as nae:
            fetch_error = f"Erro na API da NASA: {nae}"
        except Exception as e:
            fetch_error = f"Erro inesperado ao consultar a NASA POWER: {e}"

if fetch_error:
    st.error(f"Falha na Consulta: {fetch_error}")
    st.markdown("""
    > **Aviso de Integridade:** A consulta online falhou e os dados nao puderam ser recuperados para as coordenadas solicitadas.  
    > O SatAgro **nunca substitui silenciosamente** uma consulta online com erro pelos dados do piloto.  
    > Para executar sem conexao externa, altere o modo para **Demonstracao (Piloto Sertaozinho - SP)** no painel lateral.
    """)
    st.stop()


# Calculo dos Indicadores e Avaliacao
metadata = nasa_data.get("metadata", {})
indicators = calculate_climatic_summary(nasa_data["parameters"], metadata=metadata)
signals = evaluate_agroclimatic_signals(indicators, nasa_data["parameters"], metadata=metadata)
rankings = compute_rotation_rankings(producer_priorities, indicators=indicators)


# ==============================================================================
# ABAS PRINCIPAIS (sem emojis)
# ==============================================================================
tab_map_data, tab_signals, tab_comparison, tab_methods = st.tabs([
    "Localizacao e Climatologia NASA",
    "Sinais Climatologicos Exploratorios",
    "Ordenacao Heuristica das Estrategias",
    "Metodologia, Fontes e Escopo"
])


# ------------------------------------------------------------------------------
# ABA 1: LOCALIZACAO E CLIMATOLOGIA NASA
# ------------------------------------------------------------------------------
with tab_map_data:
    st.markdown(f"#### Localizacao Ativa: {location_label}")

    if is_demo_mode:
        provenance_status = "Modo Demonstracao: Dataset Autentico Verificado do Piloto (Sertaozinho - SP, sem chamadas externas)"
    elif nasa_data.get("is_cached"):
        provenance_status = f"Modo Online: Dados recuperados do cache local temporario para ({active_lat:.4f}, {active_lon:.4f})"
    else:
        provenance_status = f"Modo Online: Consulta realizada ao vivo a API NASA POWER para ({active_lat:.4f}, {active_lon:.4f})"

    st.markdown(f"""
    <div class="provenance-card">
        <strong>Fonte Oficial:</strong> {metadata.get('api_name', 'NASA POWER Climatology API')} (Versao: {metadata.get('api_version', 'v2.10.1')})<br>
        <strong>Serie Climatologica:</strong> {metadata.get('climatology_range', '2001–2025')}<br>
        <strong>Resolucao Meteorologica (T2M, PRECTOTCORR, RH2M):</strong> {metadata.get('spatial_resolution_meteorology')}<br>
        <strong>Status de Proveniencia:</strong> {provenance_status}<br>
        <strong>Data/Hora da Coleta Registrada:</strong> {nasa_data.get('collected_at')}<br>
        <strong>Coordenadas Ativas:</strong> Latitude {active_lat:.4f}, Longitude {active_lon:.4f}<br>
        <span style="color: #64748B; font-size: 12px;">Nota: <em>{metadata.get('spatial_disclaimer')}</em></span>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_metrics = st.columns([1.1, 0.9])

    with col_map:
        st.markdown("**Mapa da Localizacao Ativa:**")
        
        m = folium.Map(location=[active_lat, active_lon], zoom_start=11, tiles="OpenStreetMap")
        folium.CircleMarker(
            location=[active_lat, active_lon],
            radius=8,
            color="#0B3D91",
            fill=True,
            fill_color="#F57C00",
            fill_opacity=0.9,
            popup=f"{location_label} ({active_lat:.4f}, {active_lon:.4f})"
        ).add_to(m)

        try:
            map_data = st_folium(m, height=340, width=None, key=f"satagro_map_{active_lat}_{active_lon}")
            if map_data and map_data.get("last_clicked"):
                click_lat = map_data["last_clicked"]["lat"]
                click_lng = map_data["last_clicked"]["lng"]
                if is_demo_mode:
                    st.info(f"Ponto clicado: Lat {click_lat:.4f}, Lon {click_lng:.4f}. No Modo Demonstracao, as coordenadas sao fixas em Sertaozinho. Mude para o 'Modo Consulta Online' para pesquisar este ponto.")
                else:
                    st.info(f"Ponto clicado: Lat {click_lat:.4f}, Lon {click_lng:.4f}. Para consultar este ponto, insira as coordenadas no painel lateral e clique em 'Consultar dados da NASA'.")
        except Exception:
            st.info("Visualizacao cartografica em modo simplificado. Dados da NASA carregados com sucesso.")

    with col_metrics:
        st.markdown("**Indicadores Climatologicos Verificados:**")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_precipitation']['name']}</div>
                <div class="metric-value">{indicators['annual_precipitation']['value']} {indicators['annual_precipitation']['unit']}</div>
                <div class="metric-caption">Serie: {metadata.get('climatology_range', '2001–2025')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_mean_temp']['name']}</div>
                <div class="metric-value">{indicators['annual_mean_temp']['value']} {indicators['annual_mean_temp']['unit']}</div>
                <div class="metric-caption">Media anual a 2m (T2M)</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['reform_window_rain']['name']}</div>
                <div class="metric-value">{indicators['reform_window_rain']['value']} mm</div>
                <div class="metric-caption">{indicators['reform_window_rain']['interpretation']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['seasonal_dry_ratio']['name']}</div>
                <div class="metric-value">{indicators['seasonal_dry_ratio']['value']} %</div>
                <div class="metric-caption">Chuva no periodo seco (Abr–Set)</div>
            </div>
            """, unsafe_allow_html=True)

    # Graficos Mensais
    st.markdown("---")
    st.markdown(f"#### Distribuicao Mensal Historica — {location_label} (NASA POWER MERRA-2)")
    
    raw = indicators["raw_monthly_data"]
    df_climate = pd.DataFrame({
        "Mes": raw["months_pt"],
        "Chuva Media (mm/mes)": raw["rainfall_mm"],
        "Temp. Media (C)": raw["tmean_c"],
        "Temp. Maxima (C)": raw["tmax_c"],
        "Temp. Minima (C)": raw["tmin_c"],
    })

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.bar_chart(df_climate, x="Mes", y="Chuva Media (mm/mes)", color="#2E6FD8")
        st.caption("Precipitacao media mensal (mm/mes). Notar pico nos meses de verao (Dez–Fev), coincidente com a janela de reforma.")
    with col_ch2:
        st.line_chart(df_climate, x="Mes", y=["Temp. Media (C)", "Temp. Maxima (C)", "Temp. Minima (C)"], color=["#0B3D91", "#F57C00", "#93C5FD"])
        st.caption("Perfil termico: maximas de verao acima de 30 C e minimas de inverno (Jun/Jul) na grade regional.")


# ------------------------------------------------------------------------------
# ABA 2: SINAIS CLIMATOLOGICOS EXPLORATORIOS
# ------------------------------------------------------------------------------
with tab_signals:
    st.markdown("#### Sinais Climatologicos Exploratorios Regionais")
    st.markdown("""
    > **Aviso Cientifico:** As informacoes abaixo representam **sinais climatologicos historicos regionais** derivados da serie da NASA POWER.
    > Eles **NAO constituem diagnosticos preditivos de talhao nem medicoes de risco real**, pois fatores como declividade da encosta,
    > textura pedologica do solo, presenca de pragas vivas e microclimas locais exigem monitoramento presencial in loco.
    """)

    for s in signals:
        st.markdown(f"""
        <div class="signal-card" style="border-left: 4px solid {s['badge_color']};">
            <span class="signal-badge" style="background-color: {s['badge_color']};">{s['category']}</span>
            <h4 style="margin: 4px 0 8px 0; color: #0B3D91;">{s['title']}</h4>
            <p style="margin-bottom: 6px; font-size: 13px; color: #1F2937;"><strong>Observacao NASA:</strong> {s['observation']}</p>
            <p style="margin-bottom: 6px; font-size: 13px; color: #B91C1C;"><strong>O que este sinal NAO significa:</strong> {s['what_it_is_not']}</p>
            <p style="margin-bottom: 4px; font-size: 13px; color: #4B5563;"><strong>Referencia Tecnica (IAC/Embrapa):</strong> {s['literature_reference']}</p>
            <span style="font-size: 12px; color: #64748B;"><em>Limitacao Tecnica:</em> {s['limitation']}</span>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ABA 3: ORDENACAO HEURISTICA DAS ESTRATEGIAS
# ------------------------------------------------------------------------------
with tab_comparison:
    st.markdown("#### Ordenacao Heuristica das Estrategias de Reforma do Canavial")
    st.markdown("""
    > **Aviso de Metodologia e Honestidade Intelectual:**  
    > Esta ferramenta utiliza o metodo de **Ponderacao Multicriterio (MCDA)** para ordenar quatro estrategias de referencia.  
    > **As pontuacoes sao avaliacoes heuristicas ilustrativas**, calculadas exclusivamente a partir da combinacao dos **pesos definidos pelo produtor**
    > com **notas conceituais de referencia da literatura agronomica** (IAC, Embrapa, FAO).  
    > **Nao se trata de um modelo agronomico calibrado para o local nem de um resultado gerado por satelites da NASA.**  
    > Alterar a localizacao geografica atualiza o diagnostico climatico da NASA POWER, mas nao recalcula a aptidao das culturas sem dados locais de solo e manejo.
    """)

    table_rows = []
    for r in rankings:
        table_rows.append({
            "Posicao": f"{r['rank']}o Lugar",
            "Estrategia": r["name"],
            "Tipo": r["crop_type"],
            "Ciclo Tipico": r["cycle_days"],
            "Nota Heuristica (0 a 100)": f"{r['final_score']} / 100",
            "Grau de Confianca": r["confidence"]
        })
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)

    chart_df = pd.DataFrame({
        "Estrategia": [r["name"] for r in rankings],
        "Pontuacao Heuristica (0–100)": [r["final_score"] for r in rankings]
    })
    st.bar_chart(chart_df, x="Estrategia", y="Pontuacao Heuristica (0–100)", color="#2E6FD8")

    st.markdown("---")
    st.markdown("#### Detalhamento Matematico da Contribuicao por Criterio")
    st.caption(r"Formula aplicada: $S_j = \sum_{i} (w_i \cdot s_{ij}) \times 100$, onde $w_i$ e o peso relativo normalizado pelo usuario e $s_{ij}$ e a nota de referencia agronomica.")

    weights_summary = rankings[0]["normalized_weights"]
    weights_display = pd.DataFrame({
        "Criterio": [CRITERIA_METADATA[k]["name"] for k in weights_summary.keys()],
        "Prioridade Produtor (1–5)": [int(producer_priorities[k]) for k in weights_summary.keys()],
        "Peso Normalizado ($w_i$)": [f"{weights_summary[k]*100:.1f}%" for k in weights_summary.keys()],
    })
    st.dataframe(weights_display, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Fichas Agronomicas Padronizadas (4 Camadas Explicitas)")
    st.caption("Abra cada estrategia abaixo para verificar separadamente dados NASA, indicadores derivados, literatura agronomica e a avaliacao heuristica.")

    for r in rankings:
        with st.expander(f"{r['rank']}o Lugar — {r['name']} (Nota Heuristica: {r['final_score']} / 100)"):
            c_left, c_right = st.columns([1.3, 0.7])

            with c_left:
                st.markdown(f"""
                <div class="four-layer-box">
                    <span class="layer-tag">1. Dados Observacionais / Estimados pela NASA</span>
                    {r['nasa_observational_data']}
                </div>
                <div class="four-layer-box">
                    <span class="layer-tag">2. Indicadores Derivados Calculados pelo SatAgro</span>
                    {r['derived_indicators']}
                </div>
                <div class="four-layer-box">
                    <span class="layer-tag">3. Literatura Tecnica de Referencia (IAC / Embrapa / CTC)</span>
                    {r['technical_literature']}
                </div>
                <div class="four-layer-box">
                    <span class="layer-tag">4. Avaliacao Heuristica Ilustrativa (MCDA)</span>
                    {r['heuristic_scoring_explanation']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Lacunas de Informacao:** {r['unknowns']}")
                st.markdown(f"**Grau de Confianca:** *{r['confidence']}*")
                st.warning(f"**Validacao Agronomica Presencial Necessaria:** {r['specialist_review']}")

            with c_right:
                st.markdown("**Composicao da Nota:**")
                breakdown = r["criteria_contributions"]
                ref_scores = r["reference_scores"]
                c_data = pd.DataFrame({
                    "Criterio": [CRITERIA_METADATA[k]["name"] for k in breakdown.keys()],
                    "Nota Ref. ($s_{ij}$)": [ref_scores[k] for k in breakdown.keys()],
                    "Contribuicao": [breakdown[k] for k in breakdown.keys()],
                })
                st.dataframe(c_data, hide_index=True, use_container_width=True)


# ------------------------------------------------------------------------------
# ABA 4: METODOLOGIA, FONTES E ESCOPO
# ------------------------------------------------------------------------------
with tab_methods:
    st.markdown("#### Metodologia Cientifica e Delimitacao de Escopo")

    col_mvp, col_future = st.columns(2)
    with col_mvp:
        st.markdown("""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 16px;">
            <h4 style="color: #0B3D91; margin-top: 0;">Funcionalidades Efetivamente Implementadas no MVP</h4>
            <ul style="font-size: 13px; color: #1E3A8A; line-height: 1.6;">
                <li><strong>Modo Demonstracao vs Modo Consulta Online:</strong> Separacao estrita com fixacao de coordenadas para o piloto e requisicao real para novos pontos.</li>
                <li><strong>Integracao com a API NASA POWER v2.10.1:</strong> Coleta e validacao de precipitacao (PRECTOTCORR), temperatura media, maxima e minima (T2M, T2M_MAX, T2M_MIN) e umidade relativa (RH2M).</li>
                <li><strong>Validacao Estrita de Dados:</strong> Rejeicao de valores sentinela (-999.0), nao-finitos ou meses ausentes.</li>
                <li><strong>Proveniencia Dinamica:</strong> Exibicao do intervalo temporal real (2001–2025) e distincao entre grade MERRA-2 e escala de talhao.</li>
                <li><strong>Conjunto de Demonstracao Verificado:</strong> Dados autenticos pre-validados para Sertaozinho (SP) empacotados no repositorio.</li>
                <li><strong>Indicadores Climatologicos Regionais:</strong> Acumulado anual, indice de estiagem de inverno e chuva na reforma.</li>
                <li><strong>Sinais Climatologicos Exploratorios:</strong> Contexto historico regional com advertencia explicita sobre suas limitacoes.</li>
                <li><strong>Motor de Decisao Heuristico Transparente:</strong> Ponderacao multicriterio (MCDA) baseada exclusivamente nos pesos do produtor e referencias agronomicas.</li>
                <li><strong>Fichas em 4 Camadas:</strong> Separacao estrita entre dados NASA, indicadores SatAgro, literatura agronomica e avaliacoes heuristicas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_future:
        st.markdown("""
        <div style="background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 6px; padding: 16px;">
            <h4 style="color: #C2410C; margin-top: 0;">Funcionalidades Planejadas (Fase 2 / Pos-Hackathon)</h4>
            <ul style="font-size: 13px; color: #9A3412; line-height: 1.6;">
                <li><strong>Resolucao Espacial Fina:</strong> Integracao de Sentinel-2 e Landsat 8/9 (10–30 m) para medicao de vigor vegetal intra-talhao.</li>
                <li><strong>Topografia SRTM (~30 m):</strong> Extracao de Modelo Digital de Elevacao para calculo de declividade e escoamento.</li>
                <li><strong>Umidade do Solo SMAP:</strong> Camadas de umidade superficial e radicular em alta resolucao.</li>
                <li><strong>Focos de Calor FIRMS:</strong> Deteccao de queimadas na vizinhanca imediata da lavoura.</li>
                <li><strong>Calibracao com Dados Locais:</strong> Inclusao de dados de solo e talhoes informados pelo agricultor.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Referencias Tecnicas e Cientificas")
    st.markdown("""
    1. **AMBROSANO, E. J. et al.** *Adubacao verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronomico (IAC), Boletim Tecnico.
    2. **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Praticas conservacionistas e fixacao biologica de nitrogenio em sistemas de rotacao no Centro-Sul.*
    3. **DOORENBOS, J.; KASSAM, A. H.** *Yield response to water.* Rome: FAO, 1979. (FAO Irrigation and Drainage Paper, 33).
    4. **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.10.1).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
    """)

    st.info("""
    **Isencao de Responsabilidade (Disclaimer):**  
    O SatAgro e uma ferramenta educacional e conceitual desenvolvida para o NASA Space Apps Challenge 2026. 
    As estimativas da NASA possuem resolucao regional (~50 km) e a ferramenta heuristica de rotacao reflete conceitos bibliograficos gerais. 
    Nenhum resultado substitui a analise de solo, a amostragem fitossanitaria presencial ou a prescricao de um Engenheiro Agronomo.
    """)
