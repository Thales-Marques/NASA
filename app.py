"""
SatAgro — Sistema Web de Apoio à Decisão Agrícola com Dados de Observação da Terra da NASA
NASA Space Apps Challenge 2026
Desafio: Field Shift: Adapting Farms with NASA Data
Equipe: Latino Party
Região-Piloto: Sertãozinho (SP) | Cultura de Referência: Cana-de-açúcar
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
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização sóbria e profissional (paleta oficial azul/laranja/fundo neutro)
st.markdown("""
<style>
    /* Cores Oficiais SatAgro:
       Azul Profundo: #0B3D91
       Azul Médio: #2E6FD8
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

# Cabeçalho Principal Sóbrio
st.markdown("""
<div class="satagro-header">
    <span class="badge-prototype">NASA Space Apps Challenge 2026 · Field Shift · Equipe Latino Party</span>
    <h1>SatAgro — Apoio à Decisão na Reforma do Canavial com Dados da NASA</h1>
    <p>Protótipo demonstrativo combinando séries climatológicas da NASA POWER com ordenação heurística transparente baseada nas prioridades do produtor.</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# BARRA LATERAL (SIDEBAR): Separação Explícita de Modos e Prioridades
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Modo de Operação")

    operation_mode = st.radio(
        "Selecione o Modo:",
        options=[
            "🎯 Demonstração (Piloto Sertãozinho - SP)",
            "🌐 Consulta Online (API NASA POWER)"
        ],
        index=0,
        help="O modo Demonstração utiliza dados verificados e coordenadas fixas de Sertãozinho (100% offline). O modo Consulta Online permite buscar novas coordenadas ao vivo."
    )

    is_demo_mode = (operation_mode == "🎯 Demonstração (Piloto Sertãozinho - SP)")

    st.markdown("---")
    st.markdown("### 📍 Localização da Propriedade")

    if is_demo_mode:
        # PROBLEMA 1: Coordenadas estritamente fixas no modo piloto verificado
        active_lat = -21.1378
        active_lon = -47.9897
        location_label = "Sertãozinho — SP (Piloto Cana-de-Açúcar)"

        st.text_input("Localidade Fixa:", value="Sertãozinho — SP", disabled=True, key="demo_loc_name")
        col_dlat, col_dlon = st.columns(2)
        with col_dlat:
            st.number_input("Latitude Fixa:", value=active_lat, format="%.4f", disabled=True, key="demo_lat_fix")
        with col_dlon:
            st.number_input("Longitude Fixa:", value=active_lon, format="%.4f", disabled=True, key="demo_lon_fix")

        st.info("🔒 **Modo Demonstração:** Coordenadas e dados estritamente fixados no dataset verificado do piloto (garantia de execução autônoma offline).")
        # PROBLEMA 2: Botão de consulta NÃO aparece no modo demonstração!
        btn_online_query = False
        use_cache_online = True

    else:
        # Modo Consulta Online: seleção e edição de coordenadas habilitadas
        ONLINE_PRESETS = {
            "Ribeirão Preto — SP (Polo Regional)": (-21.1775, -47.8103),
            "Piracicaba — SP (Centro Tradicional)": (-22.7253, -47.6492),
            "Rio Verde — GO (Expansão Centro-Oeste)": (-17.7924, -50.9192),
            "Sertãozinho — SP (Consulta Ao Vivo)": (-21.1378, -47.9897),
            "Coordenadas Personalizadas": (None, None)
        }

        selected_preset = st.selectbox(
            "Selecionar Local ou Preset:",
            options=list(ONLINE_PRESETS.keys()),
            index=0,
            key="online_preset_select"
        )

        preset_lat, preset_lon = ONLINE_PRESETS[selected_preset]

        col_olat, col_olon = st.columns(2)
        with col_olat:
            active_lat = st.number_input(
                "Latitude:",
                value=preset_lat if preset_lat is not None else -21.1775,
                format="%.4f",
                step=0.01,
                disabled=False,
                key="online_lat_input"
            )
        with col_olon:
            active_lon = st.number_input(
                "Longitude:",
                value=preset_lon if preset_lon is not None else -47.8103,
                format="%.4f",
                step=0.01,
                disabled=False,
                key="online_lon_input"
            )

        location_label = f"Coordenadas ({active_lat:.4f}, {active_lon:.4f})"

        use_cache_online = st.checkbox(
            "Usar cache local se disponível",
            value=True,
            help="Se desmarcado, força uma requisição imediata à API da NASA POWER.",
            key="online_use_cache_box"
        )

        # PROBLEMA 2: Botão de consulta visível e ativo exclusivamente no modo online
        btn_online_query = st.button("🛰️ Consultar API NASA POWER Ao Vivo", type="primary", key="btn_online_consult")

    st.markdown("---")
    st.markdown("### 🎯 Prioridades do Produtor")
    st.caption("Ajuste o peso relativo de cada critério (1 = Menor importância, 5 = Máxima prioridade). O motor de decisão normaliza os pesos e recalcula as notas heurísticas.")

    weight_soil = st.slider("Proteção do Solo (Cobertura)", min_value=1, max_value=5, value=5, key="w_soil")
    weight_n = st.slider("Fixação de N / Matéria Orgânica", min_value=1, max_value=5, value=4, key="w_n")
    weight_pests = st.slider("Quebra de Pragas e Nematoides", min_value=1, max_value=5, value=4, key="w_pests")
    weight_water = st.slider("Tolerância Teórica a Déficit Hídrico", min_value=1, max_value=5, value=3, key="w_water")
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
    st.caption("🔒 *Privacidade:* O SatAgro não armazena dados de propriedades rurais em servidores remotos sem consentimento.")


# ==============================================================================
# CARREGAMENTO DOS DADOS NASA COM SEPARAÇÃO ESTRITA DE MODOS
# ==============================================================================
nasa_data = None
fetch_error = None

if is_demo_mode:
    # MODO DEMONSTRAÇÃO: Carrega exclusivamente o dataset verificado de Sertãozinho
    try:
        nasa_data = load_verified_pilot_dataset()
    except Exception as e:
        fetch_error = f"Erro ao carregar dataset verificado do piloto: {e}"
else:
    # MODO CONSULTA ONLINE: Requisição real à API da NASA para as coordenadas selecionadas
    # Se o botão foi clicado ou na primeira carga da coordenada
    with st.spinner(f"Consultando API da NASA POWER para ({active_lat:.4f}, {active_lon:.4f})..."):
        try:
            nasa_data = fetch_climatology(
                lat=active_lat,
                lon=active_lon,
                use_cache=use_cache_online,
                force_pilot_demo=False
            )
        except NasaDataValidationError as dve:
            fetch_error = f"Dados da NASA Inválidos ou Incompletos: {dve}"
        except NasaPowerConnectionError as nce:
            fetch_error = f"Falha de Conexão com a NASA: {nce}"
        except NasaPowerAPIError as nae:
            fetch_error = f"Erro na API da NASA: {nae}"
        except Exception as e:
            fetch_error = f"Erro inesperado ao consultar a NASA POWER: {e}"

if fetch_error:
    st.error(f"❌ **Falha na Consulta:** {fetch_error}")
    st.markdown("""
    > **Aviso de Integridade:** A consulta online falhou e os dados não puderam ser recuperados para as coordenadas solicitadas.  
    > O SatAgro **nunca substitui silenciosamente** uma consulta online com erro pelos dados do piloto.  
    > Para executar sem conexão externa, altere o modo para **🎯 Demonstração (Piloto Sertãozinho - SP)** no painel lateral.
    """)
    st.stop()


# Cálculo dos Indicadores e Avaliação
metadata = nasa_data.get("metadata", {})
indicators = calculate_climatic_summary(nasa_data["parameters"], metadata=metadata)
signals = evaluate_agroclimatic_signals(indicators, nasa_data["parameters"], metadata=metadata)
rankings = compute_rotation_rankings(producer_priorities, indicators=indicators)


# ==============================================================================
# ABAS PRINCIPAIS
# ==============================================================================
tab_map_data, tab_signals, tab_comparison, tab_methods = st.tabs([
    "🗺️ Localização & Climatologia NASA",
    "⚠️ Sinais Climatológicos Exploratórios",
    "⚖️ Ordenação Heurística das Estratégias",
    "📖 Metodologia, Fontes e Escopo"
])


# ------------------------------------------------------------------------------
# ABA 1: LOCALIZAÇÃO E CLIMATOLOGIA NASA
# ------------------------------------------------------------------------------
with tab_map_data:
    st.markdown(f"#### Localização Ativa: {location_label}")

    # Determinação transparente do status de proveniência
    if is_demo_mode:
        provenance_status = "🟢 Modo Demonstração: Dataset Autêntico Verificado do Piloto (Sertãozinho - SP, sem chamadas externas)"
    elif nasa_data.get("is_cached"):
        provenance_status = f"💾 Modo Online: Dados recuperados do Cache Local Temporário para ({active_lat:.4f}, {active_lon:.4f})"
    else:
        provenance_status = f"🌐 Modo Online: Consulta Realizada Ao Vivo à API NASA POWER para ({active_lat:.4f}, {active_lon:.4f})"

    st.markdown(f"""
    <div class="provenance-card">
        <strong>Fonte Oficial:</strong> {metadata.get('api_name', 'NASA POWER Climatology API')} (Versão: {metadata.get('api_version', 'v2.10.1')})<br>
        <strong>Série Climatológica:</strong> {metadata.get('climatology_range', '2001–2025')}<br>
        <strong>Resolução Meteorológica (T2M, PRECTOTCORR, RH2M):</strong> {metadata.get('spatial_resolution_meteorology')}<br>
        <strong>Status de Proveniência:</strong> {provenance_status}<br>
        <strong>Data/Hora da Coleta Registrada:</strong> {nasa_data.get('collected_at')}<br>
        <strong>Coordenadas Ativas:</strong> Latitude {active_lat:.4f}, Longitude {active_lon:.4f}<br>
        <span style="color: #64748B; font-size: 12px;">ℹ️ <em>{metadata.get('spatial_disclaimer')}</em></span>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_metrics = st.columns([1.1, 0.9])

    with col_map:
        st.markdown("**Mapa da Localização Ativa:**")
        
        # O mapa sempre é centralizado estritamente nas coordenadas ativas
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
                    st.info(f"Ponto clicado: Lat {click_lat:.4f}, Lon {click_lng:.4f}. No Modo Demonstração, as coordenadas são fixas em Sertãozinho. Mude para o 'Modo Consulta Online' para pesquisar este ponto.")
                else:
                    st.info(f"Ponto clicado: Lat {click_lat:.4f}, Lon {click_lng:.4f}. Para consultar este ponto, insira as coordenadas no painel lateral e clique em 'Consultar API NASA POWER Ao Vivo'.")
        except Exception:
            st.info("Visualização cartográfica em modo simplificado. Dados da NASA carregados com sucesso.")

    with col_metrics:
        st.markdown("**Indicadores Climatológicos Verificados:**")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_precipitation']['name']}</div>
                <div class="metric-value">{indicators['annual_precipitation']['value']} {indicators['annual_precipitation']['unit']}</div>
                <div class="metric-caption">Série: {metadata.get('climatology_range', '2001–2025')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_mean_temp']['name']}</div>
                <div class="metric-value">{indicators['annual_mean_temp']['value']} {indicators['annual_mean_temp']['unit']}</div>
                <div class="metric-caption">Média anual a 2m (T2M)</div>
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
                <div class="metric-caption">Chuva no período seco (Abr–Set)</div>
            </div>
            """, unsafe_allow_html=True)

    # Gráficos Mensais
    st.markdown("---")
    st.markdown(f"#### Distribuição Mensal Histórica — {location_label} (NASA POWER MERRA-2)")
    
    raw = indicators["raw_monthly_data"]
    df_climate = pd.DataFrame({
        "Mês": raw["months_pt"],
        "Chuva Média (mm/mês)": raw["rainfall_mm"],
        "Temp. Média (°C)": raw["tmean_c"],
        "Temp. Máxima (°C)": raw["tmax_c"],
        "Temp. Mínima (°C)": raw["tmin_c"],
    })

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.bar_chart(df_climate, x="Mês", y="Chuva Média (mm/mês)", color="#2E6FD8")
        st.caption("Precipitação média mensal (mm/mês). Notar pico nos meses de verão (Dez–Fev), coincidente com a janela de reforma.")
    with col_ch2:
        st.line_chart(df_climate, x="Mês", y=["Temp. Média (°C)", "Temp. Máxima (°C)", "Temp. Mínima (°C)"], color=["#0B3D91", "#F57C00", "#93C5FD"])
        st.caption("Perfil térmico: máximas de verão acima de 30 °C e mínimas de inverno (Jun/Jul) na grade regional.")


# ------------------------------------------------------------------------------
# ABA 2: SINAIS CLIMATOLÓGICOS EXPLORATÓRIOS
# ------------------------------------------------------------------------------
with tab_signals:
    st.markdown("#### Sinais Climatológicos Exploratórios Regionais")
    st.markdown("""
    > **Aviso Científico:** As informações abaixo representam **sinais climatológicos históricos regionais** derivados da série da NASA POWER.
    > Eles **NÃO constituem diagnósticos preditivos de talhão nem medições de risco real**, pois fatores como declividade da encosta,
    > textura pedológica do solo, presença de pragas vivas e microclimas locais exigem monitoramento presencial in loco.
    """)

    for s in signals:
        st.markdown(f"""
        <div class="signal-card" style="border-left: 4px solid {s['badge_color']};">
            <span class="signal-badge" style="background-color: {s['badge_color']};">{s['category']}</span>
            <h4 style="margin: 4px 0 8px 0; color: #0B3D91;">{s['icon']} {s['title']}</h4>
            <p style="margin-bottom: 6px; font-size: 13px; color: #1F2937;"><strong>Observação NASA:</strong> {s['observation']}</p>
            <p style="margin-bottom: 6px; font-size: 13px; color: #B91C1C;"><strong>O que este sinal NÃO significa:</strong> {s['what_it_is_not']}</p>
            <p style="margin-bottom: 4px; font-size: 13px; color: #4B5563;"><strong>Referência Técnica (IAC/Embrapa):</strong> {s['literature_reference']}</p>
            <span style="font-size: 12px; color: #64748B;">⚠️ <em>Limitação Técnica:</em> {s['limitation']}</span>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ABA 3: ORDENAÇÃO HEURÍSTICA DAS ESTRATÉGIAS
# ------------------------------------------------------------------------------
with tab_comparison:
    st.markdown("#### Ordenação Heurística das Estratégias de Reforma do Canavial")
    st.markdown("""
    > **Aviso de Metodologia e Honestidade Intelectual:**  
    > Esta ferramenta utiliza o método de **Ponderação Multicritério (MCDA)** para ordenar quatro estratégias de referência.  
    > **As pontuações são avaliações heurísticas ilustrativas**, calculadas exclusivamente a partir da combinação dos **pesos definidos pelo produtor**
    > com **notas conceituais de referência da literatura agronômica** (IAC, Embrapa, FAO).  
    > **Não se trata de um modelo agronômico calibrado para o local nem de um resultado gerado por satélites da NASA.**  
    > Alterar a localização geográfica atualiza o diagnóstico climático da NASA POWER, mas não recalcula a aptidão das culturas sem dados locais de solo e manejo.
    """)

    # Tabela Resumo da Ordenação
    table_rows = []
    for r in rankings:
        table_rows.append({
            "Posição": f"{r['rank']}º Lugar",
            "Estratégia": r["name"],
            "Tipo": r["crop_type"],
            "Ciclo Típico": r["cycle_days"],
            "Nota Heurística (0 a 100)": f"{r['final_score']} / 100",
            "Grau de Confiança": r["confidence"]
        })
    st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)

    # Gráfico Comparativo
    chart_df = pd.DataFrame({
        "Estratégia": [r["name"] for r in rankings],
        "Pontuação Heurística (0–100)": [r["final_score"] for r in rankings]
    })
    st.bar_chart(chart_df, x="Estratégia", y="Pontuação Heurística (0–100)", color="#2E6FD8")

    # Detalhamento Matemático Dinâmico
    st.markdown("---")
    st.markdown("#### Detalhamento Matemático da Contribuição por Critério")
    st.caption(r"Fórmula aplicada: $S_j = \sum_{i} (w_i \cdot s_{ij}) \times 100$, onde $w_i$ é o peso relativo normalizado pelo usuário e $s_{ij}$ é a nota de referência agronômica.")

    weights_summary = rankings[0]["normalized_weights"]
    weights_display = pd.DataFrame({
        "Critério": [CRITERIA_METADATA[k]["name"] for k in weights_summary.keys()],
        "Prioridade Produtor (1–5)": [int(producer_priorities[k]) for k in weights_summary.keys()],
        "Peso Normalizado ($w_i$)": [f"{weights_summary[k]*100:.1f}%" for k in weights_summary.keys()],
    })
    st.dataframe(weights_display, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Fichas Agronômicas Padronizadas (4 Camadas Explícitas)")
    st.caption("Abra cada estratégia abaixo para verificar separadamente dados NASA, indicadores derivados, literatura agronômica e a avaliação heurística.")

    for r in rankings:
        with st.expander(f"🏅 {r['rank']}º Lugar — {r['name']} (Nota Heurística: {r['final_score']} / 100)"):
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
                    <span class="layer-tag">3. Literatura Técnica de Referência (IAC / Embrapa / CTC)</span>
                    {r['technical_literature']}
                </div>
                <div class="four-layer-box">
                    <span class="layer-tag">4. Avaliação Heurística Ilustrativa (MCDA)</span>
                    {r['heuristic_scoring_explanation']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Lacunas de Informação:** {r['unknowns']}")
                st.markdown(f"**Grau de Confiança:** *{r['confidence']}*")
                st.warning(f"⚠️ **Validação Agronômica Presencial Necessária:** {r['specialist_review']}")

            with c_right:
                st.markdown("**Composição da Nota:**")
                breakdown = r["criteria_contributions"]
                ref_scores = r["reference_scores"]
                c_data = pd.DataFrame({
                    "Critério": [CRITERIA_METADATA[k]["name"] for k in breakdown.keys()],
                    "Nota Ref. ($s_{ij}$)": [ref_scores[k] for k in breakdown.keys()],
                    "Contribuição": [breakdown[k] for k in breakdown.keys()],
                })
                st.dataframe(c_data, hide_index=True, use_container_width=True)


# ------------------------------------------------------------------------------
# ABA 4: METODOLOGIA, FONTES E ESCOPO
# ------------------------------------------------------------------------------
with tab_methods:
    st.markdown("#### Metodologia Científica e Delimitação de Escopo")

    col_mvp, col_future = st.columns(2)
    with col_mvp:
        st.markdown("""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 16px;">
            <h4 style="color: #0B3D91; margin-top: 0;">✅ Funcionalidades Efetivamente Implementadas no MVP</h4>
            <ul style="font-size: 13px; color: #1E3A8A; line-height: 1.6;">
                <li><strong>Modo Demonstração vs Modo Consulta Online:</strong> Separação estrita com fixação de coordenadas para o piloto e requisição real para novos pontos.</li>
                <li><strong>Integração com a API NASA POWER v2.10.1:</strong> Coleta e validação de precipitação (PRECTOTCORR), temperatura média, máxima e mínima (T2M, T2M_MAX, T2M_MIN) e umidade relativa (RH2M).</li>
                <li><strong>Validação Estrita de Dados:</strong> Rejeição de valores sentinela (-999.0), não-finitos ou meses ausentes.</li>
                <li><strong>Proveniência Dinâmica:</strong> Exibição do intervalo temporal real (2001–2025) e distinção entre grade MERRA-2 e escala de talhão.</li>
                <li><strong>Conjunto de Demonstração Verificado:</strong> Dados autênticos pré-validados para Sertãozinho (SP) empacotados no repositório.</li>
                <li><strong>Indicadores Climatológicos Regionais:</strong> Acumulado anual, índice de estiagem de inverno e chuva na reforma.</li>
                <li><strong>Sinais Climatológicos Exploratórios:</strong> Contexto histórico regional com advertência explícita sobre suas limitações.</li>
                <li><strong>Motor de Decisão Heurístico Transparente:</strong> Ponderação multicritério (MCDA) baseada exclusivamente nos pesos do produtor e referências agronômicas.</li>
                <li><strong>Fichas em 4 Camadas:</strong> Separação estrita entre dados NASA, indicadores SatAgro, literatura agronômica e avaliações heurísticas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_future:
        st.markdown("""
        <div style="background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 6px; padding: 16px;">
            <h4 style="color: #C2410C; margin-top: 0;">🔮 Funcionalidades Planejadas (Fase 2 / Pós-Hackathon)</h4>
            <ul style="font-size: 13px; color: #9A3412; line-height: 1.6;">
                <li><strong>Resolução Espacial Fina:</strong> Integração de Sentinel-2 e Landsat 8/9 (10–30 m) para medição de vigor vegetal intra-talhão.</li>
                <li><strong>Topografia SRTM (~30 m):</strong> Extração de Modelo Digital de Elevação para cálculo de declividade e escoamento.</li>
                <li><strong>Umidade do Solo SMAP:</strong> Camadas de umidade superficial e radicular em alta resolução.</li>
                <li><strong>Focos de Calor FIRMS:</strong> Detecção de queimadas na vizinhança imediata da lavoura.</li>
                <li><strong>Calibração com Dados Locais:</strong> Inclusão de dados de solo e talhões informados pelo agricultor.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Referências Técnicas e Científicas")
    st.markdown("""
    1. **AMBROSANO, E. J. et al.** *Adubação verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronômico (IAC), Boletim Técnico.
    2. **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Práticas conservacionistas e fixação biológica de nitrogênio em sistemas de rotação no Centro-Sul.*
    3. **DOORENBOS, J.; KASSAM, A. H.** *Yield response to water.* Rome: FAO, 1979. (FAO Irrigation and Drainage Paper, 33).
    4. **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.10.1).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
    """)

    st.info("""
    **Isenção de Responsabilidade (Disclaimer):**  
    O SatAgro é uma ferramenta educacional e conceitual desenvolvida para o NASA Space Apps Challenge 2026. 
    As estimativas da NASA possuem resolução regional (~50 km) e a ferramenta heurística de rotação reflete conceitos bibliográficos gerais. 
    Nenhum resultado substitui a análise de solo, a amostragem fitossanitária presencial ou a prescrição de um Engenheiro Agrônomo.
    """)
