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
# BARRA LATERAL (SIDEBAR): Localização e Prioridades do Produtor
# ==============================================================================
with st.sidebar:
    st.markdown("### 📍 Localização de Referência")

    PRESETS = {
        "Sertãozinho — SP (Piloto Cana)": (-21.1378, -47.9897),
        "Ribeirão Preto — SP (Polo Regional)": (-21.1775, -47.8103),
        "Piracicaba — SP (Centro Tradicional)": (-22.7253, -47.6492),
        "Rio Verde — GO (Expansão Centro-Oeste)": (-17.7924, -50.9192),
        "Coordenadas Personalizadas": (None, None)
    }

    selected_preset = st.selectbox(
        "Local Selecionado:",
        options=list(PRESETS.keys()),
        index=0
    )

    preset_lat, preset_lon = PRESETS[selected_preset]

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat_val = st.number_input(
            "Latitude:",
            value=preset_lat if preset_lat is not None else -21.1378,
            format="%.4f",
            step=0.01
        )
    with col_lon:
        lon_val = st.number_input(
            "Longitude:",
            value=preset_lon if preset_lon is not None else -47.9897,
            format="%.4f",
            step=0.01
        )

    # Opção de demonstração garantida para o piloto
    use_verified_pilot = False
    if "Sertãozinho" in selected_preset:
        use_verified_pilot = st.checkbox(
            "Usar Demonstração Verificada do Piloto (Garante execução 100% offline)",
            value=False,
            help="Carrega o conjunto autêntico previamente coletado e verificado da NASA POWER empacotado no repositório."
        )

    st.markdown("---")
    st.markdown("### 🎯 Prioridades do Produtor")
    st.caption("Ajuste o peso relativo de cada critério (1 = Menor importância, 5 = Máxima prioridade). O motor de decisão normaliza os pesos e recalcula as notas heurísticas.")

    weight_soil = st.slider("Proteção do Solo (Cobertura)", min_value=1, max_value=5, value=5)
    weight_n = st.slider("Fixação de N / Matéria Orgânica", min_value=1, max_value=5, value=4)
    weight_pests = st.slider("Quebra de Pragas e Nematoides", min_value=1, max_value=5, value=4)
    weight_water = st.slider("Tolerância Teórica a Déficit Hídrico", min_value=1, max_value=5, value=3)
    weight_income = st.slider("Renda Direta na Entressafra", min_value=1, max_value=5, value=3)
    weight_ops = st.slider("Simplicidade Operacional", min_value=1, max_value=5, value=2)

    producer_priorities = {
        "protecao_solo": weight_soil,
        "fixacao_nitrogenio": weight_n,
        "quebra_pragas": weight_pests,
        "resiliencia_hidrica": weight_water,
        "renda_adicional": weight_income,
        "simplicidade_operacional": weight_ops,
    }

    st.markdown("---")
    force_refresh = st.button("🔄 Consultar API NASA POWER Ao Vivo")
    st.caption("🔒 *Privacidade:* O SatAgro não armazena dados de propriedades rurais em servidores remotos sem consentimento.")


# ==============================================================================
# CARREGAMENTO DOS DADOS REAIS DA NASA POWER COM TRATAMENTO DE ERROS E AUDITORIA
# ==============================================================================
nasa_data = None
fetch_error = None
error_type = None

with st.spinner("Recuperando e validando dados climatológicos da NASA POWER..."):
    try:
        if use_verified_pilot:
            nasa_data = load_verified_pilot_dataset()
        else:
            nasa_data = fetch_climatology(lat_val, lon_val, use_cache=not force_refresh)
    except NasaDataValidationError as dve:
        fetch_error = f"Dados da NASA Inválidos ou Incompletos: {dve}"
        error_type = "validation"
    except NasaPowerConnectionError as nce:
        fetch_error = f"Falha de Conexão: {nce}"
        error_type = "connection"
    except NasaPowerAPIError as nae:
        fetch_error = f"Erro na API da NASA: {nae}"
        error_type = "api"
    except Exception as e:
        fetch_error = f"Erro inesperado: {e}"
        error_type = "unexpected"

if fetch_error:
    st.error(f"❌ **Indisponível:** {fetch_error}")
    st.markdown("""
    > **Aviso de Integridade:** O SatAgro não substitui dados ausentes da NASA por números simulados ou zeros arbitrários.
    """)
    if error_type in ["connection", "api", "validation"] and "Sertãozinho" in selected_preset:
        if st.button("Carregar Demonstração Verificada do Piloto (Sertãozinho - SP)"):
            st.session_state["force_demo"] = True
            st.rerun()
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
    st.markdown("#### Localização Selecionada e Proveniência Verificada dos Dados")

    # Aviso offline, se houver
    if nasa_data.get("offline_notice"):
        st.warning(f"ℹ️ {nasa_data['offline_notice']}")

    # Proveniência extraída dinamicamente dos metadados da resposta da NASA (P0.4)
    provenance_status = (
        "🟢 Demonstração Verificada do Piloto (Empacotada no Repositório)"
        if nasa_data.get("is_verified_pilot")
        else ("💾 Cache Local Verificado" if nasa_data.get("is_cached") else "🌐 Consulta Direta Ao Vivo à API da NASA POWER")
    )

    st.markdown(f"""
    <div class="provenance-card">
        <strong>Fonte Oficial:</strong> {metadata.get('api_name', 'NASA POWER Climatology API')} (Versão: {metadata.get('api_version', 'v2.10.1')})<br>
        <strong>Série Climatológica:</strong> {metadata.get('climatology_range', '2001–2025')}<br>
        <strong>Resolução Meteorológica (T2M, PRECTOTCORR, RH2M):</strong> {metadata.get('spatial_resolution_meteorology')}<br>
        <strong>Status da Conexão / Proveniência:</strong> {provenance_status}<br>
        <strong>Data/Hora da Coleta Registrada:</strong> {nasa_data.get('collected_at')}<br>
        <strong>Coordenadas Ativas:</strong> Latitude {lat_val:.4f}, Longitude {lon_val:.4f}<br>
        <span style="color: #64748B; font-size: 12px;">ℹ️ <em>{metadata.get('spatial_disclaimer')}</em></span>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_metrics = st.columns([1.1, 0.9])

    with col_map:
        st.markdown("**Mapa Interativo da Localização:**")
        st.caption("Marcador posicionado nas coordenadas ativas. Clique no mapa para inspecionar novos pontos.")
        
        m = folium.Map(location=[lat_val, lon_val], zoom_start=11, tiles="OpenStreetMap")
        folium.CircleMarker(
            location=[lat_val, lon_val],
            radius=8,
            color="#0B3D91",
            fill=True,
            fill_color="#F57C00",
            fill_opacity=0.9,
            popup=f"Ponto de Análise ({lat_val:.4f}, {lon_val:.4f})"
        ).add_to(m)

        try:
            map_data = st_folium(m, height=340, width=None, key="satagro_map")
            if map_data and map_data.get("last_clicked"):
                click_lat = map_data["last_clicked"]["lat"]
                click_lng = map_data["last_clicked"]["lng"]
                st.info(f"Ponto selecionado via clique: Lat {click_lat:.4f}, Lon {click_lng:.4f}. Para atualizar o diagnóstico, insira estes valores no painel lateral.")
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
    st.markdown("#### Distribuição Mensal Histórica (Série NASA POWER MERRA-2)")
    
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
        st.caption("Perfil térmico: máximas de verão acima de 30 °C e mínimas de inverno (Jun/Jul) em torno de 7–8 °C na grade regional.")


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
    > **Aviso de Metodologia e Honestidade Intelectual (P0.1):**  
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

    # Detalhamento Matemático Dinâmico (P0.1)
    st.markdown("---")
    st.markdown("#### Detalhamento Matemático da Contribuição por Critério")
    st.caption(r"Fórmula aplicada: $S_j = \sum_{i} (w_i \cdot s_{ij}) \times 100$, onde $w_i$ é o peso relativo normalizado pelo usuário e $s_{ij}$ é a nota de referência agronômica.")

    # Tabela dinâmica de pesos e contribuições
    weights_summary = rankings[0]["normalized_weights"]
    weights_display = pd.DataFrame({
        "Critério": [CRITERIA_METADATA[k]["name"] for k in weights_summary.keys()],
        "Prioridade Produtor (1–5)": [int(producer_priorities[k]) for k in weights_summary.keys()],
        "Peso Normalizado ($w_i$)": [f"{weights_summary[k]*100:.1f}%" for k in weights_summary.keys()],
    })
    st.dataframe(weights_display, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Fichas Agronômicas Padronizadas (4 Camadas Explícitas — P0.6)")
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
                <li><strong>Integração com a API NASA POWER v2.10.1:</strong> Coleta e validação de precipitação (PRECTOTCORR), temperatura média, máxima e mínima (T2M, T2M_MAX, T2M_MIN) e umidade relativa (RH2M).</li>
                <li><strong>Validação Estrita de Dados (P0.3):</strong> Rejeição de valores sentinela (-999.0), não-finitos ou meses ausentes.</li>
                <li><strong>Proveniência Dinâmica (P0.4):</strong> Exibição do intervalo temporal real (2001–2025) e distinção entre grade MERRA-2 e escala de talhão.</li>
                <li><strong>Conjunto de Demonstração Verificado (P0.7):</strong> Dados autênticos pré-validados para Sertãozinho (SP) empacotados no repositório.</li>
                <li><strong>Indicadores Climatológicos Regionais (P0.5):</strong> Acumulado anual, índice de estiagem de inverno e chuva na reforma (sem fórmulas experimentais de ET0 não validadas).</li>
                <li><strong>Sinais Climatológicos Exploratórios (P0.5):</strong> Contexto histórico regional com advertência explícita sobre suas limitações.</li>
                <li><strong>Motor de Decisão Heurístico Transparente (P0.1):</strong> Ponderação multicritério (MCDA) baseada exclusivamente nos pesos do produtor e referências agronômicas.</li>
                <li><strong>Fichas em 4 Camadas (P0.6):</strong> Separação estrita entre dados NASA, indicadores SatAgro, literatura agronômica e avaliações heurísticas.</li>
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
                <li><strong>Calibração de Modelos Locais:</strong> Inclusão de dados laboratoriais de solo informados pelo agricultor.</li>
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
