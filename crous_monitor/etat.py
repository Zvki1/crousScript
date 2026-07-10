"""Mémoire des annonces vues, en SQLite — porte la règle « identité + réapparition » (cf. CONTEXT.md)."""

import sqlite3
from datetime import datetime, timezone

from .crous import Annonce

SCHEMA = """
CREATE TABLE IF NOT EXISTS annonces (
    id            INTEGER NOT NULL,
    surveillance  TEXT    NOT NULL,
    titre         TEXT,
    residence     TEXT,
    prix          TEXT,
    brut          TEXT,
    premiere_vue  TEXT NOT NULL,
    derniere_vue  TEXT NOT NULL,
    disparue_le   TEXT,
    PRIMARY KEY (id, surveillance)
);
"""


def ouvrir(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def comparer(conn: sqlite3.Connection, surveillance: str, annonces: list[Annonce]) -> list[tuple[Annonce, str]]:
    """Compare les annonces du cycle avec les annonces vues.

    Retourne les nouvelles annonces à alerter, chacune avec son motif :
    "nouvelle" (jamais vue) ou "reapparition" (disparue puis revenue).
    Marque au passage les disparitions. Tout est commité en une transaction.
    """
    maintenant = _maintenant()
    ids_actuels = {a.id for a in annonces}
    connues = {
        ligne[0]: ligne[1]
        for ligne in conn.execute(
            "SELECT id, disparue_le FROM annonces WHERE surveillance = ?", (surveillance,)
        )
    }

    a_alerter: list[tuple[Annonce, str]] = []
    for annonce in annonces:
        if annonce.id not in connues:
            a_alerter.append((annonce, "nouvelle"))
            conn.execute(
                "INSERT INTO annonces (id, surveillance, titre, residence, prix, brut, premiere_vue, derniere_vue)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (annonce.id, surveillance, annonce.titre, annonce.residence,
                 annonce.prix, annonce.brut, maintenant, maintenant),
            )
        else:
            if connues[annonce.id] is not None:  # annonce vue, disparue, revenue
                a_alerter.append((annonce, "reapparition"))
            conn.execute(
                "UPDATE annonces SET derniere_vue = ?, disparue_le = NULL, titre = ?, residence = ?, prix = ?, brut = ?"
                " WHERE id = ? AND surveillance = ?",
                (maintenant, annonce.titre, annonce.residence, annonce.prix,
                 annonce.brut, annonce.id, surveillance),
            )

    disparues = [id_ for id_, disparue in connues.items() if disparue is None and id_ not in ids_actuels]
    for id_ in disparues:
        conn.execute(
            "UPDATE annonces SET disparue_le = ? WHERE id = ? AND surveillance = ?",
            (maintenant, id_, surveillance),
        )

    conn.commit()
    return a_alerter
