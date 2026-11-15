"""
Testes Unitários - Motor de Rotações e Ponderação Multicritério
"""

import unittest
from satagro.rotation_engine import compute_rotation_rankings
from satagro.agronomic_data import STRATEGIES_DATABASE


class TestRotationEngine(unittest.TestCase):
    def test_ranking_has_all_strategies(self):
        priorities = {
            "protecao_solo": 5,
            "fixacao_nitrogenio": 5,
            "quebra_pragas": 5,
            "resiliencia_hidrica": 5,
            "renda_adicional": 5,
            "simplicidade_operacional": 5,
        }
        rankings = compute_rotation_rankings(priorities, {})
        self.assertEqual(len(rankings), len(STRATEGIES_DATABASE))
        self.assertEqual(rankings[0]["rank"], 1)

    def test_prioritizing_soil_and_cover_favors_crotalaria(self):
        # Quando o produtor prioriza proteção e solo:
        priorities = {
            "protecao_solo": 5,
            "fixacao_nitrogenio": 5,
            "quebra_pragas": 5,
            "resiliencia_hidrica": 4,
            "renda_adicional": 1,
            "simplicidade_operacional": 1,
        }
        rankings = compute_rotation_rankings(priorities, {})
        top_strat = rankings[0]
        self.assertEqual(top_strat["id"], "crotalaria")

    def test_prioritizing_immediate_income_favors_commercial_crops(self):
        # Quando o produtor prioriza renda direta na entressafra:
        priorities = {
            "protecao_solo": 1,
            "fixacao_nitrogenio": 1,
            "quebra_pragas": 1,
            "resiliencia_hidrica": 1,
            "renda_adicional": 5,
            "simplicidade_operacional": 1,
        }
        rankings = compute_rotation_rankings(priorities, {})
        top_two = [r["id"] for r in rankings[:2]]
        self.assertTrue("soja" in top_two or "amendoim" in top_two)

    def test_climate_scenario_drought_impact(self):
        # Cenário seco (-30% chuva):
        priorities = {
            "protecao_solo": 3, "fixacao_nitrogenio": 3, "quebra_pragas": 3,
            "resiliencia_hidrica": 5, "renda_adicional": 3, "simplicidade_operacional": 3
        }
        baseline = compute_rotation_rankings(priorities, {}, {"rain_delta_pct": 0, "temp_delta_c": 0})
        dry = compute_rotation_rankings(priorities, {}, {"rain_delta_pct": -30, "temp_delta_c": 2.0})

        # Crotalária deve manter maior estabilidade do que soja
        soja_base = next(r for r in baseline if r["id"] == "soja")["final_score"]
        soja_dry = next(r for r in dry if r["id"] == "soja")["final_score"]
        self.assertLess(soja_dry, soja_base)


if __name__ == "__main__":
    unittest.main()
