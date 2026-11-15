"""
Testes de Integração Ponta a Ponta (End-to-End Workflow)
SatAgro - NASA Space Apps Challenge 2026
"""

import unittest
from satagro.nasa_power import fetch_climatology, NasaPowerConnectionError, NasaPowerAPIError
from satagro.indicators import calculate_climatic_summary
from satagro.alerts import evaluate_agroclimatic_alerts
from satagro.rotation_engine import compute_rotation_rankings


class TestEndToEndWorkflow(unittest.TestCase):
    def test_complete_sertaozinho_pipeline(self):
        # 1. Coordenadas do Piloto
        lat, lon = -21.1378, -47.9897

        # 2. Coleta NASA POWER
        nasa_data = fetch_climatology(lat, lon, use_cache=True)
        self.assertIsNotNone(nasa_data)
        self.assertIn("parameters", nasa_data)
        self.assertIn("PRECTOTCORR", nasa_data["parameters"])
        self.assertIn("T2M", nasa_data["parameters"])

        # 3. Cálculo de Indicadores
        indicators = calculate_climatic_summary(nasa_data["parameters"], lat=lat)
        annual_rain = indicators["annual_precipitation"]["value"]
        annual_temp = indicators["annual_mean_temp"]["value"]
        self.assertGreater(annual_rain, 800.0)
        self.assertLess(annual_rain, 2500.0)
        self.assertGreater(annual_temp, 18.0)
        self.assertLess(annual_temp, 30.0)

        # 4. Avaliação de Alertas Agroclimáticos
        alerts = evaluate_agroclimatic_alerts(indicators, nasa_data["parameters"])
        self.assertGreaterEqual(len(alerts), 3)
        for alert in alerts:
            self.assertIn("title", alert)
            self.assertIn("summary", alert)
            self.assertIn("evidence", alert)
            self.assertIn("scientific_basis", alert)
            self.assertIn("recommendation", alert)
            self.assertIn("limitation", alert)

        # 5. Motor de Decisão com Prioridades Variadas
        # Cenário 1: Foco em Regeneração do Solo
        priorities_soil = {
            "protecao_solo": 5, "fixacao_nitrogenio": 5, "quebra_pragas": 4,
            "resiliencia_hidrica": 4, "renda_adicional": 1, "simplicidade_operacional": 2
        }
        rankings_soil = compute_rotation_rankings(priorities_soil, indicators)
        self.assertEqual(rankings_soil[0]["id"], "crotalaria")
        self.assertEqual(rankings_soil[0]["rank"], 1)

        # Cenário 2: Foco em Renda Imediata
        priorities_income = {
            "protecao_solo": 1, "fixacao_nitrogenio": 1, "quebra_pragas": 2,
            "resiliencia_hidrica": 2, "renda_adicional": 5, "simplicidade_operacional": 3
        }
        rankings_income = compute_rotation_rankings(priorities_income, indicators)
        top_income_ids = [rankings_income[0]["id"], rankings_income[1]["id"]]
        self.assertTrue("soja" in top_income_ids or "amendoim" in top_income_ids)

        # 6. Ficha Padronizada Completa
        for r in rankings_soil:
            self.assertTrue(len(r["why_suggested"]) > 10)
            self.assertTrue(len(r["benefits"]) > 10)
            self.assertTrue(len(r["risks"]) > 10)
            self.assertTrue(len(r["unknowns"]) > 10)
            self.assertTrue(len(r["evidence"]) > 10)
            self.assertTrue(any(c in r["confidence"] for c in ["Alta", "Média", "Baixa"]))
            self.assertTrue(len(r["specialist_review"]) > 10)

    def test_api_error_handling_invalid_coords(self):
        # Coordenadas fora da faixa geográfica mundial válida
        with self.assertRaises(Exception):
            fetch_climatology(lat=200.0, lon=500.0, use_cache=False)


if __name__ == "__main__":
    unittest.main()
