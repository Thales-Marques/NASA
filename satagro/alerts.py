"""
SatAgro - Sistema de Alertas Agroclimáticos Explicáveis
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Gera diagnósticos e alertas transparentes com base na climatologia e dados
recentes da NASA POWER, com fundamentação científica e avisos de limitação.
"""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate_agroclimatic_alerts(
    indicators: Dict[str, Any],
    climatology_params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Avalia condições de risco agroclimático para a cultura de referência
    (cana-de-açúcar e janela de reforma) a partir dos dados NASA.
    """
    alerts = []

    annual_rain = indicators.get("annual_precipitation", {}).get("value", 1200.0)
    reform_rain = indicators.get("reform_window_rain", {}).get("value", 900.0)
    min_temp = indicators.get("frost_risk_minimum", {}).get("value", 4.0)
    
    prect = climatology_params.get("PRECTOTCORR", {})
    t2m = climatology_params.get("T2M", {})
    rh2m = climatology_params.get("RH2M", {})

    # ALERTA 1: Risco de Chuvas Concentradas e Erosão na Reforma
    reform_pct = (reform_rain / annual_rain * 100) if annual_rain > 0 else 0
    if reform_pct > 65:
        alerts.append({
            "id": "alerta_erosao",
            "level": "Alerta Alto",
            "badge_color": "#F57C00",  # Laranja de atenção
            "icon": "🌧️",
            "title": "Alto Risco de Erosão na Janela de Reforma do Canavial",
            "summary": (
                f"{reform_pct:.1f}% das chuvas anuais ({reform_rain:.0f} mm) concentram-se "
                f"entre novembro e março. Deixar o solo descoberto (pousio convencional) "
                f"expõe a área à perda acelerada de nutrientes e solo fértil."
            ),
            "evidence": "NASA POWER Climatology (PRECTOTCORR) — série de 30 anos.",
            "scientific_basis": (
                "Estudos do IAC e Embrapa Meio Ambiente comprovam que a intensidade da chuva "
                "de verão no Estado de SP causa as maiores taxas anuais de perda por enxurrada."
            ),
            "recommendation": (
                "Priorizar culturas de rotação com rápido fechamento de dossel (Crotalária ou Soja) "
                "para amortecer o impacto cinético das gotas de chuva."
            ),
            "limitation": "A intensidade pontual de tempestades locais pode variar em relação à grade espacial de 0.5°."
        })
    else:
        alerts.append({
            "id": "alerta_erosao",
            "level": "Atenção Moderada",
            "badge_color": "#2E6FD8",
            "icon": "🌦️",
            "title": "Distribuição Pluvial Moderada na Reforma",
            "summary": f"Chuvas de verão totalizam {reform_rain:.0f} mm ({reform_pct:.1f}% do total anual).",
            "evidence": "NASA POWER Climatology (PRECTOTCORR)",
            "scientific_basis": "Modelos USLE de conservação de solo.",
            "recommendation": "Manter práticas conservacionistas de plantio em nível.",
            "limitation": "Resolução regional ~50 km."
        })

    # ALERTA 2: Veranico e Déficit Hídrico no Estabelecimento
    # Avalia os meses de Jan/Fev
    jan_rain = float(prect.get("JAN", 0.0)) * 31
    feb_rain = float(prect.get("FEB", 0.0)) * 28.25
    jan_temp = float(t2m.get("JAN", 24.0))

    if jan_temp > 24.0 and (jan_rain < 180 or feb_rain < 150):
        alerts.append({
            "id": "alerta_veranico",
            "level": "Atenção",
            "badge_color": "#F57C00",
            "icon": "☀️",
            "title": "Vulnerabilidade a Veranicos no Enchimento de Grãos / Estabelecimento",
            "summary": (
                f"Janeiro e fevereiro apresentam temperaturas médias elevadas ({jan_temp:.1f} °C) "
                f"e alta demanda evaporativa. Estiagens curtas (7 a 14 dias) nessa janela podem estressar "
                f"lavouras de soja ou amendoim na fase de floração/granação."
            ),
            "evidence": "NASA POWER Climatology (T2M e PRECTOTCORR)",
            "scientific_basis": "Zoneamento Agrícola de Risco Climático (ZARC / Mapa / Embrapa).",
            "recommendation": (
                "Em solos de menor retenção de umidade (textura média/arenosa), preferir cultivares "
                "com sistema radicular vigoroso ou adubos verdes resistentes à seca (Crotalaria juncea)."
            ),
            "limitation": "Veranicos são fenômenos sinóticos que exigem acompanhamento de previsão semanal."
        })
    else:
        alerts.append({
            "id": "alerta_veranico",
            "level": "Favorável",
            "badge_color": "#2E6FD8",
            "icon": "💧",
            "title": "Regime Hídrico Regular no Verão",
            "summary": "Balanço hídrico médio de verão suficiente para a maioria das culturas de rotação.",
            "evidence": "NASA POWER Climatology",
            "scientific_basis": "FAO 56 Balanço Hídrico.",
            "recommendation": "Monitorar a umidade de solo na semeadura.",
            "limitation": "Médias históricas não impedem veranicos esporádicos."
        })

    # ALERTA 3: Risco Térmico e de Geada
    if min_temp < 3.0:
        alerts.append({
            "id": "alerta_geada",
            "level": "Alerta de Frio",
            "badge_color": "#F57C00",
            "icon": "❄️",
            "title": "Histórico de Temperaturas Próximas ao Ponto de Geada",
            "summary": (
                f"A série histórica da NASA POWER registra mínimas de até {min_temp:.1f} °C em 2m. "
                f"Baixadas e vales podem atingir temperaturas inferiores a 0 °C em relva durante ondas polares."
            ),
            "evidence": "NASA POWER Climatology (T2M_MIN)",
            "scientific_basis": "Bioclimatologia da cana-de-açúcar (IAC).",
            "recommendation": "Evitar plantios tardios em áreas de baixada sujeitas a acúmulo de ar frio.",
            "limitation": "A resolução de 0.5° não detecta inversões térmicas microtopográficas de fundo de vale."
        })
    else:
        alerts.append({
            "id": "alerta_geada",
            "level": "Baixo Risco",
            "badge_color": "#0B3D91",
            "icon": "🌱",
            "title": "Risco Histórico Baixo de Geada Severa",
            "summary": (
                f"Mínima histórica média de {min_temp:.1f} °C na climatologia em 2m. "
                f"Ambiente térmico favorável para o desenvolvimento contínuo da cana e rotações de verão."
            ),
            "evidence": "NASA POWER Climatology (T2M_MIN)",
            "scientific_basis": "IAC Centro de Cana.",
            "recommendation": "Condições térmicas adequadas para o calendário padrão.",
            "limitation": "Fenômenos extremos raros requerem monitoramento meteorológico de inverno."
        })

    # ALERTA 4: Favorabilidade a Pragas (Cigarrinha e Broca da Cana)
    # Avalia calor e umidade nos meses de verão
    summer_rh = [float(rh2m.get(m, 70.0)) for m in ["DEC", "JAN", "FEB"]]
    avg_summer_rh = sum(summer_rh) / len(summer_rh)
    if avg_summer_rh > 75.0 and jan_temp > 23.0:
        alerts.append({
            "id": "alerta_pragas",
            "level": "Atenção Fitossanitária",
            "badge_color": "#F57C00",
            "icon": "🦗",
            "title": "Ambiente Climático Favorável à Cigarrinha e Broca da Cana",
            "summary": (
                f"Verão com alta umidade relativa média ({avg_summer_rh:.1f}%) e temperaturas elevadas "
                f"({jan_temp:.1f} °C) constituem o ambiente bioclimático ótimo para eclosão de ninfas "
                f"de cigarrinha-das-raízes (Mahanarva fimbriolata) e proliferação da broca (Diatraea saccharalis)."
            ),
            "evidence": "NASA POWER Climatology (T2M e RH2M) — meses de dezembro a fevereiro.",
            "scientific_basis": (
                "Modelos fenológicos do IAC e Embrapa Meio Ambiente para pragas canavieiras no Centro-Sul."
            ),
            "recommendation": (
                "A rotação de culturas quebra o ciclo de hospedeiros da gramínea. "
                "No canavial vizinho, intensificar vistorias de campo e amostragem na base dos colmos."
            ),
            "limitation": (
                "ATENÇÃO: Este alerta indica apenas favorabilidade climática regional. "
                "Ele NÃO indica presença da praga na fazenda. Vistoria in loco é indispensável."
            )
        })

    return alerts
