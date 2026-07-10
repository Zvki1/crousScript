"""Conversion d'un nom de ville en zone de surveillance (bounding box élargie d'une marge)."""

import math
from dataclasses import dataclass

import requests

GEO_API = "https://geo.api.gouv.fr/communes"


@dataclass(frozen=True)
class Zone:
    """Zone de surveillance : la bbox de la commune élargie de la marge (cf. CONTEXT.md)."""

    ville: str
    lon_min: float
    lat_min: float
    lon_max: float
    lat_max: float


def zone_pour_ville(nom: str, marge_km: float) -> Zone:
    """Géocode la commune la plus peuplée portant ce nom et élargit sa bbox de marge_km."""
    reponse = requests.get(
        GEO_API,
        params={"nom": nom, "fields": "nom,bbox", "boost": "population", "limit": 1},
        timeout=10,
    )
    reponse.raise_for_status()
    communes = reponse.json()
    if not communes:
        raise SystemExit(f"❌ Ville introuvable : « {nom} » (vérifie l'orthographe)")

    commune = communes[0]
    points = commune["bbox"]["coordinates"][0]
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)

    # Conversion km → degrés : ~111 km par degré de latitude,
    # et 111·cos(latitude) km par degré de longitude.
    marge_lat = marge_km / 111.0
    marge_lon = marge_km / (111.0 * math.cos(math.radians((lat_min + lat_max) / 2)))

    return Zone(
        ville=commune["nom"],
        lon_min=lon_min - marge_lon,
        lat_min=lat_min - marge_lat,
        lon_max=lon_max + marge_lon,
        lat_max=lat_max + marge_lat,
    )
