"""
Testes Unitários - Integração NASA POWER e Cache Local
"""

import os
import unittest
from satagro.nasa_power import fetch_climatology, CACHE_DIR, NasaPowerAPIError


class TestNasaPower(unittest.TestCase):
    def test_fetch_climatology_live_and_cached(self):
        # Sertãozinho (SP)
        lat, lon = -21.14, -48.06
        
        # 1ª chamada (busca na rede ou lê cache existente)
        data = fetch_climatology(lat, lon, use_cache=True)
        self.assertIn("parameters", data)
        self.assertIn("PRECTOTCORR", data["parameters"])
        self.assertIn("T2M", data["parameters"])
        self.assertIn("T2M_MAX", data["parameters"])
        self.assertIn("T2M_MIN", data["parameters"])
        self.assertIn("RH2M", data["parameters"])
        self.assertIn("ALLSKY_SFC_SW_DWN", data["parameters"])
        self.assertIn("collected_at", data)
        self.assertEqual(data["latitude"], lat)
        self.assertEqual(data["longitude"], lon)

        # 2ª chamada (deve vir do cache local)
        data_cached = fetch_climatology(lat, lon, use_cache=True)
        self.assertTrue(data_cached["is_cached"])

    def test_cache_directory_exists(self):
        self.assertTrue(os.path.exists(CACHE_DIR))

    def test_invalid_coordinates(self):
        # Coordenada fora do globo deve lançar erro apropriado ou ser tratada
        with self.assertRaises(Exception):
            fetch_climatology(lat=999.0, lon=999.0, use_cache=False)


if __name__ == "__main__":
    unittest.main()
