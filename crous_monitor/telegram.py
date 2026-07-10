"""Canal de notification Telegram."""

import requests


def envoyer(bot_token: str, chat_id: str, texte_html: str) -> None:
    reponse = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": texte_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
    reponse.raise_for_status()
