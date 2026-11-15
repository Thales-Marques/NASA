"""
Testes Unitários - Motor Heurístico Multicritério (MCDA)
Conforme P0.1 e P0.2:
- Avaliação heurística transparente baseada exclusivamente nas prioridades do produtor.
- Ausência de controles climáticos inertes.
- Explicação matemática dinâmica da nota.
"""

import unittest
from satagro.rotation_engine import compute_rotation_rankings
from satagro.agronomic_data import STRATEGIES_DATABASE


class TestRotationEngine(unittest.TestCase):
    def test_ranking_structure_and_completeness(self):
        priorities = {
            "protecao_solo": 5, "fixacao_nitrogenio": 4, "quebra_pragas": 4,
            "resiliencia_hidrica": 3, "renda_adicional": 2, "simplicidade_operacional": 2,
        }
        rankings = compute_rotation_rankings(priorities)
        self.assertEqual(len(rankings), len(STRATEGIES_DATABASE))
        self.assertEqual(rankings[0]["rank"], 1)

        # Checar 4 camadas de explicabilidade por estratégia (P0.6)
        for r in rankings:
            self.assertIn("nasa_observational_data", r)
            self.assertIn("derived_indicators", r)
            self.assertIn("technical_literature", r)
            self.assertIn("heuristic_scoring_explanation", r)
            self.assertIn("criteria_contributions", r)
            self.assertIn("normalized_weights", r)
            # A soma das contribuições deve equivaler à nota final
            contrib_sum = sum(r["criteria_contributions"].values())
            self.assertAlmostEqual(r["final_score"], contrib_sum, delta=0.1)

    def test_prioritizing_soil_and_cover_favors_crotalaria(self):
        # Quando o produtor prioriza proteção e cobertura:
        priorities = {
            "protecao_solo": 5, "fixacao_nitrogenio": 5, "quebra_pragas": 5,
            "resiliencia_hidrica": 4, "renda_adicional": 1, "simplicidade_operacional": 1,
        }
        rankings = compute_rotation_rankings(priorities)
        top_strat = rankings[0]
        self.assertEqual(top_strat["id"], "crotalaria")

    def test_prioritizing_immediate_income_favors_commercial_crops(self):
        # Quando o produtor prioriza renda direta na entressafra:
        priorities = {
            "protecao_solo": 1, "fixacao_nitrogenio": 1, "quebra_pragas": 1,
            "resiliencia_hidrica": 1, "renda_adicional": 5, "simplicidade_operacional": 1,
        }
        rankings = compute_rotation_rankings(priorities)
        top_two = [r["id"] for r in rankings[:2]]
        self.assertTrue("soja" in top_two or "amendoim" in top_two)

    def test_prioritizing_simplicity_boosts_baseline_practice(self):
        # Quando o produtor aumenta a prioridade de simplicidade operacional, a nota da prática atual sobe significativamente
        p_low_ops = {
            "protecao_solo": 4, "fixacao_nitrogenio": 4, "quebra_pragas": 4,
            "resiliencia_hidrica": 4, "renda_adicional": 4, "simplicidade_operacional": 1,
        }
        p_high_ops = {
            "protecao_solo": 1, "fixacao_nitrogenio": 1, "quebra_pragas": 1,
            "resiliencia_hidrica": 1, "renda_adicional": 1, "simplicidade_operacional": 5,
        }
        score_low = next(r for r in compute_rotation_rankings(p_low_ops) if r["id"] == "atual")["final_score"]
        score_high = next(r for r in compute_rotation_rankings(p_high_ops) if r["id"] == "atual")["final_score"]
        self.assertGreater(score_high, score_low)


if __name__ == "__main__":
    unittest.main()
