"""
SatAgro - Cliente de Integração com a API NASA POWER
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Este módulo implementa a comunicação REAL com a API pública do NASA POWER
(Prediction Of Worldwide Energy Resources - https://power.larc.nasa.gov/).
Inclui sistema de cache local, tratamento de falhas e rastreabilidade temporal.
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import requests

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "nasa_power")

BASE_URL = "https://power.larc.nasa.gov/api/temporal"


class NasaPowerError(Exception):
    """Exceção base para erros na integração com NASA POWER."""
    pass


class NasaPowerConnectionError(NasaPowerError):
    """Erro de conectividade de rede com a API NASA POWER."""
    pass


class NasaPowerAPIError(NasaPowerError):
    """Erro retornado pelo servidor da NASA POWER (HTTP 4xx ou 5xx)."""
    pass


def _ensure_cache_dir() -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR


def _build_cache_filename(endpoint: str, lat: float, lon: float, extra: str = "") -> str:
    """Gera nome único de cache determinístico baseado nas coordenadas e requisição."""
    norm_lat = round(float(lat), 3)
    norm_lon = round(float(lon), 3)
    key = f"{endpoint}_{norm_lat}_{norm_lon}_{extra}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"power_{endpoint}_{norm_lat}_{norm_lon}_{h}.json"


def fetch_climatology(
    lat: float,
    lon: float,
    timeout: int = 15,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Recupera a climatologia histórica (médias de 30 anos) para o ponto especificado.
    
    Parâmetros solicitados:
    - T2M: Temperatura Média do Ar a 2m (°C)
    - T2M_MAX: Temperatura Máxima do Ar a 2m (°C)
    - T2M_MIN: Temperatura Mínima do Ar a 2m (°C)
    - PRECTOTCORR: Precipitação Corrigida (mm/dia)
    - RH2M: Umidade Relativa do Ar a 2m (%)
    - ALLSKY_SFC_SW_DWN: Radiação Solar Incidente em Superfície (MJ/m²/dia)
    """
    _ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, _build_cache_filename("climatology", lat, lon))
    
    # 1. Tentar ler cache local
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_payload = json.load(f)
                cached_payload["is_cached"] = True
                return cached_payload
        except Exception:
            pass  # Se o cache estiver corrompido, busca na rede

    # 2. Requisição real à API da NASA
    endpoint_url = f"{BASE_URL}/climatology/point"
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "format": "JSON",
    }
    
    try:
        response = requests.get(endpoint_url, params=params, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as conn_err:
        # Se falhou mas temos cache expirado, podemos usar avisando
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_payload = json.load(f)
                cached_payload["is_cached"] = True
                cached_payload["offline_warning"] = (
                    "Aviso: Não foi possível contatar a API da NASA em tempo hábil. "
                    "Exibindo dados previamente armazenados em cache local."
                )
                return cached_payload
        raise NasaPowerConnectionError(
            f"Falha de conexão com a API da NASA POWER (timeout={timeout}s): {conn_err}"
        ) from conn_err
    except Exception as e:
        raise NasaPowerConnectionError(f"Erro inesperado de rede: {e}") from e

    if response.status_code != 200:
        raise NasaPowerAPIError(
            f"A API da NASA POWER retornou código de erro HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
        props = data.get("properties", {})
        parameter_data = props.get("parameter", {})
    except Exception as parse_err:
        raise NasaPowerAPIError(f"Resposta inválida recebida da NASA POWER: {parse_err}") from parse_err

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "source": "NASA POWER Climatology API v2.0 (GMAO MERRA-2 / CERES)",
        "spatial_resolution": "~0.5° x 0.5° (~50 km)",
        "temporal_coverage": "Série histórica climatológica multi-anual padronizada",
        "collected_at": now_utc,
        "is_cached": False,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "parameters": parameter_data,
        "header": data.get("header", {}),
    }

    # Salva no cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Falha de gravação de cache não deve impedir o uso

    return payload


def fetch_historical_monthly(
    lat: float,
    lon: float,
    start_year: int = 2021,
    end_year: int = 2024,
    timeout: int = 20,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Recupera série histórica mensal para cálculo de anomalias recentes.
    """
    _ensure_cache_dir()
    extra_key = f"{start_year}_{end_year}"
    cache_file = os.path.join(CACHE_DIR, _build_cache_filename("monthly", lat, lon, extra=extra_key))

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_payload = json.load(f)
                cached_payload["is_cached"] = True
                return cached_payload
        except Exception:
            pass

    endpoint_url = f"{BASE_URL}/monthly/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "start": str(start_year),
        "end": str(end_year),
        "format": "JSON",
    }

    try:
        response = requests.get(endpoint_url, params=params, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as conn_err:
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_payload = json.load(f)
                cached_payload["is_cached"] = True
                cached_payload["offline_warning"] = "Exibindo série histórica do cache local."
                return cached_payload
        raise NasaPowerConnectionError(f"Falha de conexão com a API NASA POWER: {conn_err}") from conn_err

    if response.status_code != 200:
        raise NasaPowerAPIError(f"Erro HTTP {response.status_code} na API NASA POWER: {response.text[:200]}")

    data = response.json()
    props = data.get("properties", {})
    parameter_data = props.get("parameter", {})
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "source": "NASA POWER Monthly API v2.0",
        "spatial_resolution": "~0.5° x 0.5°",
        "collected_at": now_utc,
        "is_cached": False,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "start_year": start_year,
        "end_year": end_year,
        "parameters": parameter_data,
    }

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return payload
