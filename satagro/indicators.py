"""
SatAgro - Indicadores Climatológicos Regionais
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Módulo responsável pelo cálculo de indicadores climatológicos verificáveis a partir
das séries históricas validadas da NASA POWER (MERRA-2).
Conforme P0.5: Não inclui ET0 experimental nem balanços hídricos de solo não verificados.
"""

from __future__ import annotations

from typing import Any, Dict, List

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
    Requer que todos os 12 meses estejam validados.
    """
    monthly_mm = {}
    for m in MONTHS:
        rate = float(prectotcorr_dict[m])
        monthly_mm[m] = round(rate * DAYS_IN_MONTH[m], 1)
    return monthly_mm


def calculate_climatic_summary(parameters: Dict[str, Any], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Calcula indicadores climatológicos históricos transparentes a partir dos parâmetros
    validados da NASA POWER.
    
    Indicadores gerados:
    1. Precipitação total média anual (mm/ano)
    2. Sazonalidade: acumulado no período chuvoso (Out–Mar) e seco (Abr–Set)
    3. Acumulado histórico na janela típica de reforma do canavial (Nov–Mar)
    4. Perfil térmico anual: temperatura média, máxima e mínima históricas
    """
    if metadata is None:
        metadata = {}

    prect = parameters["PRECTOTCORR"]
    t2m = parameters["T2M"]
    t2m_max = parameters["T2M_MAX"]
    t2m_min = parameters["T2M_MIN"]
    rh2m = parameters.get("RH2M", {})

    climatology_range = metadata.get("climatology_range", "2001–2025")

    # 1. Acumulado Mensal e Anual de Chuva
    monthly_rain = compute_monthly_rainfall(prect)
    annual_rain = round(sum(monthly_rain.values()), 1)

    # 2. Divisão Sazonal (Período Chuvoso vs Seco no Centro-Sul)
    wet_months = ["OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]
    dry_months = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP"]
    wet_rain = round(sum(monthly_rain[m] for m in wet_months), 1)
    dry_rain = round(sum(monthly_rain[m] for m in dry_months), 1)
    dry_ratio = round((dry_rain / annual_rain * 100) if annual_rain > 0 else 0, 1)
    wet_ratio = round((wet_rain / annual_rain * 100) if annual_rain > 0 else 0, 1)

    # 3. Chuva na Janela Típica de Reforma do Canavial (Novembro a Março)
    reform_months = ["NOV", "DEC", "JAN", "FEB", "MAR"]
    reform_rain = round(sum(monthly_rain[m] for m in reform_months), 1)
    reform_ratio = round((reform_rain / annual_rain * 100) if annual_rain > 0 else 0, 1)

    # 4. Perfil Térmico
    monthly_tmean = {m: round(float(t2m[m]), 1) for m in MONTHS}
    monthly_tmax = {m: round(float(t2m_max[m]), 1) for m in MONTHS}
    monthly_tmin = {m: round(float(t2m_min[m]), 1) for m in MONTHS}

    annual_tmean = round(sum(monthly_tmean.values()) / 12, 1)
    hottest_month = max(monthly_tmean, key=monthly_tmean.get)
    coldest_month = min(monthly_tmean, key=monthly_tmean.get)
    max_recorded_temp = max(monthly_tmax.values())
    min_recorded_temp = min(monthly_tmin.values())

    return {
        "annual_precipitation": {
            "name": "Precipitação Média Anual",
            "value": annual_rain,
            "unit": "mm/ano",
            "methodology": f"Soma dos acumulados mensais derivados da taxa diária PRECTOTCORR da série {climatology_range}",
            "source": f"NASA POWER / GMAO MERRA-2 ({climatology_range})",
            "confidence": "Alta na escala regional (~0,5°)",
            "interpretation": f"Precipitação histórica anual de {annual_rain} mm na grade regional."
        },
        "seasonal_dry_ratio": {
            "name": "Concentração da Estiagem (Abr–Set)",
            "value": dry_ratio,
            "unit": "% do total anual",
            "methodology": "Razão entre o acumulado histórico do período seco (abril a setembro) e o total anual",
            "source": f"NASA POWER / GMAO MERRA-2 ({climatology_range})",
            "confidence": "Alta na escala regional",
            "interpretation": f"Apenas {dry_ratio}% da chuva ({dry_rain} mm) ocorre entre abril e setembro, confirmando estação seca de inverno marcante."
        },
        "reform_window_rain": {
            "name": "Chuva na Janela de Reforma (Nov–Mar)",
            "value": reform_rain,
            "unit": "mm (Nov–Mar)",
            "methodology": "Acumulado médio da série histórica nos meses típicos de reforma (novembro a março)",
            "source": f"NASA POWER / GMAO MERRA-2 ({climatology_range})",
            "confidence": "Alta na escala regional",
            "interpretation": f"{reform_ratio}% da precipitação anual ({reform_rain} mm) concentra-se nos 5 meses da janela de reforma."
        },
        "annual_mean_temp": {
            "name": "Temperatura Média Anual",
            "value": annual_tmean,
            "unit": "°C",
            "methodology": "Média das temperaturas médias mensais a 2m (T2M)",
            "source": f"NASA POWER / GMAO MERRA-2 ({climatology_range})",
            "confidence": "Alta na escala regional",
            "interpretation": f"Média térmica regional de {annual_tmean} °C (mês mais quente: {MONTH_NAMES_PT[hottest_month]} com {monthly_tmean[hottest_month]} °C; mais frio: {MONTH_NAMES_PT[coldest_month]} com {monthly_tmean[coldest_month]} °C)."
        },
        "thermal_extremes": {
            "name": "Extremos Médios de Temperatura",
            "max_value": max_recorded_temp,
            "min_value": min_recorded_temp,
            "unit": "°C",
            "methodology": "Máxima de T2M_MAX e mínima de T2M_MIN na série climatológica mensal",
            "source": f"NASA POWER / GMAO MERRA-2 ({climatology_range})",
            "confidence": "Média (grade de ~0,5° suaviza extremos locais e inversões em baixadas)",
            "interpretation": f"Máxima média climatológica de {max_recorded_temp} °C e mínima média de {min_recorded_temp} °C na grade regional."
        },
        "raw_monthly_data": {
            "months": MONTHS,
            "months_pt": [MONTH_NAMES_PT[m] for m in MONTHS],
            "rainfall_mm": [monthly_rain[m] for m in MONTHS],
            "tmean_c": [monthly_tmean[m] for m in MONTHS],
            "tmax_c": [monthly_tmax[m] for m in MONTHS],
            "tmin_c": [monthly_tmin[m] for m in MONTHS],
            "rh2m_pct": [round(float(rh2m[m]), 1) for m in MONTHS] if rh2m else [],
        }
    }
