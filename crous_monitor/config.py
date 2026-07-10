"""Configuration du moniteur, chargée depuis les variables d'environnement (et un .env optionnel)."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Surveillance:
    """Une zone à surveiller pour le compte d'un utilisateur (cf. CONTEXT.md).

    En v1 le moniteur n'exécute qu'une seule surveillance, mais le cœur
    en accepte une liste — c'est le point d'extension vers le multi-utilisateurs
    (voir docs/adr/0002).
    """

    nom: str  # nom de la ville, sert aussi d'identifiant de la surveillance
    marge_km: float
    telegram_chat_id: str


@dataclass(frozen=True)
class Config:
    surveillances: list
    telegram_bot_token: str
    intervalle_s: int
    jitter_s: int
    echecs_avant_alerte: int
    healthcheck_url: str | None
    db_path: str
    tool_id: int


def _charger_dotenv(chemin: str = ".env") -> None:
    """Charge un fichier .env s'il existe, sans écraser l'environnement existant."""
    fichier = Path(chemin)
    if not fichier.is_file():
        return
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        os.environ.setdefault(cle.strip(), valeur.strip().strip("'\""))


def charger_config() -> Config:
    _charger_dotenv()

    manquantes = [v for v in ("CITY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if not os.environ.get(v)]
    if manquantes:
        raise SystemExit(
            f"❌ Variables d'environnement requises manquantes : {', '.join(manquantes)}\n"
            "   Voir README.md pour la configuration."
        )

    surveillance = Surveillance(
        nom=os.environ["CITY"],
        marge_km=float(os.environ.get("MARGIN_KM", 5)),
        telegram_chat_id=os.environ["TELEGRAM_CHAT_ID"],
    )

    return Config(
        surveillances=[surveillance],
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        intervalle_s=int(os.environ.get("CHECK_INTERVAL", 60)),
        jitter_s=int(os.environ.get("JITTER", 10)),
        echecs_avant_alerte=int(os.environ.get("FAILURES_BEFORE_ALERT", 5)),
        healthcheck_url=os.environ.get("HEALTHCHECK_URL") or None,
        db_path=os.environ.get("DB_PATH", "etat.db"),
        tool_id=int(os.environ.get("TOOL_ID", 41)),
    )
