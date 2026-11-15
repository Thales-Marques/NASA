"""
SatAgro - Cliente de Integração com a API NASA POWER e Validação de Dados
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Este módulo implementa a comunicação REAL com a API pública da NASA POWER,
validação rigorosa de integridade (rejeitando valores -999, não-finitos ou incompletos),
extração dinâmica de proveniência dos metadados e suporte a conjunto de demonstração
verificado para o local-piloto (Sertãozinho - SP).
"""

from __future__ import annotations

import os
import json
import math
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
VERIFIED_PILOT_FILE = os.path.join(DATA_DIR, "pilot_sertaozinho_verified.json")
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "nasa_power")
BASE_URL = "https://power.larc.nasa.gov/api/temporal"

CALENDAR_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
REQUIRED_PARAMETERS = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M"]


class NasaPowerError(Exception):
    """Exceção base para erros na integração com NASA POWER."""
    pass


class NasaPowerConnectionError(NasaPowerError):
    """Erro de conectividade de rede com a API NASA POWER (timeout, offline, DNS)."""
    pass


class NasaPowerAPIError(NasaPowerError):
    """Erro retornado pelo servidor da NASA POWER (HTTP 4xx ou 5xx)."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NasaDataValidationError(NasaPowerError):
    """Erro de validação nos dados recebidos da NASA (valores sentinela -999, meses ausentes, estrutura inválida)."""
    pass


def _ensure_cache_dir() -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR


def _build_cache_filename(lat: float, lon: float) -> str:
    norm_lat = round(float(lat), 4)
    norm_lon = round(float(lon), 4)
    key = f"climatology_{norm_lat}_{norm_lon}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"power_climatology_{norm_lat}_{norm_lon}_{h}.json"


def validate_nasa_climatology_response(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    P0.3 - Validação rigorosa dos dados da NASA POWER.
    
    Verifica:
    1. Estrutura básica do payload JSON.
    2. Presença dos parâmetros meteorológicos obrigatórios.
    3. Presença de todos os 12 meses do ano para cada parâmetro.
    4. Rejeição de sentinelas (-999, -999.0, -9999), NaN ou valores não-finitos.
    5. Não substituição de dados ausentes por zero ou constantes arbitrárias.
    """
    if not isinstance(raw_data, dict):
        raise NasaDataValidationError("A resposta da API NASA POWER não é um objeto JSON válido.")

    properties = raw_data.get("properties")
    if not isinstance(properties, dict):
        raise NasaDataValidationError("Estrutura da API inválida: campo 'properties' ausente.")

    parameters = properties.get("parameter")
    if not isinstance(parameters, dict):
        raise NasaDataValidationError("Estrutura da API inválida: campo 'properties.parameter' ausente.")

    header = raw_data.get("header", {})
    fill_value = float(header.get("fill_value", -999.0))
    sentinels = {fill_value, -999.0, -999, -9999.0, -9999}

    validated_parameters = {}

    for param_name in REQUIRED_PARAMETERS:
        if param_name not in parameters:
            raise NasaDataValidationError(f"Parâmetro obrigatório '{param_name}' não foi retornado pela NASA POWER.")

        param_dict = parameters[param_name]
        if not isinstance(param_dict, dict):
            raise NasaDataValidationError(f"Formato inválido para o parâmetro '{param_name}'.")

        validated_months = {}
        for month in CALENDAR_MONTHS:
            if month not in param_dict:
                raise NasaDataValidationError(
                    f"Mês '{month}' ausente no parâmetro '{param_name}'. Os 12 meses são indispensáveis."
                )

            val = param_dict[month]
            if val is None:
                raise NasaDataValidationError(f"Valor nulo (None) encontrado no parâmetro '{param_name}' para o mês '{month}'.")

            try:
                f_val = float(val)
            except (ValueError, TypeError):
                raise NasaDataValidationError(
                    f"Valor não-numérico '{val}' encontrado no parâmetro '{param_name}' para o mês '{month}'."
                )

            if math.isnan(f_val) or math.isinf(f_val):
                raise NasaDataValidationError(
                    f"Valor não-finito (NaN ou Infinito) no parâmetro '{param_name}' para o mês '{month}'."
                )

            if f_val in sentinels or abs(f_val - fill_value) < 1e-4:
                raise NasaDataValidationError(
                    f"Valor sentinela/ausente detectado pela NASA ({f_val}) no parâmetro '{param_name}' para o mês '{month}'."
                )

            validated_months[month] = f_val

        # Também preservar a média anual 'ANN' se disponível e válida
        if "ANN" in param_dict:
            try:
                ann_val = float(param_dict["ANN"])
                if not (math.isnan(ann_val) or math.isinf(ann_val) or ann_val in sentinels):
                    validated_months["ANN"] = ann_val
            except Exception:
                pass

        validated_parameters[param_name] = validated_months

    # Se radiação solar estiver disponível e válida, adiciona
    if "ALLSKY_SFC_SW_DWN" in parameters:
        sw_dict = parameters["ALLSKY_SFC_SW_DWN"]
        if isinstance(sw_dict, dict):
            valid_sw = {}
            for month in CALENDAR_MONTHS:
                if month in sw_dict:
                    try:
                        v = float(sw_dict[month])
                        if not (math.isnan(v) or math.isinf(v) or v in sentinels):
                            valid_sw[month] = v
                    except Exception:
                        pass
            if len(valid_sw) == 12:
                validated_parameters["ALLSKY_SFC_SW_DWN"] = valid_sw

    return validated_parameters


def parse_nasa_metadata(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    P0.4 - Extração dinâmica e precisa de metadados da resposta da NASA.
    Lê diretamente de header, api, sources, geometry e parameters.
    """
    header = raw_data.get("header", {})
    api_info = header.get("api", {})
    sources = header.get("sources", ["MERRA2", "SYN1DEG", "POWER"])
    climatology_range = header.get("range", "Período climatológico multianual (2001–2025)")
    api_version = api_info.get("version", "v2.10.1")

    geometry = raw_data.get("geometry", {})
    coords = geometry.get("coordinates", [])
    elevation_m = coords[2] if len(coords) >= 3 else None

    param_metadata = raw_data.get("parameters", {})

    return {
        "api_name": api_info.get("name", "POWER Climatology API"),
        "api_version": api_version,
        "climatology_range": climatology_range,
        "sources": sources,
        "fill_value": header.get("fill_value", -999.0),
        "elevation_m": elevation_m,
        "parameters_info": param_metadata,
        "spatial_resolution_meteorology": "0,5° latitude × 0,625° longitude (~50 km × ~65 km) — Modelo NASA GMAO MERRA-2",
        "spatial_resolution_solar": "1,0° × 1,0° (~110 km) — Projeto NASA CERES / SYN1DEG",
        "spatial_disclaimer": "Médias históricas regionais da grade MERRA-2 da NASA; não representam medições microclimáticas de um talhão individual.",
    }


def load_verified_pilot_dataset() -> Dict[str, Any]:
    """
    P0.7 - Carrega o conjunto verificado de demonstração do ponto piloto de Sertãozinho (SP).
    Garante execução 100% confiável e sem dependência de rede ou de cache ignorado pelo Git.
    """
    if not os.path.exists(VERIFIED_PILOT_FILE):
        raise NasaPowerError(f"Arquivo de demonstração verificado não encontrado em: {VERIFIED_PILOT_FILE}")

    with open(VERIFIED_PILOT_FILE, "r", encoding="utf-8") as f:
        pilot_data = json.load(f)

    raw_response = pilot_data.get("raw_response", {})
    validated_params = validate_nasa_climatology_response(raw_response)
    metadata = parse_nasa_metadata(raw_response)

    return {
        "source": "NASA POWER Climatology API v2.10.1 (Verificado para o Piloto)",
        "is_verified_pilot": True,
        "is_cached": False,
        "pilot_site": pilot_data.get("pilot_site", "Sertãozinho - SP, Brasil"),
        "latitude": pilot_data.get("latitude", -21.1378),
        "longitude": pilot_data.get("longitude", -47.9897),
        "collected_at": pilot_data.get("acquired_at_utc", "2026-11-15 22:29:38 UTC"),
        "metadata": metadata,
        "parameters": validated_params,
        "verification_note": pilot_data.get("verification_note", "Conjunto autêntico verificado."),
    }


def is_near_pilot(lat: float, lon: float, tolerance: float = 0.05) -> bool:
    """Verifica se a coordenada coincide com o local-piloto de Sertãozinho."""
    return abs(lat - (-21.1378)) < tolerance and abs(lon - (-47.9897)) < tolerance


def fetch_climatology(
    lat: float,
    lon: float,
    timeout: int = 15,
    use_cache: bool = True,
    force_pilot_demo: bool = False
) -> Dict[str, Any]:
    """
    Recupera a climatologia histórica com validação estrita e tratamento de erros.
    
    1. Se force_pilot_demo for True ou em caso de falha de rede para Sertãozinho,
       utiliza o conjunto de demonstração verificado empacotado no repositório.
    2. Valida todos os parâmetros contra sentinelas (-999) e meses ausentes antes de aceitar.
    3. Trata HTTP 429 (Too Many Requests), 5xx e timeouts de forma limpa.
    """
    if force_pilot_demo:
        return load_verified_pilot_dataset()

    cache_file = os.path.join(CACHE_DIR, _build_cache_filename(lat, lon))

    # Tenta cache local se use_cache=True
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            raw_resp = cached_data.get("raw_response", {})
            valid_params = validate_nasa_climatology_response(raw_resp)
            metadata = parse_nasa_metadata(raw_resp)
            return {
                "source": "NASA POWER Climatology (Cache Local)",
                "is_verified_pilot": False,
                "is_cached": True,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "collected_at": cached_data.get("collected_at", "Horário registrado no cache"),
                "metadata": metadata,
                "parameters": valid_params,
            }
        except Exception:
            pass

    # Consulta real à API NASA POWER
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
    except (requests.ConnectionError, requests.Timeout) as net_err:
        if is_near_pilot(lat, lon):
            pilot = load_verified_pilot_dataset()
            pilot["offline_notice"] = (
                f"Aviso de Rede: A API da NASA POWER está temporariamente inacessível ({type(net_err).__name__}). "
                "Exibindo com segurança o conjunto de demonstração verificado do piloto de Sertãozinho."
            )
            return pilot

        raise NasaPowerConnectionError(
            f"Não foi possível conectar à API da NASA POWER ({type(net_err).__name__}). "
            f"Verifique sua conexão com a internet ou tente novamente em instantes."
        ) from net_err

    if response.status_code == 429:
        if is_near_pilot(lat, lon):
            pilot = load_verified_pilot_dataset()
            pilot["offline_notice"] = "Aviso (HTTP 429): Limite de requisições da NASA atingido. Exibindo conjunto verificado do piloto."
            return pilot
        raise NasaPowerAPIError(
            "A API da NASA POWER retornou HTTP 429 (Muitas Requisições / Rate Limit). Aguarde alguns segundos.",
            status_code=429
        )

    if response.status_code >= 500:
        if is_near_pilot(lat, lon):
            pilot = load_verified_pilot_dataset()
            pilot["offline_notice"] = f"Aviso (HTTP {response.status_code}): Servidor da NASA indisponível. Exibindo conjunto verificado do piloto."
            return pilot
        raise NasaPowerAPIError(
            f"O servidor da NASA POWER apresentou instabilidade temporária (HTTP {response.status_code}).",
            status_code=response.status_code
        )

    if response.status_code != 200:
        raise NasaPowerAPIError(
            f"A API da NASA POWER retornou erro HTTP {response.status_code}: {response.text[:180]}",
            status_code=response.status_code
        )

    try:
        raw_json = response.json()
    except Exception as json_err:
        raise NasaPowerAPIError(f"Resposta recebida da NASA POWER não é um JSON válido: {json_err}")

    validated_parameters = validate_nasa_climatology_response(raw_json)
    metadata = parse_nasa_metadata(raw_json)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    _ensure_cache_dir()
    cache_payload = {
        "collected_at": now_utc,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "raw_response": raw_json,
    }
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "source": "NASA POWER Climatology API v2.10.1 (Consulta Ao Vivo)",
        "is_verified_pilot": False,
        "is_cached": False,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "collected_at": now_utc,
        "metadata": metadata,
        "parameters": validated_parameters,
    }
