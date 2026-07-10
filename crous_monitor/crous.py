"""Client de l'API JSON de trouverunlogement.lescrous.fr (voir docs/adr/0001)."""

import json
from dataclasses import dataclass

import requests

from .geocode import Zone

BASE = "https://trouverunlogement.lescrous.fr"
USER_AGENT = "crous-monitor/1.0 (moniteur personnel de disponibilite)"


@dataclass(frozen=True)
class Annonce:
    """Une annonce publiée sur le site du CROUS, identifiée par son ID (cf. CONTEXT.md)."""

    id: int
    titre: str
    residence: str
    prix: str
    url: str
    brut: str  # JSON brut de l'annonce, conservé tel quel


def _premier_champ(item: dict, *chemins, defaut: str = "?") -> str:
    """Extrait le premier champ non vide parmi des chemins candidats ("a.b" = item["a"]["b"]).

    Le schéma de l'API n'est pas documenté : on parse défensivement pour que
    l'apparition d'un champ manquant ne fasse jamais échouer un cycle.
    """
    for chemin in chemins:
        valeur = item
        for cle in chemin.split("."):
            if not isinstance(valeur, dict) or cle not in valeur:
                valeur = None
                break
            valeur = valeur[cle]
        if valeur not in (None, "", [], {}):
            return str(valeur)
    return defaut


def _prix(item: dict) -> str:
    """Le site exprime les loyers en centimes ; on tente plusieurs champs candidats."""
    for chemin in ("occupationModes", ):
        modes = item.get(chemin)
        if isinstance(modes, list):
            montants = [m.get("rent") for m in modes if isinstance(m, dict) and m.get("rent")]
            if montants:
                return " / ".join(f"{m / 100:.0f} €" for m in montants)
    for cle in ("rent", "minRent", "rentMin"):
        valeur = item.get(cle)
        if isinstance(valeur, (int, float)) and valeur > 0:
            return f"{valeur / 100:.0f} €"
        if isinstance(valeur, dict):
            montants = [v for v in (valeur.get("min"), valeur.get("max")) if v]
            if montants:
                return "–".join(f"{m / 100:.0f} €" for m in montants)
    return "prix ?"


def chercher_annonces(zone: Zone, tool_id: int) -> list[Annonce]:
    """Interroge le CROUS pour une zone. Lève une exception en cas d'erreur :
    une erreur ne doit JAMAIS être confondue avec « aucune annonce » (docs/adr/0001)."""
    payload = {
        "idTool": tool_id,
        "need_aggregation": False,
        "page": 1,
        "pageSize": 500,
        "sector": None,
        "occupationModes": [],
        "location": [
            {"lon": zone.lon_min, "lat": zone.lat_max},  # coin nord-ouest
            {"lon": zone.lon_max, "lat": zone.lat_min},  # coin sud-est
        ],
        "residence": None,
        "precision": 8,
        "equipment": [],
        "price": {"max": 10000000},
        "toolMechanism": "residual",
    }
    reponse = requests.post(
        f"{BASE}/api/fr/search/{tool_id}",
        json=payload,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    reponse.raise_for_status()
    corps = reponse.json()
    items = corps["results"]["items"]  # KeyError = schéma inattendu = panne, pas zéro annonce

    annonces = []
    for item in items:
        id_annonce = item.get("id")
        if id_annonce is None:
            continue
        annonces.append(
            Annonce(
                id=int(id_annonce),
                titre=_premier_champ(item, "label", "title", "name", defaut="Logement CROUS"),
                residence=_premier_champ(item, "residence.label", "residence.name", "address", defaut="?"),
                prix=_prix(item),
                url=f"{BASE}/tools/{tool_id}/accommodations/{id_annonce}",
                brut=json.dumps(item, ensure_ascii=False),
            )
        )
    return annonces
