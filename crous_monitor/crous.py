"""Client de l'API JSON de trouverunlogement.lescrous.fr (voir docs/adr/0001, docs/adr/0003)."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from .geocode import Zone

BASE = "https://trouverunlogement.lescrous.fr"
USER_AGENT = "crous-monitor/1.0 (moniteur personnel de disponibilite)"


def outils_actifs() -> list[int]:
    """Liste les outils de recherche actuellement actifs (cf. docs/adr/0003).

    Le CROUS fait tourner plusieurs campagnes en parallèle (ex. "Fil de l'Eau",
    "Phase complémentaire"), chacune sous un idTool distinct, et ces campagnes
    s'ouvrent/expirent au fil de l'année. Un idTool codé en dur finit toujours
    par pointer vers une campagne terminée — silencieusement, car l'API répond
    200 avec une liste vide plutôt qu'une erreur pour un idTool expiré.
    """
    reponse = requests.get(f"{BASE}/api/fr/tools", headers={"User-Agent": USER_AGENT}, timeout=10)
    reponse.raise_for_status()
    maintenant = datetime.now(timezone.utc)
    actifs = []
    for outil in reponse.json():
        if not outil.get("enabled"):
            continue
        fin = outil.get("endDate")
        if fin and datetime.fromisoformat(fin) < maintenant:
            continue
        actifs.append(int(outil["id"]))
    return actifs


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


_LABELS_OCCUPATION = {"alone": "Seul(e)", "couple": "Couple", "house_sharing": "Colocation"}


def _prix(item: dict) -> str:
    """Le loyer vit dans occupationModes[].rent = {min, max} en centimes, un par mode
    d'occupation possible (seul, couple, colocation). Pas de champ prix au niveau racine."""
    modes = item.get("occupationModes")
    if not isinstance(modes, list):
        return "prix ?"

    parts = []
    for mode in modes:
        rent = mode.get("rent") if isinstance(mode, dict) else None
        if not isinstance(rent, dict):
            continue
        mini, maxi = rent.get("min"), rent.get("max")
        if mini is None and maxi is None:
            continue
        if mini is None or maxi is None or mini == maxi:
            montant = f"{(mini or maxi) / 100:.0f} €"
        else:
            montant = f"{mini / 100:.0f}–{maxi / 100:.0f} €"
        label = _LABELS_OCCUPATION.get(mode.get("type"))
        parts.append(f"{label} : {montant}" if label else montant)

    return " / ".join(parts) if parts else "prix ?"


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
