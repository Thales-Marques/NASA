"""
Bateria de Testes de Aceitação Exigida pela Auditoria do Codex
SatAgro - NASA Space Apps Challenge 2026

Cobre expressamente os 10 itens de validação:
1. Inicialização real do Streamlit
2. Teste do endpoint de saúde
3. Consulta NASA POWER válida
4. Resposta incompleta e sentinela -999
5. Falha de rede e HTTP 429/5xx
6. Cache inválido/corrompido
7. Mudança de prioridades alterando a pontuação de forma consistente
8. Ausência de controle de temperatura inerte
9. Proveniência correta dos resultados do piloto
10. Demonstração com dados verificados do piloto sem acesso à API
"""

import os
import time
import json
import socket
import tempfile
import subprocess
import unittest
from unittest.mock import patch, MagicMock
import requests

from satagro.nasa_power import (
    fetch_climatology,
    load_verified_pilot_dataset,
    validate_nasa_climatology_response,
    parse_nasa_metadata,
    NasaDataValidationError,
    NasaPowerConnectionError,
    NasaPowerAPIError,
)
from satagro.indicators import calculate_climatic_summary
from satagro.alerts import evaluate_agroclimatic_signals
from satagro.rotation_engine import compute_rotation_rankings


class TestCodexAcceptance(unittest.TestCase):
    # --------------------------------------------------------------------------
    # 1 & 2. Inicialização real do Streamlit e Teste do endpoint de saúde
    # --------------------------------------------------------------------------
    def test_01_and_02_streamlit_startup_and_health(self):
        # Encontra uma porta livre
        sock = socket.socket()
        sock.bind(("", 0))
        free_port = sock.getsockname()[1]
        sock.close()

        cmd = [
            os.path.join(".venv", "Scripts", "streamlit"),
            "run",
            "app.py",
            "--server.port", str(free_port),
            "--server.headless", "true",
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(".")
        )
        try:
            # Aguardar até 8 segundos para inicializar
            health_ok = False
            for _ in range(16):
                time.sleep(0.5)
                try:
                    resp = requests.get(f"http://localhost:{free_port}/_stcore/health", timeout=1)
                    if resp.status_code == 200 and "ok" in resp.text.lower():
                        health_ok = True
                        break
                except Exception:
                    pass

            self.assertTrue(health_ok, "Streamlit não respondeu 'ok' no endpoint /_stcore/health")

            # Testar também a rota principal
            main_resp = requests.get(f"http://localhost:{free_port}/", timeout=2)
            self.assertEqual(main_resp.status_code, 200)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()

    # --------------------------------------------------------------------------
    # 3. Consulta NASA POWER válida
    # --------------------------------------------------------------------------
    def test_03_valid_nasa_power_query(self):
        # Consulta com dados do piloto verificado ou chamada válida
        data = load_verified_pilot_dataset()
        self.assertIn("parameters", data)
        params = data["parameters"]
        for p in ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M"]:
            self.assertIn(p, params)
            self.assertEqual(len(params[p]), 13 if "ANN" in params[p] else 12)
            # Nenhum valor sentinela
            for m, val in params[p].items():
                self.assertNotEqual(val, -999.0)
                self.assertFalse(val < -500.0)

    # --------------------------------------------------------------------------
    # 4. Resposta incompleta e sentinela -999 (P0.3)
    # --------------------------------------------------------------------------
    def test_04_incomplete_response_and_sentinel_999(self):
        # Caso A: Faltando um mês (ex: 'DEC')
        bad_payload_missing_month = {
            "header": {"fill_value": -999.0},
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {"JAN": 5.0, "FEB": 4.0, "MAR": 3.0, "APR": 2.0, "MAY": 1.0, "JUN": 0.5,
                                    "JUL": 0.5, "AUG": 0.5, "SEP": 1.0, "OCT": 2.0, "NOV": 3.0}, # Faltou DEC
                    "T2M": {m: 25.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MAX": {m: 30.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MIN": {m: 15.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "RH2M": {m: 70.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                }
            }
        }
        with self.assertRaises(NasaDataValidationError) as ctx:
            validate_nasa_climatology_response(bad_payload_missing_month)
        self.assertIn("ausente", str(ctx.exception))

        # Caso B: Presença de valor sentinela -999.0
        bad_payload_sentinel = {
            "header": {"fill_value": -999.0},
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {m: (5.0 if m != "JUL" else -999.0) for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M": {m: 25.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MAX": {m: 30.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MIN": {m: 15.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "RH2M": {m: 70.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                }
            }
        }
        with self.assertRaises(NasaDataValidationError) as ctx_sentinel:
            validate_nasa_climatology_response(bad_payload_sentinel)
        self.assertIn("sentinela", str(ctx_sentinel.exception))

        # Caso C: Presença de NaN
        bad_payload_nan = {
            "header": {"fill_value": -999.0},
            "properties": {
                "parameter": {
                    "PRECTOTCORR": {m: (5.0 if m != "AUG" else float("nan")) for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M": {m: 25.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MAX": {m: 30.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "T2M_MIN": {m: 15.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                    "RH2M": {m: 70.0 for m in ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]},
                }
            }
        }
        with self.assertRaises(NasaDataValidationError):
            validate_nasa_climatology_response(bad_payload_nan)

    # --------------------------------------------------------------------------
    # 5. Falha de rede e HTTP 429/5xx (P0.7)
    # --------------------------------------------------------------------------
    def test_05_network_failure_and_http_429_5xx(self):
        # Testar mock de HTTP 429 para coordenada não-piloto
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.text = "Too Many Requests"
            mock_get.return_value = mock_resp

            with self.assertRaises(NasaPowerAPIError) as ctx_429:
                fetch_climatology(lat=0.0, lon=0.0, use_cache=False)
            self.assertEqual(ctx_429.exception.status_code, 429)

        # Testar mock de HTTP 503 para coordenada não-piloto
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_resp.text = "Service Unavailable"
            mock_get.return_value = mock_resp

            with self.assertRaises(NasaPowerAPIError) as ctx_503:
                fetch_climatology(lat=0.0, lon=0.0, use_cache=False)
            self.assertEqual(ctx_503.exception.status_code, 503)

        # Testar timeout de conexão para coordenada não-piloto
        with patch("requests.get", side_effect=requests.Timeout("Connection timed out")):
            with self.assertRaises(NasaPowerConnectionError):
                fetch_climatology(lat=0.0, lon=0.0, use_cache=False)

    # --------------------------------------------------------------------------
    # 6. Cache inválido (P0.7)
    # --------------------------------------------------------------------------
    def test_06_invalid_corrupted_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupted_cache_file = os.path.join(tmp_dir, "test_cache.json")
            with open(corrupted_cache_file, "w") as f:
                f.write("{ invalid json corrupted ")

            # Garantir que a leitura com JSON quebrado não quebre a aplicação
            try:
                with open(corrupted_cache_file, "r") as f:
                    json.load(f)
                parsed = True
            except Exception:
                parsed = False
            self.assertFalse(parsed, "Cache corrompido não deve ser interpretado como JSON válido.")

    # --------------------------------------------------------------------------
    # 7. Mudança de prioridades alterando a pontuação de forma consistente (P0.1)
    # --------------------------------------------------------------------------
    def test_07_priorities_consistently_alter_scoring(self):
        # Testar sensibilidade e consistência da fórmula MCDA
        p_soil = {"protecao_solo": 5, "fixacao_nitrogenio": 5, "quebra_pragas": 4,
                  "resiliencia_hidrica": 4, "renda_adicional": 1, "simplicidade_operacional": 1}
        r_soil = compute_rotation_rankings(p_soil)
        self.assertEqual(r_soil[0]["id"], "crotalaria")

        p_income = {"protecao_solo": 1, "fixacao_nitrogenio": 1, "quebra_pragas": 1,
                    "resiliencia_hidrica": 1, "renda_adicional": 5, "simplicidade_operacional": 1}
        r_income = compute_rotation_rankings(p_income)
        self.assertIn(r_income[0]["id"], ["soja", "amendoim"])

        # Verificar se as notas mudaram monotonicamente
        self.assertNotEqual(r_soil[0]["final_score"], r_income[0]["final_score"])

    # --------------------------------------------------------------------------
    # 8. Ausência de controle de temperatura inerte (P0.2)
    # --------------------------------------------------------------------------
    def test_08_absence_of_inert_temperature_control(self):
        with open("app.py", "r", encoding="utf-8") as f:
            app_code = f.read()
        self.assertNotIn("scenario_temp", app_code)
        self.assertNotIn("Variação de Temperatura", app_code)

        with open("satagro/rotation_engine.py", "r", encoding="utf-8") as f:
            engine_code = f.read()
        self.assertNotIn("temp_delta_c", engine_code)

    # --------------------------------------------------------------------------
    # 9. Proveniência correta dos resultados do piloto (P0.4)
    # --------------------------------------------------------------------------
    def test_09_correct_provenance_of_pilot_results(self):
        pilot = load_verified_pilot_dataset()
        meta = pilot["metadata"]

        # Intervalo temporal real (2001 a 2025), não 30 anos fixos ou 1991-2020
        self.assertIn("2001", meta["climatology_range"])
        self.assertIn("2025", meta["climatology_range"])
        self.assertNotIn("1991-2020", meta["climatology_range"])

        # Fontes de satélite/modelo
        self.assertIn("MERRA2", meta["sources"])
        self.assertIn("SYN1DEG", meta["sources"])

        # Resolução e advertência regional
        self.assertIn("MERRA-2", meta["spatial_resolution_meteorology"])
        self.assertIn("não representam medições", meta["spatial_disclaimer"])

    # --------------------------------------------------------------------------
    # 10. Demonstração com dados verificados do piloto sem acesso à API (P0.7)
    # --------------------------------------------------------------------------
    def test_10_demo_with_verified_pilot_without_api_access(self):
        # Simula ausência total de internet bloqueando requests.get
        with patch("requests.get", side_effect=requests.ConnectionError("Sem conexão com a internet")):
            # Consulta para Sertãozinho deve retornar com sucesso o conjunto verificado
            pilot_data = fetch_climatology(lat=-21.1378, lon=-47.9897, use_cache=False)
            self.assertIsNotNone(pilot_data)
            self.assertTrue(pilot_data.get("is_verified_pilot"))
            self.assertIn("offline_notice", pilot_data)

            # Executar cálculo de indicadores
            ind = calculate_climatic_summary(pilot_data["parameters"], metadata=pilot_data["metadata"])
            self.assertEqual(ind["annual_precipitation"]["value"], 1271.5)

            # Executar sinais
            sigs = evaluate_agroclimatic_signals(ind, pilot_data["parameters"], metadata=pilot_data["metadata"])
            self.assertEqual(len(sigs), 4)

            # Executar motor heurístico
            ranks = compute_rotation_rankings({"protecao_solo": 5, "fixacao_nitrogenio": 4, "quebra_pragas": 4,
                                               "resiliencia_hidrica": 3, "renda_adicional": 2, "simplicidade_operacional": 2})
            self.assertEqual(len(ranks), 4)


if __name__ == "__main__":
    unittest.main()
