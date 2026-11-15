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

from satagro.nasa_power import fetch_climatology, NasaPowerError
from satagro.indicators import calculate_climatic_summary
from satagro.alerts import evaluate_agroclimatic_alerts
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
    /* Cores do Projeto:
       Azul Profundo: #0B3D91
       Azul Médio: #2E6FD8
       Laranja Atenção: #F57C00
       Fundo: #F5F7FA
       Texto: #1F2937
    */
    .main {
        background-color: #F5F7FA;
    }
    .satagro-header {
        background: #0B3D91;
        padding: 22px 28px;
        border-radius: 8px;
        color: #FFFFFF;
        margin-bottom: 20px;
    }
    .satagro-header h1 {
        color: #FFFFFF;
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .satagro-header p {
        color: #E2E8F0;
        margin: 6px 0 0 0;
        font-size: 14px;
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
        margin-bottom: 8px;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-title {
        color: #6B7280;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        color: #0B3D91;
        font-size: 24px;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-caption {
        color: #4B5563;
        font-size: 12px;
    }
    .provenance-box {
        background: #FFFFFF;
        border-left: 4px solid #2E6FD8;
        border-top: 1px solid #E5E7EB;
        border-right: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        border-radius: 4px;
        padding: 12px 16px;
        font-size: 13px;
        color: #374151;
        margin-bottom: 16px;
    }
    .alert-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .alert-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        color: #FFFFFF;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho da Aplicação
st.markdown("""
<div class="satagro-header">
    <span class="badge-prototype">NASA Space Apps Challenge 2026 · Field Shift · Equipe Latino Party</span>
    <h1>SatAgro — Apoio à Decisão na Reforma do Canavial com Dados NASA</h1>
    <p>Protótipo demonstrativo com dados climáticos reais da NASA POWER, alertas explicáveis e comparação multicritério de rotações de culturas.</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# BARRA LATERAL (SIDEBAR): Localização, Prioridades e Cenários
# ==============================================================================
with st.sidebar:
    st.markdown("### 📍 Localização da Propriedade")

    PRESETS = {
        "Sertãozinho — SP (Piloto Cana)": (-21.1378, -47.9897),
        "Ribeirão Preto — SP (Polo Regional)": (-21.1775, -47.8103),
        "Piracicaba — SP (Centro Tradicional)": (-22.7253, -47.6492),
        "Rio Verde — GO (Expansão Centro-Oeste)": (-17.7924, -50.9192),
        "Coordenadas Personalizadas": (None, None)
    }

    selected_preset = st.selectbox(
        "Local de Referência:",
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

    st.markdown("---")
    st.markdown("### 🎯 Prioridades do Produtor")
    st.caption("Ajuste o peso relativo de cada critério para personalizar a recomendação (1 = Menor importância, 5 = Máxima prioridade).")

    weight_soil = st.slider("Proteção do Solo / Erosão", min_value=1, max_value=5, value=5)
    weight_n = st.slider("Fixação de N / Matéria Orgânica", min_value=1, max_value=5, value=4)
    weight_pests = st.slider("Quebra de Pragas e Nematoides", min_value=1, max_value=5, value=4)
    weight_water = st.slider("Resiliência Hídrica / Seca", min_value=1, max_value=5, value=3)
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
    st.markdown("### 🌦️ Cenário Climático (Sensibilidade)")
    st.caption("Perturbação climática para avaliar a robustez das estratégias frente a anomalias:")
    scenario_rain = st.slider("Variação de Chuva (%)", min_value=-30, max_value=30, value=0, step=5)
    scenario_temp = st.slider("Variação de Temperatura (°C)", min_value=-1.0, max_value=3.0, value=0.0, step=0.5)

    climate_scenario = {
        "rain_delta_pct": float(scenario_rain),
        "temp_delta_c": float(scenario_temp)
    }

    st.markdown("---")
    force_refresh = st.button("🔄 Recarregar Dados da NASA")


# ==============================================================================
# CARREGAMENTO DOS DADOS REAIS DA NASA POWER COM TRATAMENTO DE ERROS
# ==============================================================================
nasa_data = None
fetch_error = None

with st.spinner("Conectando à API da NASA POWER e recuperando climatologia..."):
    try:
        nasa_data = fetch_climatology(lat_val, lon_val, use_cache=not force_refresh)
    except NasaPowerError as npe:
        fetch_error = str(npe)
    except Exception as e:
        fetch_error = f"Erro inesperado ao consultar a NASA POWER: {e}"

if fetch_error:
    st.error(f"❌ **Falha na Coleta de Dados:** {fetch_error}")
    st.warning("O SatAgro não inventa dados climáticos simulados. Verifique a conectividade de rede com a API da NASA ou tente novamente.")
    st.stop()


# Cálculo dos Indicadores
indicators = calculate_climatic_summary(nasa_data["parameters"], lat=lat_val)
alerts = evaluate_agroclimatic_alerts(indicators, nasa_data["parameters"])
rankings = compute_rotation_rankings(producer_priorities, indicators, climate_scenario)


# ==============================================================================
# ABAS PRINCIPAIS
# ==============================================================================
tab_map_data, tab_alerts, tab_comparison, tab_methods = st.tabs([
    "🗺️ Localização & Dados NASA",
    "⚠️ Alertas Agroclimáticos",
    "⚖️ Comparação de Estratégias",
    "📖 Metodologia, Fontes e Escopo"
])


# ------------------------------------------------------------------------------
# ABA 1: LOCALIZAÇÃO E DADOS NASA
# ------------------------------------------------------------------------------
with tab_map_data:
    st.markdown("#### Localização Selecionada e Proveniência dos Dados")

    # Banner de Proveniência Real dos Dados
    cache_tag = "✅ Em Cache Local (Offline / Resposta Imediata)" if nasa_data.get("is_cached") else "🌐 Consulta Direta Ao Vivo à API da NASA"
    st.markdown(f"""
    <div class="provenance-box">
        <strong>Fonte Oficial:</strong> {nasa_data.get('source')}<br>
        <strong>Resolução Espacial:</strong> {nasa_data.get('spatial_resolution')} · 
        <strong>Abrangência Temporal:</strong> Climatologia Histórica de 30 Anos<br>
        <strong>Coleta Registrada:</strong> {nasa_data.get('collected_at')} · 
        <strong>Status de Proveniência:</strong> {cache_tag}<br>
        <strong>Coordenadas Ativas:</strong> Latitude {lat_val:.4f}, Longitude {lon_val:.4f}
    </div>
    """, unsafe_allow_html=True)

    col_map, col_metrics = st.columns([1.1, 0.9])

    with col_map:
        st.markdown("**Mapa Interativo da Propriedade / Região:**")
        st.caption("Você pode clicar no mapa para inspecionar a região-piloto (Sertãozinho - SP).")
        
        # Renderização do mapa Folium
        m = folium.Map(location=[lat_val, lon_val], zoom_start=11, tiles="OpenStreetMap")
        folium.CircleMarker(
            location=[lat_val, lon_val],
            radius=8,
            color="#0B3D91",
            fill=True,
            fill_color="#F57C00",
            fill_opacity=0.9,
            popup=f"Talhão / Área SatAgro ({lat_val:.4f}, {lon_val:.4f})"
        ).add_to(m)

        map_data = st_folium(m, height=360, width=None, key="satagro_map")
        if map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lng = map_data["last_clicked"]["lng"]
            st.info(f"Ponto clicado no mapa: Lat {click_lat:.4f}, Lon {click_lng:.4f}. (Para recalcular com este ponto, insira as coordenadas no painel lateral).")

    with col_metrics:
        st.markdown("**Indicadores Agroclimáticos Consolidados:**")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_precipitation']['name']}</div>
                <div class="metric-value">{indicators['annual_precipitation']['value']} {indicators['annual_precipitation']['unit']}</div>
                <div class="metric-caption">Confiança: <strong>{indicators['annual_precipitation']['confidence']}</strong></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_mean_temp']['name']}</div>
                <div class="metric-value">{indicators['annual_mean_temp']['value']} {indicators['annual_mean_temp']['unit']}</div>
                <div class="metric-caption">Confiança: <strong>{indicators['annual_mean_temp']['confidence']}</strong></div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['reform_window_rain']['name']}</div>
                <div class="metric-value">{indicators['reform_window_rain']['value']} {indicators['reform_window_rain']['unit']}</div>
                <div class="metric-caption">Concentração: <strong>{indicators['seasonal_dry_ratio']['value']}% no inverno</strong></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{indicators['annual_et0']['name']}</div>
                <div class="metric-value">{indicators['annual_et0']['value']} {indicators['annual_et0']['unit']}</div>
                <div class="metric-caption">Demanda hídrica atmosférica anual</div>
            </div>
            """, unsafe_allow_html=True)

    # Gráfico Climatológico Mensal
    st.markdown("---")
    st.markdown("#### Distribuição Mensal de Precipitação e Temperatura (Série Histórica NASA POWER)")
    
    raw = indicators["raw_monthly_data"]
    df_climate = pd.DataFrame({
        "Mês": raw["months_pt"],
        "Chuva Média (mm/mês)": raw["rainfall_mm"],
        "Temp. Média (°C)": raw["tmean_c"],
        "Temp. Máx (°C)": raw["tmax_c"],
        "Temp. Mín (°C)": raw["tmin_c"],
        "ET0 Estimada (mm/mês)": raw["et0_mm"],
    })

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.bar_chart(df_climate, x="Mês", y="Chuva Média (mm/mês)", color="#2E6FD8")
        st.caption("Chuva acumulada mensal (mm/mês). Observe o pico pluvial entre dezembro e fevereiro, coincidente com o período de reforma.")
    with col_chart2:
        st.line_chart(df_climate, x="Mês", y=["Temp. Média (°C)", "Temp. Máx (°C)", "Temp. Mín (°C)"], color=["#0B3D91", "#F57C00", "#60A5FA"])
        st.caption("Perfil térmico anual: máximas no verão acima de 30°C e mínimas no inverno (junho/julho) próximas a 7-8°C.")


# ------------------------------------------------------------------------------
# ABA 2: ALERTAS AGROCLIMÁTICOS
# ------------------------------------------------------------------------------
with tab_alerts:
    st.markdown("#### Diagnóstico de Riscos e Condições Agroclimáticas na Janela de Reforma")
    st.markdown("""
    Os alertas a seguir resultam da análise dos parâmetros de 30 anos da NASA POWER cruzados com as exigências agronômicas 
    da cana-de-açúcar e das culturas de rotação. Cada alerta expõe a fundamentação científica e as limitações de escala.
    """)

    for alert in alerts:
        st.markdown(f"""
        <div class="alert-card" style="border-left: 5px solid {alert['badge_color']};">
            <span class="alert-badge" style="background-color: {alert['badge_color']};">
                {alert['icon']} {alert['level']}
            </span>
            <h4 style="margin: 4px 0 8px 0; color: #0B3D91;">{alert['title']}</h4>
            <p style="margin-bottom: 8px; color: #1F2937; font-size: 14px;"><strong>Diagnóstico:</strong> {alert['summary']}</p>
            <div style="font-size: 13px; color: #4B5563; line-height: 1.5;">
                <strong>Evidência Utilizada:</strong> {alert['evidence']}<br>
                <strong>Fundamentação Científica:</strong> {alert['scientific_basis']}<br>
                <strong>Recomendação Prática:</strong> {alert['recommendation']}<br>
                <span style="color: #9A3412;">⚠️ <em>Limitação:</em> {alert['limitation']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# ABA 3: COMPARAÇÃO DE ESTRATÉGIAS DE REFORMA
# ------------------------------------------------------------------------------
with tab_comparison:
    st.markdown("#### Comparação Demonstrativa de Estratégias de Reforma do Canavial")
    st.markdown("""
    O motor de decisão do SatAgro avalia quatro estratégias frente às **prioridades informadas pelo produtor** e ao **cenário climático configurado**.
    As pontuações são baseadas em regras explícitas da literatura (IAC, Embrapa, FAO 56) e normalizadas de 0 a 100.
    """)

    # Tabela Resumo do Ranking
    ranking_data = []
    for r in rankings:
        ranking_data.append({
            "Posição": f"{r['rank']}º Lugar",
            "Estratégia": r["name"],
            "Tipo": r["crop_type"],
            "Ciclo Típico": r["cycle_days"],
            "Pontuação SatAgro": f"{r['final_score']} / 100",
            "Confiança": r["confidence"]
        })
    df_ranking = pd.DataFrame(ranking_data)
    st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    # Gráfico de Barras Comparativo
    chart_df = pd.DataFrame({
        "Estratégia": [r["name"] for r in rankings],
        "Pontuação (0–100)": [r["final_score"] for r in rankings]
    })
    st.bar_chart(chart_df, x="Estratégia", y="Pontuação (0–100)", color="#2E6FD8")

    st.markdown("---")
    st.markdown("#### Fichas Padronizadas Explicativas por Estratégia")
    st.caption("Abra cada estratégia abaixo para inspecionar os critérios, benefícios, evidências e riscos detalhados.")

    for r in rankings:
        badge_style = "background-color: #0B3D91; color: white;" if r["rank"] == 1 else "background-color: #E2E8F0; color: #1E293B;"
        with st.expander(f"🏅 {r['rank']}º Lugar — {r['name']} (Nota: {r['final_score']} / 100)"):
            c_left, c_right = st.columns([1.2, 0.8])

            with c_left:
                st.markdown(f"**Por que foi avaliada com esta nota:**  \n{r['why_suggested']}")
                st.markdown(f"**Benefícios Esperados:**  \n{r['benefits']}")
                st.markdown(f"**Riscos e Pontos Críticos:**  \n{r['risks']}")
                st.markdown(f"**Lacunas de Informação:**  \n{r['unknowns']}")
                st.markdown(f"**Evidências e Dados NASA:**  \n{r['evidence']}")
                st.markdown(f"**Grau de Confiança:**  \n{r['confidence']}")
                st.warning(f"**⚠️ Revisão Agronômica Local Necessária:**  \n{r['specialist_review']}")

            with c_right:
                st.markdown("**Desempenho por Critério Ponderado:**")
                breakdown = r["criteria_contributions"]
                weights = r["normalized_weights"]
                crit_df = pd.DataFrame({
                    "Critério": [CRITERIA_METADATA[k]["name"] for k in breakdown.keys()],
                    "Peso Produtor": [f"{weights[k]*100:.1f}%" for k in breakdown.keys()],
                    "Contribuição": [breakdown[k] for k in breakdown.keys()]
                })
                st.dataframe(crit_df, hide_index=True, use_container_width=True)


# ------------------------------------------------------------------------------
# ABA 4: METODOLOGIA, FONTES E ESCOPO
# ------------------------------------------------------------------------------
with tab_methods:
    st.markdown("#### Metodologia Científica e Delimitação de Escopo")

    col_mvp, col_future = st.columns(2)
    with col_mvp:
        st.markdown("""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; padding: 16px;">
            <h4 style="color: #0B3D91; margin-top: 0;">✅ Funcionalidades Efetivamente Implementadas (MVP)</h4>
            <ul style="font-size: 13px; color: #1E3A8A; line-height: 1.6;">
                <li><strong>Integração Real com NASA POWER API v2.0:</strong> Consulta direta de precipitação (PRECTOTCORR), temperatura (T2M, T2M_MAX, T2M_MIN), umidade (RH2M) e radiação solar (ALLSKY_SFC_SW_DWN).</li>
                <li><strong>Cache Local Determinístico:</strong> Gravação e leitura em <code>.cache/nasa_power/</code> com rastreamento temporal UTC de coleta.</li>
                <li><strong>Seleção Geoespacial:</strong> Escolha livre de coordenadas com piloto focado em Sertãozinho (SP) e polos do interior paulista.</li>
                <li><strong>Cálculo de Indicadores Climatológicos:</strong> Acumulado anual, índice de estiagem, balanço hídrico sazonal e ET0 simplificada.</li>
                <li><strong>Sistema de Alertas Explicáveis:</strong> Diagnósticos de erosão, veranico, pragas e geada com fundamentação da Embrapa/IAC.</li>
                <li><strong>Motor de Decisão Multicritério (MCDA):</strong> Ponderação configurável das prioridades do produtor e ajuste a cenários climáticos.</li>
                <li><strong>Fichas Padronizadas:</strong> Justificativas, evidências, benefícios, riscos, lacunas e confiança para 4 estratégias de reforma.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_future:
        st.markdown("""
        <div style="background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 6px; padding: 16px;">
            <h4 style="color: #C2410C; margin-top: 0;">🔮 Funcionalidades Planejadas (Fase 2 / Pós-Hackathon)</h4>
            <ul style="font-size: 13px; color: #9A3412; line-height: 1.6;">
                <li><strong>Satélites de Alta Resolução:</strong> Integração de Sentinel-2 e Landsat 8/9 (10–30m) para cálculo de NDVI intra-talhão.</li>
                <li><strong>Umidade do Solo SMAP:</strong> Extração direta de camadas do SMAP (9–36 km) e assimilação no balanço hídrico.</li>
                <li><strong>Topografia SRTM:</strong> Extração de Modelo Digital de Elevação para cálculo de declividade exata e risco de enxurrada.</li>
                <li><strong>Focos de Calor FIRMS:</strong> Monitoramento de queimadas recentes na vizinhança do canavial.</li>
                <li><strong>Entrada de Polígonos de Fazenda:</strong> Upload de arquivos Shapefile, GeoJSON ou KML para análise por talhão.</li>
                <li><strong>Previsão de Curto Prazo:</strong> Acoplamento de previsões numéricas de 7 a 15 dias.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Referências Agronômicas e Científicas")
    st.markdown("""
    1. **ALLEN, R. G.; PEREIRA, L. S.; RAES, D.; SMITH, M.** *Crop evapotranspiration: guidelines for computing crop water requirements.* Rome: FAO, 1998. (FAO Irrigation and Drainage Paper, 56).
    2. **AMBROSANO, E. J. et al.** *Adubação verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronômico (IAC), Boletim Técnico.
    3. **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Práticas conservacionistas e fixação biológica de nitrogênio em sistemas de rotação cana-soja.*
    4. **DOORENBOS, J.; KASSAM, A. H.** *Yield response to water.* Rome: FAO, 1979. (FAO Irrigation and Drainage Paper, 33).
    5. **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.0).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
    """)

    st.info("""
    **Declaração de Isenção de Responsabilidade (Disclaimer):**  
    O SatAgro é uma ferramenta educacional e demonstrativa desenvolvida para o NASA Space Apps Challenge 2026. 
    As estimativas de satélite possuem resolução regional e não substituem análises laboratoriais de fertilidade de solo, 
    amostragem fitossanitária in loco nem o parecer técnico emitido por um profissional legalmente habilitado (Engenheiro Agrônomo).
    """)
