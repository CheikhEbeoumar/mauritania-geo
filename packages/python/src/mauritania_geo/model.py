"""Typed models for mauritania_geo (mirrors the TypeScript definitions)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .data import COMMUNES as _COMMUNE_DICTS
from .data import MOUGHATAAS as _MOUGHATAA_DICTS
from .data import WILAYAS as _WILAYA_DICTS


@dataclass(frozen=True)
class Wilaya:
    """A wilaya (region) — first-level administrative division."""
    code: str
    iso_code: str
    p_code: str
    name_fr: str
    name_ar: Optional[str]
    name_en: str
    capital: str
    capital_ar: Optional[str]
    capital_latitude: float
    capital_longitude: float
    latitude: float
    longitude: float
    area_sqkm: float
    aliases: List[str] = field(default_factory=list)
    moughataas_count: int = 0
    communes_count: int = 0
    active_from: int = 1990

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Moughataa:
    """A moughataa (department) — second-level administrative division."""
    code: str
    p_code: str
    name_fr: str
    name_ar: Optional[str]
    name_en: str
    wilaya_code: str
    capital: str
    latitude: float
    longitude: float
    capital_latitude: Optional[float]
    capital_longitude: Optional[float]
    area_sqkm: float
    aliases: List[str] = field(default_factory=list)
    communes_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class Commune:
    """A commune (municipality) — third-level administrative division."""
    code: str
    p_code: str
    name_fr: str
    name_ar: Optional[str]
    name_en: str
    moughataa_code: str
    wilaya_code: str
    latitude: Optional[float]
    longitude: Optional[float]
    area_sqkm: Optional[float]
    aliases: List[str] = field(default_factory=list)
    moughataa_name_fr: Optional[str] = None
    wilaya_name_fr: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        return d


def _build_wilayas() -> List[Wilaya]:
    return [Wilaya(**{k: d[k] for k in (
        "code", "iso_code", "p_code", "name_fr", "name_ar", "name_en",
        "capital", "capital_ar", "capital_latitude", "capital_longitude",
        "latitude", "longitude", "area_sqkm", "aliases",
        "moughataas_count", "communes_count", "active_from")})
        for d in _WILAYA_DICTS]


def _build_moughataas() -> List[Moughataa]:
    return [Moughataa(**{k: d[k] for k in (
        "code", "p_code", "name_fr", "name_ar", "name_en", "wilaya_code",
        "capital", "latitude", "longitude", "capital_latitude",
        "capital_longitude", "area_sqkm", "aliases", "communes_count")})
        for d in _MOUGHATAA_DICTS]


def _build_communes() -> List[Commune]:
    return [Commune(**{k: d.get(k) for k in (
        "code", "p_code", "name_fr", "name_ar", "name_en", "moughataa_code",
        "wilaya_code", "latitude", "longitude", "area_sqkm", "aliases",
        "moughataa_name_fr", "wilaya_name_fr")})
        for d in _COMMUNE_DICTS]


WILAYAS: List[Wilaya] = _build_wilayas()
MOUGHATAAS: List[Moughataa] = _build_moughataas()
COMMUNES: List[Commune] = _build_communes()
