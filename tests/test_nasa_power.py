"""
Testes Unitários - Integração NASA POWER e Validação
"""

import os
import unittest
from satagro.nasa_power import (
    fetch_climatology,
    load_verified_pilot_dataset,
    validate_nasa_climatology_response,
    CACHE_DIR
)


class TestNasaPower(unittest.TestCase):
    def test_load_verified_pilot(self):
        data = load_verified_pilot_dataset()
        self.assertTrue(data["is_verified_pilot"])
        self.assertIn("parameters", data)
        self.assertIn("PRECTOTCORR", data["parameters"])
        self.assertIn("T2M", data["parameters"])
        self.assertIn("metadata", data)
        self.assertIn("climatology_range", data["metadata"])

    def test_fetch_climatology_sertaozinho(self):
        lat, lon = -21.1378, -47.9897
        data = fetch_climatology(lat, lon, use_cache=True)
        self.assertIn("parameters", data)
        self.assertIn("collected_at", data)
        self.assertEqual(data["latitude"], round(lat, 4))
        self.assertEqual(data["longitude"], round(lon, 4))

    def test_cache_directory_exists(self):
        self.assertTrue(os.path.exists(CACHE_DIR))


if __name__ == "__main__":
    unittest.main()
