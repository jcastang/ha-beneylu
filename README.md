# Beneylu School pour Home Assistant

Intégration personnalisée **non officielle**, en lecture seule, basée sur les routes API de [hclaria/beneylu-mcp](https://github.com/hclaria/beneylu-mcp). Ne nécessite aucun serveur MCP.

**Statut : bêta, couverture étendue de l'API** — tests unitaires disponibles, mais pas encore validée sur un compte Beneylu réel.

## Fonctionnalités

- Config Flow avec identifiants parent ou refresh token
- Authentification, renouvellement de session et rafraîchissement configurable (10–180 min, 30 min par défaut)
- Appareil famille et un appareil par enfant
- Capteurs : mots du cahier, signatures en attente, messages non lus, notifications
- Capteurs binaires de signature à effectuer
- Événements `beneylu_post_changed` et `beneylu_notification_changed`, ainsi que des entités event
- **Contenu lisible** des mots du cahier et notifications : capteurs `Dernier mot` et `Dernière notification`, attribut `text` complet, historique récent en attribut `latest` (10 entrées) ; un capteur `Dernier mot` par enfant\n- Les messages privés restent comptabilisés mais leur contenu n'est pas récupéré automatiquement pour éviter de les marquer lus
- Exemple de tableau de bord Lovelace dans `dashboard/beneylu.yaml`

## Couverture de l'API hclaria/beneylu-mcp

| Fonction upstream | Fonction Home Assistant |
| --- | --- |
| `get_account` | Capteur Compte Beneylu, enfants, classes et écoles |
| `list_posts(page)` | Capteur Mots du cahier, texte et métadonnées |
| `get_post(post_id)` | Action `beneylu.get_post` avec réponse détaillée |
| `get_notifications(limit)` | Capteur Notifications, texte et lien |
| `list_conversations` | Capteurs Conversations et Dernière conversation (liste seulement) |
| `get_conversation(conversation_id)` | Action explicite `beneylu.read_conversation` (risque de marquer lu) |
| `whats_new` | Détection périodique des changements et événements Home Assistant |
| `ack(cursor)` | Non exposé : `ack` concerne le stockage local du serveur MCP, pas Beneylu |
| `pending` | Non exposé : les événements HA ne garantissent pas la livraison de bout en bout |

Les mots contiennent auteur, classes, enfants, texte, signatures, pièces jointes (nombre et identifiants), possibilité de réponse, lien et date. Les conversations sont listées sans ouverture des messages.

Les actions `beneylu.get_post` et `beneylu.read_conversation` renvoient une réponse utilisable avec `response_variable` dans un script Home Assistant. L'action `read_conversation` n'est **jamais appelée automatiquement**.

Exemple d'action à la demande :

```yaml
action: beneylu.read_conversation
data:
  conversation_id: "ID_DE_LA_CONVERSATION"
response_variable: beneylu_messages
```

## Lire le contenu dans Home Assistant

- Le capteur **Dernier mot** affiche les 250 premiers caractères comme état (limite Home Assistant : 255), et le texte intégral dans l'attribut `text`.
- Le capteur **Dernière notification** fonctionne de la même manière.
- Les capteurs **Mots du cahier** et **Notifications** exposent les 10 derniers éléments avec leur texte dans l'attribut `latest`.
- Le tableau de bord `dashboard/beneylu.yaml` affiche les mots et notifications **sans tronquer le texte**.
- Le contenu des conversations privées n'est pas lu automatiquement : l'API de consultation peut marquer les messages comme lus.

Les contenus apparaissent dans les attributs des entités et dans le tableau de bord. Ils ne sont pas conservés dans une base séparée par l'intégration, mais Home Assistant peut les enregistrer dans son historique : sécuriser l'accès aux sauvegardes.

## Installation HACS

1. Dans HACS, ajouter `https://github.com/jcastang/ha-beneylu` comme **dépôt personnalisé**, type **Integration**.
2. Installer **Beneylu School**.
3. Redémarrer Home Assistant.
4. Paramètres → Appareils et services → Ajouter une intégration → **Beneylu School**.
5. Fournir identifiant/mot de passe parent ou refresh token.

## Installation manuelle

Copier `custom_components/beneylu` dans `<config>/custom_components/beneylu`, redémarrer Home Assistant, puis ajouter l'intégration.

## Tableau de bord

Le fichier `dashboard/beneylu.yaml` fournit une vue Lovelace sans cartes tierces. Adapter les identifiants d'entité à ceux générés par Home Assistant.

## Exemple d'automatisation

```yaml
alias: Beneylu - nouveau mot
triggers:
  - trigger: event
    event_type: beneylu_post_changed
actions:
  - action: persistent_notification.create
    data:
      title: "Beneylu : cahier de liaison"
      message: "{{ trigger.event.data.text }}"
mode: queued
```

## Tests

```bash
python -m pip install -r requirements-test.txt
pytest -q
python -m compileall -q custom_components
```

## Limites connues

- Pas d'API publique Beneylu : les routes internes peuvent changer.
- Les mots sont récupérés sur les cinq premières pages (jusqu'à environ 50 mots) ; le compteur ne couvre pas forcément l'ensemble du compte.
- Les notifications ne sont pas ventilées par enfant.
- Les nouveaux enfants nécessitent un rechargement de l'intégration pour créer leurs entités.
- La première collecte est une référence, sans événements historiques ; détection par comparaison de deux collectes, sans garantie de livraison de notifications.
- Le contenu des conversations est disponible **uniquement à la demande** via une action qui peut marquer les messages comme lus côté école.
- La rotation du refresh token est conservée en mémoire, pas persistée après redémarrage.
- Captcha et double authentification OTP non automatisés.
- Éviter les tableaux de bord partagés et protéger les sauvegardes Home Assistant qui contiennent les identifiants.
- Tests à exécuter sur une véritable instance Home Assistant et un compte Beneylu.

## Crédits

Inspiré du comportement API de [hclaria/beneylu-mcp](https://github.com/hclaria/beneylu-mcp). Aucune affiliation avec Beneylu.
