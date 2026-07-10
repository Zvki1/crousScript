"""Moniteur de logements CROUS.

Deux modes d'exécution :
  python main.py          boucle infinie (VPS / machine perso)
  python main.py --once   un seul cycle, code de sortie 1 si échec (GitHub Actions)

Vocabulaire du domaine : CONTEXT.md. Décisions d'architecture : docs/adr/.
"""

import random
import sys
import time
from datetime import datetime

import requests

from crous_monitor import etat, geocode, moniteur, telegram
from crous_monitor.config import Config, charger_config


def _ping_healthcheck(config: Config, ok: bool) -> None:
    """Signale le cycle au watchdog externe (healthchecks.io). Optionnel et jamais bloquant."""
    if not config.healthcheck_url:
        return
    url = config.healthcheck_url if ok else f"{config.healthcheck_url}/fail"
    try:
        requests.get(url, timeout=10)
    except requests.RequestException:
        pass


def _resoudre_zones(config: Config) -> dict[str, geocode.Zone]:
    zones = {}
    for surveillance in config.surveillances:
        zone = geocode.zone_pour_ville(surveillance.nom, surveillance.marge_km)
        zones[surveillance.nom] = zone
        print(
            f"🗺️  Zone de surveillance « {surveillance.nom} » : {zone.ville}"
            f" + {surveillance.marge_km:g} km de marge"
        )
    return zones


def _un_cycle(config: Config, conn, zones) -> bool:
    horodatage = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{horodatage}] Cycle de vérification…")
    try:
        moniteur.executer_cycle(config, conn, zones)
    except Exception as erreur:  # erreur ≠ zéro annonce (docs/adr/0001)
        print(f"❌ Échec du cycle : {erreur}")
        _ping_healthcheck(config, ok=False)
        return False
    _ping_healthcheck(config, ok=True)
    return True


def _alerter_panne(config: Config, echecs: int) -> None:
    try:
        for surveillance in config.surveillances:
            telegram.envoyer(
                config.telegram_bot_token,
                surveillance.telegram_chat_id,
                f"⚠️ <b>Moniteur CROUS en panne</b>\n"
                f"{echecs} cycles consécutifs ont échoué — les annonces ne sont plus surveillées. "
                f"Regarde les logs du serveur.",
            )
    except requests.RequestException as erreur:
        print(f"❌ Impossible d'envoyer l'alerte de panne : {erreur}")


def _alerter_retablissement(config: Config) -> None:
    try:
        for surveillance in config.surveillances:
            telegram.envoyer(
                config.telegram_bot_token,
                surveillance.telegram_chat_id,
                "✅ <b>Moniteur CROUS rétabli</b> — la surveillance a repris.",
            )
    except requests.RequestException as erreur:
        print(f"❌ Impossible d'envoyer l'alerte de rétablissement : {erreur}")


def boucle(config: Config) -> None:
    conn = etat.ouvrir(config.db_path)
    zones = _resoudre_zones(config)
    print(f"⏱️  Cycle toutes les {config.intervalle_s} s (+ jitter ≤ {config.jitter_s} s)")
    print("-" * 60)

    echecs_consecutifs = 0
    panne_signalee = False
    while True:
        if _un_cycle(config, conn, zones):
            if panne_signalee:
                _alerter_retablissement(config)
                panne_signalee = False
            echecs_consecutifs = 0
        else:
            echecs_consecutifs += 1
            if echecs_consecutifs >= config.echecs_avant_alerte and not panne_signalee:
                _alerter_panne(config, echecs_consecutifs)
                panne_signalee = True
        time.sleep(config.intervalle_s + random.uniform(0, config.jitter_s))


def une_fois(config: Config) -> int:
    conn = etat.ouvrir(config.db_path)
    zones = _resoudre_zones(config)
    return 0 if _un_cycle(config, conn, zones) else 1


def main() -> None:
    config = charger_config()
    print("🔍 Moniteur de logements CROUS")
    if "--once" in sys.argv:
        raise SystemExit(une_fois(config))
    try:
        boucle(config)
    except KeyboardInterrupt:
        print("\n⚠️  Arrêt demandé par l'utilisateur.")


if __name__ == "__main__":
    main()
