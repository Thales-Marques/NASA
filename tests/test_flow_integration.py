"""
Testes de Integração Ponta a Ponta (Fluxo Completo Atualizado)
SatAgro - NASA Space Apps Challenge 2026
"""

import unittest
from satagro.nasa_power import (
    fetch_climatology,
    load_verified_pilot_dataset,
    validate_nasa_climatology_response
)
from satagro.indicators import calculate_climatic_summary
from satagro.alerts import evaluate_agroclimatic_signals
from satagro.rotation_engine import compute_rotation_rankings


class TestEndToEndWorkflow(unittest.TestCase):
    def test_complete_sertaozinho_pipeline(self):
        # 1. Conjunto Verificado do Piloto
        pilot_data = load_verified_pilot_dataset()
        self.assertIsNotNone(pilot_data)
        self.assertTrue(pilot_data["is_verified_pilot"])
        self.assertIn("parameters", pilot_data)
        self.assertIn("metadata", pilot_data)

        # 2. Metadados Extraídos Dinamicamente
        meta = pilot_data["metadata"]
        self.assertIn("2001", meta["climatology_range"])
        self.assertIn("2025", meta["climatology_range"])
        self.assertIn("MERRA2", meta["sources"])

        # 3. Cálculo de Indicadores
        indicators = calculate_climatic_summary(pilot_data["parameters"], metadata=meta)
        annual_rain = indicators["annual_precipitation"]["value"]
        annual_temp = indicators["annual_mean_temp"]["value"]
        self.assertAlmostEqual(annual_rain, 1271.5, places=0)
        self.assertAlmostEqual(annual_temp, 23.5, delta=1.0)
        self.assertNotIn("annual_et0", indicators)  # P0.5

        # 4. Avaliação de Sinais Climatológicos Exploratórios
        signals = evaluate_agroclimatic_signals(indicators, pilot_data["parameters"], metadata=meta)
        self.assertEqual(len(signals), 4)
        for sig in signals:
            self.assertIn("title", sig)
            self.assertIn("observation", sig)
            self.assertIn("what_it_is_not", sig)
            self.assertIn("literature_reference", sig)
            self.assertIn("limitation", sig)

        # 5. Motor Heurístico com Prioridades
        priorities_soil = {
            "protecao_solo": 5, "fixacao_nitrogenio": 5, "quebra_pragas": 4,
            "resiliencia_hidrica": 4, "renda_adicional": 1, "simplicidade_operacional": 2
        }
        rankings = compute_rotation_rankings(priorities_soil, indicators)
        self.assertEqual(rankings[0]["id"], "crotalaria")
        self.assertEqual(rankings[0]["rank"], 1)

        # 6. Ficha com 4 Camadas Explícitas (P0.6)
        for r in rankings:
            self.assertTrue(len(r["nasa_observational_data"]) > 15)
            self.assertTrue(len(r["derived_indicators"]) > 15)
            self.assertTrue(len(r["technical_literature"]) > 15)
            self.assertTrue(len(r["heuristic_scoring_explanation"]) > 15)
            self.assertIn("Qualitativa / Heurística", r["confidence"])
            self.assertTrue(len(r["specialist_review"]) > 15)


if __name__ == "__main__":
    unittest.main()
