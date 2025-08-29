# Contribuer à Neuro-Cloud

Merci de contribuer ! Avant toute PR, lisez `/.cursor/rules/rules.mdc` et le `README.md`.

## Principes

- DDD & Clean Architecture: Domain sans dépendances frameworks. Pas de logique métier dans les contrôleurs/adapters.
- TDD: tests unitaires + intégration requis. Couverture ≥ 80%.
- CI verte obligatoire. Lints et formats doivent passer.

## Flux de travail

1. Créez une issue (user story + critères d’acceptation).
2. Branche `feature/<slug>` depuis `develop`.
3. Développez avec tests.
4. Mettez à jour docs/ROADMAP et mapping `scripts/update_progress.py` si nouveaux tests.
5. Ouvrez une PR (template), liez l’issue.

## Standards

- Commits: Conventional Commits.
- Python: Black, Flake8, isort, mypy.
- JS/TS: ESLint + Prettier.
- Secrets: `.env` uniquement.

## Tests

- Unit: Pytest, mocks des externes.
- Intégration: HTTPX, DB/Vector/storages.
- E2E (mobile): Detox.

## Revue

- 2 reviewers si impact >1 couche.
- Vérification: sécurité, RGPD/consentement, performance/batterie.
