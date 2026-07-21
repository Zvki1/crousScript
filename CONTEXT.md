# CROUS Monitor

Surveillance des logements CROUS sur trouverunlogement.lescrous.fr : alerte l'utilisateur dès qu'une annonce devient disponible dans la ville qu'il a choisie. Générique par ville (cas d'usage initial : Lyon).

## Language

**Annonce** :
Un logement publié sur trouverunlogement.lescrous.fr, identifié de façon unique par son ID CROUS.
_Éviter_ : logement (ambigu : désigne le bien physique), offre, résultat

**Nouvelle annonce** :
Une annonce jamais vue auparavant, OU une annonce réapparue (voir Réapparition). Toute nouvelle annonce déclenche une alerte — même si le nombre total d'annonces ne change pas.
_Éviter_ : nouveau logement

**Réapparition** :
Une annonce déjà vue qui redevient visible après avoir disparu (ex. : annulation d'une réservation). Traitée comme une nouvelle annonce.

**Zone de surveillance** :
La bounding box de la commune choisie (géocodée depuis son nom), élargie d'une marge configurable (défaut ~5 km) pour couvrir les campus périphériques. C'est la zone envoyée à la recherche CROUS.
_Éviter_ : ville (la zone déborde la commune), bounds

**Surveillance** :
L'association d'une zone de surveillance et d'un canal de notification, pour le compte d'un utilisateur. Le moniteur exécute une liste de surveillances ; en v1 cette liste n'a qu'un élément.
_Éviter_ : recherche, alerte (une alerte est le message émis, pas la configuration)

**Alerte** :
Le message envoyé sur le canal de notification quand une nouvelle annonce apparaît dans une zone de surveillance.
_Éviter_ : notification (ambigu avec le canal)

**Annonce vue** :
Une annonce présente dans l'état mémorisé du moniteur, pour laquelle une alerte a déjà été envoyée et qui n'a pas disparu depuis.

**Canal de notification** :
Le moyen par lequel l'utilisateur d'une surveillance reçoit ses alertes.

**Cycle de vérification** :
Une interrogation du CROUS pour une zone de surveillance, suivie de la comparaison avec les annonces vues et de l'émission des alertes.
_Éviter_ : scan, check, polling

**Outil de recherche** :
Une campagne de logement CROUS (ex. « Fil de l'Eau », « Phase complémentaire »), identifiée par un `idTool` côté API. Plusieurs outils sont actifs en parallèle et s'ouvrent/expirent au fil de l'année ; le moniteur interroge tous ceux actifs au moment du cycle (voir docs/adr/0003).
_Éviter_ : tool, campagne (réservé au vocabulaire CROUS, pas au nôtre)
