# API JSON du CROUS plutôt que scraping HTML

La première version du moniteur scrapait le HTML de trouverunlogement.lescrous.fr, ce qui confondait « erreur de scraping » et « aucun logement » et cassait à chaque changement de markup. La réécriture interroge directement l'API JSON non documentée qu'utilise le frontend du site (`POST /api/fr/search/41`, zone passée en bounding box) : réponses structurées, identifiants d'annonces fiables, distinction nette entre erreur et résultat vide.

Contrepartie assumée : l'API est non officielle et peut changer ou être restreinte sans préavis. En conséquence, le moniteur reste poli (1 requête/minute avec jitter, User-Agent honnête) et traite tout changement de schéma comme une panne à signaler (alerte Telegram + watchdog), jamais comme « zéro annonce ».
