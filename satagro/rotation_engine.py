"""
SatAgro - Motor de Ordenação Heurística Multicritério (MCDA)
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Conforme P0.1 e P0.2:
- Implementa ordenação heurística transparente baseada exclusivamente nos pesos informados pelo produtor
  e nas notas teóricas de referência da literatura agronômica.
- Não inventa relações fictícias entre dados de satélite e notas agronômicas.
- Não atribui pontuações à NASA.
- Detalha matematicamente a contribuição de cada critério no resultado final.
"""

from __future__ import annotations

from typing import Any, Dict, List
from satagro.agronomic_data import STRATEGIES_DATABASE, CRITERIA_METADATA


def compute_rotation_rankings(
    producer_priorities: Dict[str, float],
    indicators: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    P0.1 - Calcula a pontuação heurística ilustrativa de cada estratégia de reforma
    ponderada exclusivamente pelas prioridades do produtor.
    
    Fórmula transparente (MCDA Ponderado):
    S_j = sum(w_i * s_ij) * 100
    onde sum(w_i) = 1.0 e 0 <= s_ij <= 1.0
    """
    criteria_keys = list(CRITERIA_METADATA.keys())

    # 1. Normalização dos pesos fornecidos pelo produtor (Soma = 1.0)
    raw_weights = {k: max(0.1, float(producer_priorities.get(k, 3.0))) for k in criteria_keys}
    total_raw_weight = sum(raw_weights.values())
    normalized_weights = {k: round(raw_weights[k] / total_raw_weight, 4) for k in criteria_keys}

    results = []

    for strat_id, strat in STRATEGIES_DATABASE.items():
        ref_scores = strat["reference_scores"]
        contributions = {}
        final_score = 0.0

        for crit in criteria_keys:
            w = normalized_weights[crit]
            s = ref_scores[crit]
            contrib = w * s * 100.0
            contributions[crit] = round(contrib, 2)
            final_score += contrib

        final_score = round(final_score, 1)

        results.append({
            "id": strat_id,
            "name": strat["name"],
            "crop_type": strat["crop_type"],
            "cycle_days": strat["cycle_days"],
            "final_score": final_score,
            "reference_scores": ref_scores,
            "criteria_contributions": contributions,
            "raw_user_weights": raw_weights,
            "normalized_weights": normalized_weights,
            # 4 Camadas de Explicabilidade (P0.6)
            "nasa_observational_data": strat["nasa_observational_data"],
            "derived_indicators": strat["derived_indicators"],
            "technical_literature": strat["technical_literature"],
            "heuristic_scoring_explanation": strat["heuristic_scoring_explanation"],
            "unknowns": strat["unknowns"],
            "confidence": strat["confidence"],
            "specialist_review": strat["specialist_review"],
        })

    # Ordenação decrescente por nota final
    results.sort(key=lambda x: x["final_score"], reverse=True)

    for idx, item in enumerate(results, start=1):
        item["rank"] = idx

    return results
