## Contribuer à Neuro-Cloud

Merci de votre intérêt pour Neuro-Cloud. Ce projet suit Domain-Driven Design (DDD), Clean Architecture, TDD, et une CI/CD stricte.

### Pré-requis

- Python 3.11.9
- Node 18 (pour Prettier via pre-commit)
- Docker & Docker Compose
- pre-commit installé: `pip install pre-commit`

### Installation rapide (backend)

```bash
cd apps/backend
python -m venv .venv && . .venv/bin/activate
pip install -U pip -r requirements.txt
export PYTHONPATH=.
pytest -q
```

### Lint & format

- Hooks: Black, Flake8, isort, Prettier

```bash
pre-commit install
pre-commit run --all-files
```

### Tests

- Unitaire + intégration via Pytest
- E2E (mobile) prévu via Detox

```bash
cd apps/backend && . .venv/bin/activate && PYTHONPATH=. pytest -q
```

### Git flow

- Branches: `main` (stable), `develop` (intégration), `feature/*`
- Commits: Conventional Commits (ex: `feat: ...`, `fix: ...`, `docs: ...`)
- PR: tests verts + lint OK + description claire (User story, AC, notes techniques)

### DDD / Clean Architecture

- `domain/`: entités, value objects, services métier (pur)
- `application/`: cas d’usage (orchestration)
- `infrastructure/`: DB, IA, API externes
- `interfaces/`: API REST/GraphQL, UI

### Sécurité & RGPD

- Jamais de secrets en dur, utiliser `.env`
- Chiffrement en transit (TLS) et au repos
- Respect du consentement et des lois locales

### Roadmap & CI

- La CI met à jour `docs/ROADMAP.md` selon les tests passés
- Chaque test correspond à un ID `NC-xxxx`

### Questions

Ouvrez une Issue avec le template fourni ou discutez dans une PR.
