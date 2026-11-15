"""
SatAgro - Indicadores Climáticos e Agroambientais
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Módulo responsável pelo cálculo de indicadores agronômicos verificáveis a partir
dos dados da NASA POWER, com metodologia, unidades e referências documentadas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS_IN_MONTH = {
    "JAN": 31, "FEB": 28.25, "MAR": 31, "APR": 30, "MAY": 31, "JUN": 30,
    "JUL": 31, "AUG": 31, "SEP": 30, "OCT": 31, "NOV": 30, "DEC": 31
}
MONTH_NAMES_PT = {
    "JAN": "Janeiro", "FEB": "Fevereiro", "MAR": "Março", "APR": "Abril",
    "MAY": "Maio", "JUN": "Junho", "JUL": "Julho", "AUG": "Agosto",
    "SEP": "Setembro", "OCT": "Outubro", "NOV": "Novembro", "DEC": "Dezembro"
}


def compute_monthly_rainfall(prectotcorr_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Converte a taxa média de precipitação diária da NASA POWER (mm/dia)
    no acumulado total médio mensal (mm/mês).
    """
    monthly_mm = {}
    for m in MONTHS:
        rate = float(prectotcorr_dict.get(m, 0.0))
        monthly_mm[m] = round(rate * DAYS_IN_MONTH[m], 1)
    return monthly_mm


def calculate_climatic_summary(parameters: Dict[str, Any], lat: float = -21.14) -> Dict[str, Any]:
    """
    Calcula os principais indicadores climáticos e agroambientais
    com base nas séries climatológicas de 30 anos da NASA POWER.
    """
    prect = parameters.get("PRECTOTCORR", {})
    t2m = parameters.get("T2M", {})
    t2m_max = parameters.get("T2M_MAX", {})
    t2m_min = parameters.get("T2M_MIN", {})
    rh2m = parameters.get("RH2M", {})
    rad_solar = parameters.get("ALLSKY_SFC_SW_DWN", {})

    # 1. Chuva Mensal e Anual (mm)
    monthly_rain = compute_monthly_rainfall(prect)
    annual_rain = round(sum(monthly_rain.values()), 1)

    # 2. Divisão Sazonal (Período Chuvoso vs Período Seco)
    # No Centro-Sul brasileiro: Chuvoso = Out a Mar; Seco = Abr a Set
    wet_months = ["OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]
    dry_months = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP"]

    wet_rain = round(sum(monthly_rain[m] for m in wet_months), 1)
    dry_rain = round(sum(monthly_rain[m] for m in dry_months), 1)
    dry_ratio = round((dry_rain / annual_rain * 100) if annual_rain > 0 else 0, 1)

    # 3. Chuva na Janela Típica de Reforma do Canavial (Novembro a Março)
    reform_months = ["NOV", "DEC", "JAN", "FEB", "MAR"]
    reform_rain = round(sum(monthly_rain[m] for m in reform_months), 1)
    reform_ratio = round((reform_rain / annual_rain * 100) if annual_rain > 0 else 0, 1)

    # 4. Temperaturas Médias, Máximas e Mínimas
    monthly_tmean = {m: float(t2m.get(m, 0.0)) for m in MONTHS}
    monthly_tmax = {m: float(t2m_max.get(m, 0.0)) for m in MONTHS}
    monthly_tmin = {m: float(t2m_min.get(m, 0.0)) for m in MONTHS}

    annual_tmean = round(sum(monthly_tmean.values()) / 12, 1)
    hottest_month = max(monthly_tmean, key=monthly_tmean.get)
    coldest_month = min(monthly_tmean, key=monthly_tmean.get)

    max_recorded_temp = max(monthly_tmax.values())
    min_recorded_temp = min(monthly_tmin.values())

    # 5. Estimativa de Evapotranspiração de Referência (ET0) - Método Hargreaves simplificado / Radiação
    # ET0 (mm/dia) aprox = 0.0135 * (Rs / 2.45) * (Tmean + 17.8) (adaptado de Turc/Hargreaves com radiação NASA)
    monthly_et0 = {}
    for m in MONTHS:
        rs = float(rad_solar.get(m, 18.0))  # MJ/m²/dia
        tm = monthly_tmean[m]
        # Calor latente de vaporização lambda ~ 2.45 MJ/kg
        daily_et0 = max(0.5, 0.0135 * (rs / 2.45) * (tm + 17.8))
        monthly_et0[m] = round(daily_et0 * DAYS_IN_MONTH[m], 1)
    annual_et0 = round(sum(monthly_et0.values()), 1)

    # 6. Balanço Hídrico Climatológico Simplificado (P - ET0)
    monthly_water_balance = {m: round(monthly_rain[m] - monthly_et0[m], 1) for m in MONTHS}
    annual_water_deficit_months = [m for m in MONTHS if monthly_water_balance[m] < 0]

    # Estruturação final com rastreabilidade científica
    indicators = {
        "annual_precipitation": {
            "name": "Precipitação Média Anual",
            "value": annual_rain,
            "unit": "mm/ano",
            "methodology": "Soma dos acumulados mensais derivados da taxa média diária (PRECTOTCORR × dias do mês)",
            "source": "NASA POWER Climatology (1991–2020), Resolução ~0.5°",
            "confidence": "Alta",
            "interpretation": f"Precipitação anual de {annual_rain} mm. Adequada para cana-de-açúcar (exigência hídrica de 1.100 a 1.500 mm/ano)."
        },
        "seasonal_dry_ratio": {
            "name": "Concentração da Estiagem (Abr–Set)",
            "value": dry_ratio,
            "unit": "% do total anual",
            "methodology": "Razão entre chuva acumulada no período seco (abril a setembro) e chuva anual total",
            "source": "NASA POWER Climatology",
            "confidence": "Alta",
            "interpretation": f"Apenas {dry_ratio}% das chuvas ocorrem entre abril e setembro ({dry_rain} mm), caracterizando estação seca pronunciada."
        },
        "reform_window_rain": {
            "name": "Chuva na Janela de Reforma (Nov–Mar)",
            "value": reform_rain,
            "unit": "mm",
            "methodology": "Chuva acumulada média entre novembro e março (meses típicos de preparo de solo, dessecação e rotação)",
            "source": "NASA POWER Climatology",
            "confidence": "Alta",
            "interpretation": f"{reform_ratio}% da chuva anual ({reform_rain} mm) cai durante a janela de reforma, elevando o risco de erosão em solos descobertos."
        },
        "annual_mean_temp": {
            "name": "Temperatura Média Anual",
            "value": annual_tmean,
            "unit": "°C",
            "methodology": "Média aritmética das médias mensais T2M da série de 30 anos",
            "source": "NASA POWER Climatology",
            "confidence": "Alta",
            "interpretation": f"Média térmica de {annual_tmean} °C. Ótimo fisiológico da cana e das culturas de rotação (soja, amendoim, crotalária)."
        },
        "frost_risk_minimum": {
            "name": "Temperatura Mínima Histórica Absoluta",
            "value": min_recorded_temp,
            "unit": "°C",
            "methodology": "Menor valor de T2M_MIN registrado na climatologia",
            "source": "NASA POWER Climatology",
            "confidence": "Média (~0.5° suaviza microclimas em baixadas)",
            "interpretation": (
                "Risco Baixo de geada severa na série de satélite (> 3°C), "
                "porém baixadas locais podem registrar temperaturas inferiores."
                if min_recorded_temp > 3.0 else
                "Atenção: Mínimas históricas inferiores a 3°C apontam risco potencial de geada de relva em invernos rigorosos."
            )
        },
        "annual_et0": {
            "name": "Evapotranspiração de Referência (ET0)",
            "value": annual_et0,
            "unit": "mm/ano",
            "methodology": "Estimativa combinada radiação-temperatura (Turc/Hargreaves adaptada com radiação global da NASA POWER)",
            "source": "NASA POWER (T2M + ALLSKY_SFC_SW_DWN)",
            "confidence": "Média (estimativa baseada em radiação por satélite)",
            "interpretation": f"Demanda evaporativa atmosférica anual estimada em {annual_et0} mm/ano."
        },
        "raw_monthly_data": {
            "months": MONTHS,
            "months_pt": [MONTH_NAMES_PT[m] for m in MONTHS],
            "rainfall_mm": [monthly_rain[m] for m in MONTHS],
            "tmean_c": [monthly_tmean[m] for m in MONTHS],
            "tmax_c": [monthly_tmax[m] for m in MONTHS],
            "tmin_c": [monthly_tmin[m] for m in MONTHS],
            "rh2m_pct": [round(float(rh2m.get(m, 0.0)), 1) for m in MONTHS],
            "et0_mm": [monthly_et0[m] for m in MONTHS],
            "water_balance_mm": [monthly_water_balance[m] for m in MONTHS],
        }
    }

    return indicators
