"""Cliente da API FIPE (Parallelum) — motos."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://parallelum.com.br/fipe/api/v1"
TIPO_MOTO = "motos"
TIMEOUT = 20


class FipeApiError(Exception):
    """Erro ao consultar a API FIPE."""


@dataclass(frozen=True)
class FipeItem:
    codigo: str
    nome: str


@dataclass(frozen=True)
class FipePreco:
    valor: float
    codigo_fipe: str
    marca: str
    modelo: str
    ano_modelo: int
    combustivel: str
    mes_referencia: str
    tipo_veiculo: int
    valor_texto: str


def _headers() -> dict[str, str]:
    token = os.environ.get("FIPE_API_TOKEN", "").strip()
    if token:
        return {"X-Subscription-Token": token}
    return {}


def _get(path: str) -> Any:
    url = f"{BASE_URL}/{TIPO_MOTO}/{path}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise FipeApiError(f"Falha na consulta FIPE: {e}") from e


def listar_marcas() -> list[FipeItem]:
    data = _get("marcas")
    return [FipeItem(codigo=str(m["codigo"]), nome=m["nome"]) for m in data]


def listar_modelos(codigo_marca: str) -> list[FipeItem]:
    data = _get(f"marcas/{codigo_marca}/modelos")
    modelos = data.get("modelos", data) if isinstance(data, dict) else data
    return [FipeItem(codigo=str(m["codigo"]), nome=m["nome"]) for m in modelos]


def listar_anos(codigo_marca: str, codigo_modelo: str) -> list[FipeItem]:
    data = _get(f"marcas/{codigo_marca}/modelos/{codigo_modelo}/anos")
    return [FipeItem(codigo=str(a["codigo"]), nome=a["nome"]) for a in data]


def parse_valor_fipe(valor_texto: str) -> float:
    """Converte 'R$ 25.000,00' em float."""
    s = valor_texto.replace("R$", "").strip().replace(".", "").replace(",", ".")
    return float(s)


def consultar_preco(codigo_marca: str, codigo_modelo: str, codigo_ano: str) -> FipePreco:
    data = _get(f"marcas/{codigo_marca}/modelos/{codigo_modelo}/anos/{codigo_ano}")
    return FipePreco(
        valor=parse_valor_fipe(data["Valor"]),
        codigo_fipe=str(data.get("CodigoFipe", "")),
        marca=str(data.get("Marca", "")),
        modelo=str(data.get("Modelo", "")),
        ano_modelo=int(data.get("AnoModelo", 0)),
        combustivel=str(data.get("Combustivel", "")),
        mes_referencia=str(data.get("MesReferencia", "")),
        tipo_veiculo=int(data.get("TipoVeiculo", 0)),
        valor_texto=str(data.get("Valor", "")),
    )
