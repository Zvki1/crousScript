"""Le cœur : un cycle de vérification pour chaque surveillance (cf. CONTEXT.md)."""

import html
import sqlite3

from . import crous, etat, telegram
from .config import Config, Surveillance
from .geocode import Zone

ENTETES = {
    "nouvelle": "🏠 Nouvelle annonce CROUS",
    "reapparition": "🔄 Annonce de nouveau disponible",
}


def _message_alerte(motif: str, annonce: crous.Annonce, surveillance: Surveillance) -> str:
    return (
        f"<b>{ENTETES[motif]} — {html.escape(surveillance.nom)}</b>\n\n"
        f"<b>{html.escape(annonce.titre)}</b>\n"
        f"📍 {html.escape(annonce.residence)}\n"
        f"💰 {html.escape(annonce.prix)}\n\n"
        f'🔗 <a href="{annonce.url}">Voir et réserver</a>\n'
        f"⚡ Fonce, les chambres partent en quelques minutes."
    )


def _annonces_zone(zone: Zone, tool_ids: list[int]) -> list[crous.Annonce]:
    """Interroge tous les outils actifs pour une zone et fusionne les résultats.

    Une même annonce ne peut apparaître que dans un seul outil à la fois
    (chaque campagne porte ses propres logements), donc la fusion par id
    est une simple précaution, pas une déduplication attendue en pratique.
    """
    vues: dict[int, crous.Annonce] = {}
    for tool_id in tool_ids:
        for annonce in crous.chercher_annonces(zone, tool_id):
            vues[annonce.id] = annonce
    return list(vues.values())


def executer_cycle(config: Config, conn: sqlite3.Connection, zones: dict[str, Zone]) -> int:
    """Exécute un cycle de vérification pour toutes les surveillances.

    Retourne le nombre d'alertes émises. Laisse remonter les exceptions :
    c'est l'appelant (main) qui tient le compte des échecs consécutifs.
    """
    tool_ids = config.tool_ids or crous.outils_actifs()
    if not tool_ids:
        raise RuntimeError("Aucun outil de recherche CROUS actif en ce moment (cf. /api/fr/tools)")

    nb_alertes = 0
    for surveillance in config.surveillances:
        zone = zones[surveillance.nom]
        annonces = _annonces_zone(zone, tool_ids)
        a_alerter = etat.comparer(conn, surveillance.nom, annonces)

        for annonce, motif in a_alerter:
            telegram.envoyer(
                config.telegram_bot_token,
                surveillance.telegram_chat_id,
                _message_alerte(motif, annonce, surveillance),
            )
            nb_alertes += 1

        print(f"   {surveillance.nom} : {len(annonces)} annonce(s) visibles, {len(a_alerter)} alerte(s)")
    return nb_alertes
