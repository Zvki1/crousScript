# Découverte automatique des outils de recherche CROUS

Le moniteur interrogeait initialement un `idTool` codé en dur (`41`, hérité de l'URL de l'ancien script pour Avignon). Cet outil a expiré silencieusement : `/api/fr/search/41` répond `200 OK` avec `items: []` pour un outil désactivé, exactement comme une vraie absence de logements. Le moniteur a donc tourné plusieurs semaines sans jamais pouvoir détecter d'annonce, sans qu'aucune erreur ne le signale.

Nous interrogeons désormais `/api/fr/tools` à chaque cycle pour obtenir la liste des outils actuellement actifs (`enabled` et non expirés), et nous cherchons des annonces sur chacun d'eux. Le CROUS fait tourner plusieurs campagnes en parallèle (ex. « Fil de l'Eau », campagne continue ; « Phase complémentaire », campagne saisonnière) sous des `idTool` distincts, qui s'ouvrent et expirent au fil de l'année — un identifiant figé est donc voué à repourrir.

Contrepartie assumée : un appel HTTP de plus par cycle. `TOOL_IDS` reste disponible en variable d'environnement pour épingler des outils précis si on veut un jour restreindre la surveillance à une campagne donnée.
