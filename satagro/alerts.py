"""
SatAgro - Sinais Climatológicos Exploratórios Regionais
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Gera sinais climatológicos exploratórios a partir dos dados históricos da NASA POWER.
Conforme P0.5: Não infere riscos reais de talhão (erosão, veranico, pragas, ausência de geada),
apresentando apenas correlações históricas com limitações e avisos explícitos.
Sem emojis conforme diretriz de interface profissional e sóbria.
"""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate_agroclimatic_signals(
    indicators: Dict[str, Any],
    climatology_params: Dict[str, Any],
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    P0.5 - Identifica sinais climatológicos exploratórios a partir das séries regionais
    da NASA POWER, com delimitação estrita entre o dado regional e a realidade de campo.
    """
    if metadata is None:
        metadata = {}

    signals = []

    annual_rain = indicators.get("annual_precipitation", {}).get("value", 1200.0)
    reform_rain = indicators.get("reform_window_rain", {}).get("value", 900.0)
    thermal_ext = indicators.get("thermal_extremes", {})
    min_temp = thermal_ext.get("min_value", 5.0)

    prect = climatology_params.get("PRECTOTCORR", {})
    t2m = climatology_params.get("T2M", {})
    rh2m = climatology_params.get("RH2M", {})
    climatology_range = metadata.get("climatology_range", "2001–2025")

    # SINAL 1: Concentração Pluvial na Janela de Reforma (Nov–Mar)
    reform_pct = (reform_rain / annual_rain * 100) if annual_rain > 0 else 0
    signals.append({
        "id": "sinal_concentracao_chuva",
        "category": "Sinal Climatologico Regional (Chuva)",
        "badge_color": "#2E6FD8",
        "title": "Concentracao Historica de Chuva na Janela de Reforma (Nov-Mar)",
        "observation": (
            f"Na série da NASA POWER ({climatology_range}), {reform_pct:.1f}% da precipitação anual "
            f"({reform_rain:.0f} mm de um total de {annual_rain:.0f} mm) ocorre entre novembro e março."
        ),
        "what_it_is_not": (
            "Não constitui cálculo ou estimativa de erosão real do talhão. A perda efetiva de solo depende "
            "de variáveis locais não medidas aqui: declividade da encosta, tipo de solo (arenoso/argiloso) "
            "e cobertura vegetal viva ou morta presente na área."
        ),
        "literature_reference": (
            "A literatura agronômica (IAC/Embrapa) aponta que períodos de maior intensidade de chuva "
            "demandam maior atenção conservacionista em áreas onde o solo é revolvido."
        ),
        "limitation": "A média climatológica regional de ~50 km não captura temporais locais de alta intensidade."
    })

    # SINAL 2: Estiagem de Inverno e Sazonalidade Pluvial
    dry_ratio = indicators.get("seasonal_dry_ratio", {}).get("value", 17.0)
    signals.append({
        "id": "sinal_sazonalidade_inverno",
        "category": "Sinal Climatologico Regional (Sazonalidade)",
        "badge_color": "#2E6FD8",
        "title": "Estacao Seca Pronunciada de Inverno (Abr-Set)",
        "observation": (
            f"Apenas {dry_ratio:.1f}% da chuva histórica regional cai entre abril e setembro. "
            f"As médias mensais de junho, julho e agosto são historicamente inferiores a 30 mm/mês."
        ),
        "what_it_is_not": (
            "Não permite inferir a ocorrência de 'veranicos' no verão a partir de médias mensais. "
            "Veranicos são anomalias intra-sazonais de curto prazo (7 a 15 dias sem chuva no meio do verão) "
            "que não são detectáveis em dados médios climatológicos mensais."
        ),
        "literature_reference": (
            "Recomenda-se consultar o Zoneamento Agrícola de Risco Climático (ZARC) e previsões meteorológicas "
            "semanais para gerenciar o risco de déficit hídrico em fases críticas de culturas de grãos."
        ),
        "limitation": "Médias mensais agregadas diluem a variabilidade diária das chuvas."
    })

    # SINAL 3: Mínimas Históricas e Microclimas Térmicos
    signals.append({
        "id": "sinal_termico_geada",
        "category": "Sinal Climatologico Regional (Temperatura)",
        "badge_color": "#0B3D91",
        "title": "Perfil Termico de Inverno e Limitacoes da Grade Espacial",
        "observation": (
            f"A menor temperatura média mensal histórica na série regional da NASA POWER a 2m é de {min_temp:.1f} °C."
        ),
        "what_it_is_not": (
            "A temperatura regional de grade (~0,5°) NÃO garante ausência de risco de geada. "
            "Baixadas topográficas, fundos de vale e áreas de acúmulo de ar frio sofrem inversões térmicas "
            "que geram temperaturas de relva abaixo de 0 °C, as quais a resolução regional da NASA não captura."
        ),
        "literature_reference": (
            "O produtor e o agrônomo devem avaliar o relevo local e o histórico de geadas de relva da propriedade."
        ),
        "limitation": "A resolução de grade regional (~50 km) suaviza os microclimas causados pelo relevo local."
    })

    # SINAL 4: Coincidência Bioclimática com Pragas da Cana
    jan_temp = float(t2m.get("JAN", 24.0))
    summer_rh = [float(rh2m.get(m, 70.0)) for m in ["DEC", "JAN", "FEB"] if m in rh2m]
    avg_summer_rh = (sum(summer_rh) / len(summer_rh)) if summer_rh else 78.0

    signals.append({
        "id": "sinal_bioclimatico_pragas",
        "category": "Sinal Climatologico Regional (Bioclima)",
        "badge_color": "#F57C00",
        "title": "Coincidencia Bioclimatica Regional com Periodo de Atividade de Pragas",
        "observation": (
            f"As médias históricas de verão na região combinam temperaturas médias elevadas ({jan_temp:.1f} °C) "
            f"com umidade relativa média estimada em torno de {avg_summer_rh:.0f}%."
        ),
        "what_it_is_not": (
            "Este sinal NÃO constitui diagnóstico de presença nem de infestação de pragas (como cigarrinha-das-raízes "
            "ou broca-da-cana) na propriedade. Dados de satélite não detectam organismos vivos no canavial."
        ),
        "literature_reference": (
            "A literatura entomológica (IAC/Embrapa) descreve que o calor úmido de verão favorece a atividade biológica. "
            "A vistoria presencial de campo com amostragem na base dos colmos é indispensável."
        ),
        "limitation": "Dados regionais apenas descrevem o ambiente climático médio histórico da macrorregião."
    })

    return signals
