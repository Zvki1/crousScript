# Moniteur de logements CROUS

Surveille [trouverunlogement.lescrous.fr](https://trouverunlogement.lescrous.fr) pour une ville donnée et envoie une alerte **Telegram** dès qu'une **nouvelle annonce** apparaît — y compris quand une annonce déjà vue **réapparaît** (annulation de réservation).

- Générique : `CITY=Lyon`, `CITY=Montpellier`… n'importe quelle commune française (géocodage automatique, avec une marge configurable pour couvrir les campus périphériques comme Villeurbanne).
- Fiable : interroge l'API JSON du site (pas de scraping HTML), distingue « erreur » de « zéro annonce », s'auto-signale en panne sur Telegram et via un watchdog externe.
- Vocabulaire du projet : [CONTEXT.md](CONTEXT.md). Décisions d'architecture : [docs/adr/](docs/adr/).

## Configuration

```bash
cp .env.example .env   # puis remplis les valeurs
pip install -r requirements.txt
```

### Créer le bot Telegram (2 minutes)

1. Dans Telegram, parle à [@BotFather](https://t.me/BotFather) → `/newbot` → suis les étapes → copie le **token** dans `TELEGRAM_BOT_TOKEN`.
2. Envoie n'importe quel message à ton nouveau bot (obligatoire, sinon il ne peut pas t'écrire).
3. Ouvre `https://api.telegram.org/bot<TON_TOKEN>/getUpdates` dans le navigateur → repère `"chat":{"id":…}` → copie ce nombre dans `TELEGRAM_CHAT_ID`.

### Watchdog externe (optionnel, recommandé)

Crée un check gratuit sur [healthchecks.io](https://healthchecks.io) (période : 5 min) et colle l'URL de ping dans `HEALTHCHECK_URL`. Si le moniteur (ou le serveur entier) meurt, healthchecks t'alerte de l'extérieur.

## Lancer

```bash
python main.py          # boucle : un cycle toutes les 60 s (+ jitter)
python main.py --once   # un seul cycle puis sortie (mode GitHub Actions)
```

## Déploiement

### Option A — VPS (Oracle Always Free ou autre), 24/7

```bash
sudo tee /etc/systemd/system/crous-monitor.service > /dev/null <<'EOF'
[Unit]
Description=Moniteur logements CROUS
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/home/ubuntu/crousScript
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now crous-monitor
journalctl -u crous-monitor -f   # suivre les logs
```

(Le `.env` est lu automatiquement depuis le répertoire de travail.)

### Option B — GitHub Actions (gratuit, sans serveur)

Le workflow [.github/workflows/moniteur.yml](.github/workflows/moniteur.yml) exécute `--once` par cron et committe l'état (`etat.db`) dans le repo.

1. Dans le repo GitHub : *Settings → Secrets and variables → Actions* → ajoute les secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (et `HEALTHCHECK_URL` si utilisé) ; ajoute les *variables* `CITY` et `MARGIN_KM` si tu ne veux pas les défauts (Lyon, 5 km).
2. Décommente le bloc `schedule:` dans le workflow.
3. Teste avec *Actions → Moniteur CROUS → Run workflow*.

Limite honnête : GitHub peut retarder les crons de 5 à 15 minutes aux heures chargées. Le VPS reste l'option la plus réactive (cycle toutes les 60 s).

## Variables

| Variable | Défaut | Rôle |
|---|---|---|
| `CITY` | — (requis) | Commune à surveiller |
| `MARGIN_KM` | `5` | Marge autour de la commune |
| `TELEGRAM_BOT_TOKEN` | — (requis) | Token du bot |
| `TELEGRAM_CHAT_ID` | — (requis) | Destinataire des alertes |
| `HEALTHCHECK_URL` | — | Ping healthchecks.io à chaque cycle |
| `CHECK_INTERVAL` | `60` | Secondes entre deux cycles (mode boucle) |
| `JITTER` | `10` | Décalage aléatoire max ajouté à l'intervalle |
| `FAILURES_BEFORE_ALERT` | `5` | Échecs consécutifs avant l'alerte de panne |
| `DB_PATH` | `etat.db` | Fichier SQLite des annonces vues |
| `TOOL_IDS` | — | Épingle des campagnes CROUS précises (ex. `42,47`) ; par défaut, découverte automatique des campagnes actives à chaque cycle |
