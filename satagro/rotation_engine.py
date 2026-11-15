"""
SatAgro - Motor de Comparação e Apoio à Decisão de Rotações
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Implementa o algoritmo de ponderação multicritério (MCDA), sensibilidade a cenários
climáticos e geração de fichas explicativas padronizadas para cada estratégia.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from satagro.agronomic_data import STRATEGIES_DATABASE, CRITERIA_METADATA


def compute_rotation_rankings(
    producer_priorities: Dict[str, float],
    climatic_indicators: Dict[str, Any],
    climate_scenario: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """
    Calcula a pontuação de cada estratégia de reforma do canavial
    ponderada pelas prioridades do produtor e ajustada pelo cenário climático.
    
    producer_priorities: dicionário {criterio: peso_1_a_5}
    climate_scenario: {
        'rain_delta_pct': float (-30.0 a +30.0),
        'temp_delta_c': float (-1.0 a +3.0)
    }
    """
    if climate_scenario is None:
        climate_scenario = {"rain_delta_pct": 0.0, "temp_delta_c": 0.0}

    rain_delta = climate_scenario.get("rain_delta_pct", 0.0)
    temp_delta = climate_scenario.get("temp_delta_c", 0.0)

    # 1. Normalização dos pesos das prioridades do produtor (Soma = 1.0)
    criteria_keys = list(CRITERIA_METADATA.keys())
    raw_weights = {k: max(0.1, float(producer_priorities.get(k, 3.0))) for k in criteria_keys}
    total_weight = sum(raw_weights.values())
    normalized_weights = {k: raw_weights[k] / total_weight for k in criteria_keys}

    # 2. Avaliação de cada estratégia
    results = []

    for strat_id, strat in STRATEGIES_DATABASE.items():
        base_scores = strat["scores"].copy()
        adjusted_scores = {}

        # Ajuste dinâmico de sensibilidade ao cenário climático:
        # Se cenário prevê redução de chuva ou aumento de temperatura:
        # - Culturas sensíveis a estresse hídrico (soja, amendoim) sofrem penalidade na resiliência
        # - Crotalária mantém ou amplia vantagem relativa de proteção e tolerância
        # - Solo descoberto (prática atual) sofre maior penalidade em proteção se chuva aumentar
        for crit, score in base_scores.items():
            adj_score = score

            if crit == "resiliencia_hidrica":
                if rain_delta < 0:  # Cenário mais seco
                    if strat_id in ["soja", "amendoim"]:
                        # Perda de pontuação proporcional ao déficit
                        adj_score = max(0.1, score * (1.0 + (rain_delta / 100.0) * 0.8))
                    elif strat_id == "crotalaria":
                        # Crotalária possui sistema radicular pivotante profundo
                        adj_score = max(0.3, score * (1.0 + (rain_delta / 100.0) * 0.2))
                    elif strat_id == "atual":
                        adj_score = max(0.1, score * (1.0 + (rain_delta / 100.0) * 0.5))

            if crit == "protecao_solo":
                if rain_delta > 0:  # Cenário de chuvas mais intensas
                    if strat_id == "atual":
                        # Solo exposto sob chuvas mais fortes perde ainda mais solo
                        adj_score = max(0.05, score * (1.0 - (rain_delta / 100.0) * 0.5))
                    elif strat_id == "crotalaria":
                        adj_score = min(1.0, score * 1.02)

            adjusted_scores[crit] = round(adj_score, 3)

        # 3. Cálculo da pontuação composta ponderada (0 a 100)
        final_score = 0.0
        contributions = {}
        for crit in criteria_keys:
            w = normalized_weights[crit]
            s = adjusted_scores[crit]
            contrib = w * s * 100.0
            contributions[crit] = round(contrib, 1)
            final_score += contrib

        final_score = round(final_score, 1)

        # 4. Montagem da ficha padronizada explicativa
        results.append({
            "id": strat_id,
            "name": strat["name"],
            "crop_type": strat["crop_type"],
            "cycle_days": strat["cycle_days"],
            "final_score": final_score,
            "adjusted_scores": adjusted_scores,
            "criteria_contributions": contributions,
            "normalized_weights": {k: round(v, 3) for k, v in normalized_weights.items()},
            # Ficha Padronizada
            "why_suggested": strat["why_suggested"],
            "evidence": strat["evidence"],
            "benefits": strat["benefits"],
            "unknowns": strat["unknowns"],
            "risks": strat["risks"],
            "confidence": strat["confidence"],
            "specialist_review": strat["specialist_review"],
        })

    # 5. Ordenação decrescente por nota final
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # Atribuir posições no ranking
    for idx, item in enumerate(results, start=1):
        item["rank"] = idx

    return results
