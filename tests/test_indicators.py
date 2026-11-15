"""
Testes Unitários - Indicadores Agroclimáticos e Alertas
"""

import unittest
from satagro.indicators import calculate_climatic_summary, compute_monthly_rainfall
from satagro.alerts import evaluate_agroclimatic_alerts


class TestIndicators(unittest.TestCase):
    def setUp(self):
        # Parâmetros simulados consistentes com Sertãozinho (SP)
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
            "ALLSKY_SFC_SW_DWN": {m: 20.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]}
        }

    def test_rainfall_aggregation(self):
        monthly = compute_monthly_rainfall(self.mock_params["PRECTOTCORR"])
        self.assertEqual(len(monthly), 12)
        # Jan: 8.0 * 31 = 248.0 mm
        self.assertAlmostEqual(monthly["JAN"], 248.0, places=1)

    def test_summary_indicators(self):
        summary = calculate_climatic_summary(self.mock_params, lat=-21.14)
        
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

    def test_alerts_generation(self):
        summary = calculate_climatic_summary(self.mock_params, lat=-21.14)
        alerts = evaluate_agroclimatic_alerts(summary, self.mock_params)
        self.assertGreaterEqual(len(alerts), 3)
        alert_ids = [a["id"] for a in alerts]
        self.assertIn("alerta_erosao", alert_ids)
        self.assertIn("alerta_pragas", alert_ids)


if __name__ == "__main__":
    unittest.main()
