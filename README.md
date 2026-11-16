# Beneylu School pour Home Assistant

Intégration personnalisée **non officielle**, en lecture seule, basée sur les routes API de [hclaria/beneylu-mcp](https://github.com/hclaria/beneylu-mcp). Ne nécessite aucun serveur MCP.

**Statut : v0.1.0 bêta** — tests unitaires disponibles, mais pas encore validée sur un compte Beneylu réel.

## Fonctionnalités

- Config Flow avec identifiants parent ou refresh token
- Authentification, renouvellement de session et rafraîchissement configurable (10–180 min, 30 min par défaut)
- Appareil famille et un appareil par enfant
- Capteurs : mots du cahier, signatures en attente, messages non lus, notifications
- Capteurs binaires de signature à effectuer
- Événements `beneylu_post_changed` et `beneylu_notification_changed`, ainsi que des entités event
- Historique récent exposé en attribut `latest`
- Exemple de tableau de bord Lovelace dans `dashboard/beneylu.yaml`

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
- Ne récupère pas automatiquement les contenus des conversations : cela pourrait les marquer lus côté école.
- La rotation du refresh token est conservée en mémoire, pas persistée après redémarrage.
- Captcha et double authentification OTP non automatisés.
- Éviter les tableaux de bord partagés et protéger les sauvegardes Home Assistant qui contiennent les identifiants.
- Tests à exécuter sur une véritable instance Home Assistant et un compte Beneylu.

## Crédits

Inspiré du comportement API de [hclaria/beneylu-mcp](https://github.com/hclaria/beneylu-mcp). Aucune affiliation avec Beneylu.
