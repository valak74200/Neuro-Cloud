# Neuro-Cloud — Mémoire personnelle augmentée par l’IA (Mobile)

Neuro-Cloud est une application mobile qui capture, transcrit, résume et indexe vos souvenirs (audio/texte) pour permettre une recherche sémantique et un rappel proactif. L’objectif est de servir à la fois le grand public et les professionnels, avec un fort accent sur la confidentialité, la conformité et l’ergonomie.

> Mobile-only: l’application cible iOS et Android. Les limitations OS (micro en arrière-plan, capture d’autres apps) sont prises en compte via des modes d’écoute « smart‑active » (déclenchement par contexte/consentement) et non « always-on » illimitée.

---

## Sommaire

- [Pourquoi Neuro-Cloud ?](#pourquoi-neuro-cloud-)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Cas d’usage couverts (mobile)](#cas-dusage-couverts-mobile)
- [Architecture (DDD, Clean Architecture)](#architecture-ddd-clean-architecture)
- [Structure du dépôt (monorepo)](#structure-du-dépôt-monorepo)
- [Stack technique](#stack-technique)
- [Sécurité, RGPD et consentement](#sécurité-rgpd-et-consentement)
- [Performances, SLO et coûts](#performances-slo-et-coûts)
- [Démarrage rapide (non‑dev)](#démarrage-rapide-non-dev)
- [Démarrage développeur](#démarrage-développeur)
- [Tests & Qualité](#tests--qualité)
- [CI/CD](#cicd)
- [Roadmap MVP](#roadmap-mvp)
- [Contribution](#contribution)
- [Changelog & Licence](#changelog--licence)

---

## Pourquoi Neuro-Cloud ?

- Retenir l’essentiel de vos réunions, conversations, cours, idées.
- Rechercher intelligemment dans vos souvenirs (sémantique, tags, contexte, récence).
- Être rappelé proactivement des points importants au bon moment.
- Respecter votre vie privée (consentement, chiffrement, résidence UE, suppression à la demande).

---

## Fonctionnalités principales

- Capture audio/texte (mobile) avec modes d’écoute « smart‑active »:
  - Auto‑réunion (calendrier)
  - Hotword on‑device (déclenchement local)
  - VAD opportuniste (tampon 30–60s)
  - Manuel (push‑to‑talk, widget, watch)
- Transcription (Whisper / faster‑whisper), multilingue, diarisation serveur.
- Résumés et action items, chapitrage, mots‑clés.
- Indexation d’embeddings, recherche sémantique, filtres (tags, période, source).
- Rappels proactifs (importance × récence), cartes de rappel (« RecallCard »).
- Sécurité: chiffrement au repos/en transit, clés locales, politiques de rétention.

---

## Cas d’usage couverts (mobile)

- Réunions visioconf (Zoom/Meet/Teams) depuis mobile: capture micro local + bot notetaker serveur (rejoint la réunion via API) avec consentement.
- Réunions présentielles (salle): micro device/BT + VAD + tampon + diarisation serveur.
- Conversations impromptues 1:1: hotword ou push‑to‑talk + consentement rapide.
- Monologue / mémo perso: push‑to‑talk, transcription locale si possible.
- Cours / conférences longues: sessions segmentées (15–30 min), upload différé.
- Appels téléphoniques: iOS interdit l’enregistrement natif → pont d’appel serveur (opt‑in) ou récap post‑appel guidé; Android restreint selon région/OEM.
- Mode hors‑ligne: file locale chiffrée + reprise réseau; Whisper local quand possible.
- Environnements bruyants: RNNoise/suppression de bruit, VAD adaptatif.

Critères d’acceptation clés:

- Latence transcription par segment < 30s; résumé fin de réunion < 2 min
- Faux positifs hotword ≤ 1/jour; F1 VAD ≥ 0.90 bureau
- Couverture tests ≥ 80%

---

## Architecture (DDD, Clean Architecture)

Le projet suit Domain‑Driven Design et Clean Architecture. Pas de logique métier dans les contrôleurs ni l’infrastructure.

```mermaid
graph TD
    subgraph Mobile App (iOS/Android)
        UI[Interfaces: React Native Expo]
        Listeners[Smart‑Active Listeners: Auto‑réunion / Hotword / VAD / Manuel]
        UI --> Listeners
    end

    subgraph Backend (FastAPI)
        AppSvc[Application Services]
        Domain[Domain (Entités, Aggregates, VOs, Domain Services)]
        Repos[Ports: Repository Interfaces]
        Impl[Adapters: Infra Implementations]
        AppSvc --> Domain
        AppSvc --> Repos
        Repos --> Impl
    end

    subgraph Data Stores
        PG[(PostgreSQL)]
        VDB[(Qdrant / Weaviate)]
        Files[(Stockage chiffré: Audio/Blobs)]
    end

    subgraph AI Providers
        Whisper[Whisper / faster‑whisper]
        Emb[Embeddings]
        LLM[LLM]
    end

    Listeners -->|Segments audio| AppSvc
    AppSvc -->|Transcribe| Whisper
    AppSvc -->|Embeddings| Emb
    AppSvc -->|Summarize| LLM
    Impl --> PG
    Impl --> VDB
    Impl --> Files
```

Modèle DDD de référence (mobile):

- Domain: `Memory`, `CaptureSession`, `TranscriptSegment`, `Participant`, `ConsentRecord`, `ImportanceScore`, `RetentionPolicy`, `RecallCard`, `Tag`.
- Application: `StartPassiveListening`, `RequestConsent`, `RecordSegment`, `Transcribe`, `Summarize`, `IndexEmbeddings`, `SearchMemories`, `ProactiveRecall`, `PurgeData`.
- Infrastructure: VAD (WebRTC/Silero), Hotword (openWakeWord/Porcupine), Transcription (Whisper/faster‑whisper), Diarisation (pyannote), Embeddings (OpenAI/UE), Vector DB (Qdrant/Weaviate), Stockage chiffré, Intégrations Calendrier/Zoom/Teams.

---

## Structure du dépôt (monorepo)

Proposition alignée avec les règles du projet:

```
/neuro-cloud
  /apps
    /backend          # API FastAPI
    /mobile           # App React Native (Expo)
  /packages
    /domain           # logique métier pure (DDD)
    /application      # use cases / services d’application
    /infrastructure   # DB, IA, APIs externes, persistance
    /shared           # types, utils, config
  /tests
    /unit
    /integration
    /e2e
  /.cursor/rules     # règles du dépôt (contrat de contribution)
  README.md
  CHANGELOG.md
```

---

## Stack technique

- Mobile: React Native (Expo), Foreground Service Android, UI consentement, widgets push‑to‑talk, notifications.
- Backend: Python FastAPI (Swagger/OpenAPI), HTTPX pour tests d’intégration.
- Base de données: PostgreSQL (rel.), Qdrant/Weaviate (vectorielle), stockage fichiers chiffrés.
- IA: Whisper/faster‑whisper (transcription), OpenAI ou alternative UE (embeddings), LLM (OpenAI/GPT).
- Authentification: Supabase Auth.
- Observabilité: télémétrie anonymisée, santé pipeline, alertes.

---

## Sécurité, RGPD et consentement

- Consentement explicite: bannière, beep configurable, annonce vocale, journal `ConsentRecord` horodaté par session/participant.
- RGPD: chiffrement en transit (TLS) et au repos (AES‑256), clés dans Keychain/Keystore, résidence UE, export/suppression des données, politiques de rétention.
- PII: redaction/masquage optionnels; séparation audio/texte vs embeddings.
- Secrets: `.env` (jamais en dur); gestionnaire de secrets recommandé.

---

## Performances, SLO et coûts

- SLO: transcription < 30s/segment, résumé < 2 min fin réunion, faux positifs hotword ≤ 1/jour, F1 VAD ≥ 0.90, couverture tests ≥ 80%.
- Batterie/Data: éviter streaming continu; VAD + tampon 30–60s; upload Wi‑Fi prioritaire; codecs efficaces (Opus 16k). CPU moyen < 5% hors capture, < 15% en capture.
- Coûts: on‑device d’abord (VAD, hotword, Whisper tiny/base quand possible), batch côté serveur, cache embeddings, budgets par utilisateur, fallback provider.

---

## Démarrage rapide (non‑dev)

1. Installer l’app (iOS/Android) — à venir (TestFlight/Play Store privé).
2. Se connecter (Supabase Auth).
3. Autoriser micro et activer les modes d’écoute souhaités.
4. Lancer une réunion ou utiliser le push‑to‑talk.
5. Consulter les résumés et rechercher vos souvenirs.

---

## Démarrage développeur

Prérequis:

- Node.js 18+ (recommandé), npm 9+ ou pnpm 8+
- Python 3.11+
- Docker (pour PostgreSQL et Qdrant/Weaviate en local)
- OpenAI key (ou alternative) si nécessaire pour embeddings/LLM

Services locaux (suggestion rapide):

```bash
# PostgreSQL
docker run --name nc-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15

# Qdrant (vector DB)
docker run --name nc-qdrant -p 6333:6333 -d qdrant/qdrant:latest
```

Variables d’environnement (exemple):

```bash
# Backend
export NC_ENV=dev
export NC_POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/postgres
export NC_VECTORDB_URL=http://localhost:6333
export NC_OPENAI_API_KEY=sk-...
export NC_STORAGE_DIR=.data/storage

# Mobile (Expo)
export EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

Installation (proposition cible monorepo):

```bash
# Mobile
cd apps/mobile
npm install
npx expo start

# Backend
cd apps/backend
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt  # ou poetry install
uvicorn app.main:app --reload --port 8000
```

> Note: la structure exacte du dépôt (apps/, packages/, etc.) suivra le modèle décrit dans `.cursor/rules/rules.mdc`. Les scripts Make/Task viendront standardiser ces commandes.

---

## Tests & Qualité

- Python: Pytest (unit), HTTPX (intégration), coverage ≥ 80%.
- Mobile E2E: Detox.
- Lint/Format: Black, Flake8, isort, mypy (Python) ; ESLint + Prettier (JS/TS).
- Audit sécurité: `pip-audit`, `npm audit`.

Exemples:

```bash
# Backend
pytest -q --maxfail=1 --disable-warnings --cov=app

# Mobile
npm run lint
# E2E mobile
# Voir script Detox une fois l’app mobile scaffolder
```

---

## CI/CD

- Git flow: main (stable), develop (intégration), feature/\*.
- CI GitHub Actions: lint + tests unitaires + intégration + build.
- CD: backend (Render/Heroku), mobile (Expo EAS). Gate sur tests et qualité.

---

## Roadmap MVP

1. v1 — Auto‑réunion (calendrier), VAD + tampon, transcription, résumé, indexation, recherche, rappel « À retenir aujourd’hui ».
2. v1.1 — Hotword + capture courte; journaux de consentement; redaction PII basique.
3. v1.2 — Bot notetaker serveur pour visioconf; réglages pro (rétention, budgets, rôles).

---

## Contribution

- Issues: user story + critères d’acceptation + cas de test.
- PR: petite portée, tests inclus, doc mise à jour.
- Commits: Conventional Commits.
- Hooks: pre-commit pour lint/tests rapides.

---

## Changelog & Licence

- Voir `CHANGELOG.md` (SemVer: MAJOR.MINOR.PATCH).
- Licence: à définir (MIT/Apache-2.0, selon objectifs commerciaux et contributions).

---

## Références & Règles du dépôt

- Les règles détaillées (DDD, cas d’usage mobiles, sécurité, tests) sont dans `/.cursor/rules/rules.mdc`. Elles sont contraignantes et doivent être respectées pour toute contribution.
