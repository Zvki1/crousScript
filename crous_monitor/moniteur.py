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


def executer_cycle(config: Config, conn: sqlite3.Connection, zones: dict[str, Zone]) -> int:
    """Exécute un cycle de vérification pour toutes les surveillances.

    Retourne le nombre d'alertes émises. Laisse remonter les exceptions :
    c'est l'appelant (main) qui tient le compte des échecs consécutifs.
    """
    nb_alertes = 0
    for surveillance in config.surveillances:
        zone = zones[surveillance.nom]
        annonces = crous.chercher_annonces(zone, config.tool_id)
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
