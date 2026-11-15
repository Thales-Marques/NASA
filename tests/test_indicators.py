"""
Testes Unitários - Indicadores Climatológicos Regionais e Sinais Exploratórios
Conforme P0.5: Sem ET0 experimental e sem inferência de riscos reais sem dados locais.
"""

import unittest
from satagro.indicators import calculate_climatic_summary, compute_monthly_rainfall
from satagro.alerts import evaluate_agroclimatic_signals


class TestIndicators(unittest.TestCase):
    def setUp(self):
        # Parâmetros simulados completos e consistentes (sem sentinelas)
        self.mock_params = {
            "PRECTOTCORR": {
                "JAN": 8.0, "FEB": 6.5, "MAR": 5.0, "APR": 2.2, "MAY": 1.7, "JUN": 0.7,
                "JUL": 0.5, "AUG": 0.6, "SEP": 1.6, "OCT": 3.2, "NOV": 5.5, "DEC": 6.7
            },
            "T2M": {
                "JAN": 24.5, "FEB": 24.5, "MAR": 23.9, "APR": 23.0, "MAY": 20.6, "JUN": 20.3,
                "JUL": 20.7, "AUG": 22.9, "SEP": 25.5, "OCT": 26.2, "NOV": 25.1, "DEC": 24.6
            },
            "T2M_MAX": {m: 32.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
            "T2M_MIN": {
                "JAN": 18.0, "FEB": 18.0, "MAR": 17.0, "APR": 14.0, "MAY": 10.0, "JUN": 8.0,
                "JUL": 7.5, "AUG": 8.5, "SEP": 11.0, "OCT": 14.5, "NOV": 16.0, "DEC": 17.5
            },
            "RH2M": {m: 78.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
        }
        self.mock_metadata = {
            "climatology_range": "25-year (January 2001 - December 2025)"
        }

    def test_rainfall_aggregation(self):
        monthly = compute_monthly_rainfall(self.mock_params["PRECTOTCORR"])
        self.assertEqual(len(monthly), 12)
        # Jan: 8.0 mm/day * 31 dias = 248.0 mm
        self.assertAlmostEqual(monthly["JAN"], 248.0, places=1)

    def test_summary_indicators_no_experimental_et0(self):
        summary = calculate_climatic_summary(self.mock_params, metadata=self.mock_metadata)
        
        # P0.5: ET0 não deve estar presente nos indicadores
        self.assertNotIn("annual_et0", summary)

        self.assertIn("annual_precipitation", summary)
        self.assertGreater(summary["annual_precipitation"]["value"], 1000)
        self.assertEqual(summary["annual_precipitation"]["unit"], "mm/ano")

        self.assertIn("seasonal_dry_ratio", summary)
        self.assertGreater(summary["seasonal_dry_ratio"]["value"], 0)
        self.assertLess(summary["seasonal_dry_ratio"]["value"], 50)

        self.assertIn("reform_window_rain", summary)
        self.assertGreater(summary["reform_window_rain"]["value"], 500)

        self.assertIn("annual_mean_temp", summary)
        self.assertAlmostEqual(summary["annual_mean_temp"]["value"], 23.5, delta=1.0)

        self.assertIn("thermal_extremes", summary)
        self.assertEqual(summary["thermal_extremes"]["min_value"], 7.5)

    def test_exploratory_signals_generation(self):
        summary = calculate_climatic_summary(self.mock_params, metadata=self.mock_metadata)
        signals = evaluate_agroclimatic_signals(summary, self.mock_params, metadata=self.mock_metadata)
        self.assertEqual(len(signals), 4)
        
        signal_ids = [s["id"] for s in signals]
        self.assertIn("sinal_concentracao_chuva", signal_ids)
        self.assertIn("sinal_sazonalidade_inverno", signal_ids)
        self.assertIn("sinal_termico_geada", signal_ids)
        self.assertIn("sinal_bioclimatico_pragas", signal_ids)

        # Verificar presença de ressalvas obrigatórias (P0.5)
        for s in signals:
            self.assertIn("what_it_is_not", s)
            self.assertIn("limitation", s)
            self.assertTrue(len(s["what_it_is_not"]) > 20)


if __name__ == "__main__":
    unittest.main()
