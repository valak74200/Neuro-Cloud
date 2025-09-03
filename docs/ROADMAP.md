# Roadmap Neuro-Cloud (Mobile only)

Cette roadmap est le fil rouge du projet. Chaque item possède un ID unique (NC-XXXX). La CI coche automatiquement les cases lorsque les tests associés passent (voir `.github/workflows/ci.yml` et `scripts/update_progress.py`).

## Légende

- [ ] À faire
- [~] En cours
- [x] Fait (validé par tests)

---

## 0. Fondations du repo

- [x] NC-0001 Créer README (vision, DDD, cas d’usage mobiles, SLO) — tests: n/a
- [x] NC-0002 Règles `.cursor/rules/rules.mdc` complètes (mobile) — tests: n/a
- [x] NC-0003 CHANGELOG & templates issues/PR/MR — tests: n/a
- [x] NC-0004 Licence (MIT/Apache-2.0) — tests: n/a
- [x] NC-0005 CONTRIBUTING.md (workflow, DDD, tests, CI) — tests: n/a
- [x] NC-0006 CODE_OF_CONDUCT.md — tests: n/a
- [x] NC-0007 Hooks pre-commit (lint + tests rapides) — tests: `test_precommit_hooks.py`
- [x] NC-0008 Environnements `.env` + docs secrets — tests: n/a
- [x] NC-0009 Docker compose (PostgreSQL, Qdrant/Weaviate, MinIO) — tests: `test_docker_local.py`
- [x] NC-0010 Documentation API (Swagger/OpenAPI) — tests: `test_openapi_schema.py`

---

## 1. Backend API & Domaine (FastAPI, DDD)

### 1.1 Modèle de domaine

- [x] NC-1001 Squelette FastAPI + /healthz — tests: `test_healthz.py`
- [x] NC-1002 Entité `Memory` + tests unitaires — tests: `test_memory_domain.py`
- [x] NC-1003 Service `SaveMemoryService` + repo mémoire — tests: `test_api_memories.py`
- [x] NC-1004 Entité `TranscriptSegment` (audio segment) — tests: `test_transcript_segment.py`
- [x] NC-1005 Entité `CaptureSession` — tests: `test_capture_session.py`
- [x] NC-1006 Entité `Participant` — tests: `test_participant.py`
- [x] NC-1007 Entité `ConsentRecord` — tests: `test_consent_record.py`
- [x] NC-1008 Entité `Tag` & `ImportanceScore` — tests: `test_tag_importance.py`
- [x] NC-1009 Entité `RetentionPolicy` — tests: `test_retention_policy.py`
- [x] NC-1010 Entité `RecallCard` — tests: `test_recall_card.py`
- [x] NC-1011 Repositories (interfaces) pour toutes les entités — tests: `test_repositories_contracts.py`

### 1.2 Services d’application (use cases)

- [x] NC-1101 `StartSession` / `EndSession` — tests: `test_session_service.py`
- [x] NC-1102 `RecordSegment` (ingestion audio chunk) — tests: `test_record_segment_service.py`
- [x] NC-1103 `TranscribeSegment` (asynchrone) — tests: `test_transcribe_service.py`
- [x] NC-1104 `DiarizeSession` (serveur) — tests: `test_diarization_service.py`
- [x] NC-1105 `SummarizeSession` (LLM) — tests: `test_summarize_service.py`
- [x] NC-1106 `GenerateActionItems` — tests: `test_action_items_service.py`
- [x] NC-1107 `IndexEmbeddings` — tests: `test_index_embeddings_service.py`
- [x] NC-1108 `SearchMemories` (RAG, filtres) — tests: `test_search_service.py`
- [x] NC-1109 `ProactiveRecall` (scheduler) — tests: `test_proactive_recall_service.py`
- [x] NC-1110 `PurgeData` + `ExportData` — tests: `test_data_lifecycle_service.py`
- [x] NC-1111 `RequestConsent` + `StoreConsentRecord` — tests: `test_consent_service.py`

### 1.3 Adapters & infrastructure

- [x] NC-1201 Postgres repositories (SQLAlchemy/Alembic) — tests: `test_repo_postgres.py`
- [ ] NC-1202 Vector DB adapter (Qdrant/Weaviate) — tests: `test_vector_adapter.py`
- [ ] NC-1203 Storage audio (S3/MinIO) — tests: `test_storage_audio.py`
- [ ] NC-1204 Whisper adapter (faster‑whisper serveur) — tests: `test_whisper_adapter.py`
- [ ] NC-1205 Embeddings provider (OpenAI/alt UE) + cache — tests: `test_embeddings_provider.py`
- [ ] NC-1206 LLM summarizer (OpenAI) + fallback — tests: `test_llm_summarizer.py`
- [ ] NC-1207 Auth Supabase (validation JWT) — tests: `test_auth_supabase.py`
- [ ] NC-1208 Observabilité (logs, traces, métriques) — tests: `test_observability.py`
- [ ] NC-1209 Rate limiting / quotas — tests: `test_rate_limits.py`

### 1.4 API REST

- [ ] NC-1301 `POST /api/v1/memories` (créé) + `GET /memories` — tests: `test_api_memories_list.py`
- [ ] NC-1302 Sessions: `POST /sessions` `POST /sessions/{id}/end` `GET /sessions` — tests: `test_api_sessions.py`
- [ ] NC-1303 Segments: `POST /segments` (upload) `GET /sessions/{id}/segments` — tests: `test_api_segments.py`
- [ ] NC-1304 Recherche: `GET /search` (q, filtres, pagination) — tests: `test_api_search.py`
- [ ] NC-1305 Consentement: `POST /consents` `GET /consents` — tests: `test_api_consents.py`
- [ ] NC-1306 Rappels: `GET /recall/feed` — tests: `test_api_recall.py`
- [ ] NC-1307 Export/Suppression: `POST /export` `POST /purge` — tests: `test_api_data_lifecycle.py`

---

## 2. Application Mobile (Expo, TypeScript)

### 2.1 Socle app

- [ ] NC-2001 Projet Expo TS + navigation — tests: Detox `app_boot.e2e.ts`
- [ ] NC-2002 Onboarding & permissions (micro, notifications) — tests: Detox `permissions.e2e.ts`
- [ ] NC-2003 Auth Supabase (email/magic link) — tests: Detox `auth.e2e.ts`
- [ ] NC-2004 State mgmt & config (beep, rétention, langue) — tests: unit `config_store.test.ts`

### 2.2 Capture audio (smart‑active)

- [ ] NC-2101 Push‑to‑talk (UI + envoi `POST /memories`) — tests: Detox `ptt_create_memory.e2e.ts`
- [ ] NC-2102 Hotword on‑device (openWakeWord/Porcupine) + seuils — tests: unit `hotword.test.ts`
- [ ] NC-2103 VAD opportuniste (WebRTC VAD) + tampon 30–60s — tests: unit `vad.test.ts`
- [ ] NC-2104 Auto‑réunion (calendrier) + déclenchement — tests: Detox `auto_meeting.e2e.ts`
- [ ] NC-2105 Foreground Service Android + notification — tests: Detox `foreground_service.e2e.ts`
- [ ] NC-2106 Indicateurs UI (recording badge, beep) — tests: Detox `recording_indicator.e2e.ts`

### 2.3 Pipeline client

- [ ] NC-2201 Encodage audio (Opus 16k) + compression — tests: unit `audio_encode.test.ts`
- [ ] NC-2202 File offline chiffrée + reprise réseau — tests: unit `offline_queue.test.ts`
- [ ] NC-2203 Uploader résilient (retry/backoff, Wi‑Fi prioritaire) — tests: unit `uploader.test.ts`
- [ ] NC-2204 Chiffrement local (Keychain/Keystore) — tests: unit `crypto_store.test.ts`

### 2.4 UI & Recherche

- [ ] NC-2301 Timeline souvenirs (list + filtres) — tests: Detox `timeline.e2e.ts`
- [ ] NC-2302 Détail `Memory` (transcript, résumé, actions) — tests: Detox `memory_detail.e2e.ts`
- [ ] NC-2303 Recherche sémantique + filtres — tests: Detox `search.e2e.ts`
- [ ] NC-2304 Rappels (feed « À retenir aujourd’hui ») — tests: Detox `recall_feed.e2e.ts`
- [ ] NC-2305 Export/partage (PDF/Markdown) — tests: Detox `export_share.e2e.ts`

### 2.5 Paramètres & Accessibilité

- [ ] NC-2401 Paramètres d’écoute (hotword/VAD/auto‑réunion) — tests: Detox `settings_listening.e2e.ts`
- [ ] NC-2402 Langue & traduction — tests: unit `i18n.test.ts`
- [ ] NC-2403 Accessibilité (voice-over, contrastes, haptique) — tests: manual + Detox `a11y.e2e.ts`
- [ ] NC-2404 Widgets (push‑to‑talk) — tests: manual `widgets.md`

---

## 3. Consentement & RGPD

- [ ] NC-3001 Modèle `ConsentRecord` + API — tests: `test_consent_domain.py`, `test_api_consents.py`
- [ ] NC-3002 Flux d’acceptation in‑app + beep + journal — tests: Detox `consent_flow.e2e.ts`
- [ ] NC-3003 Redaction PII basique (emails, numéros) — tests: `test_pii_redaction.py`
- [ ] NC-3004 Export/Suppression utilisateur (RGPD) — tests: `test_gdpr_portability_erasure.py`
- [ ] NC-3005 Résidence UE (config) + DPIA docs — tests: n/a

---

## 4. Observabilité & SLO

- [ ] NC-4001 Logs structurés + corrélation requêtes — tests: `test_logging.py`
- [ ] NC-4002 Métriques clés (latence transcription, taux rappel) — tests: `test_metrics_collector.py`
- [ ] NC-4003 Tableaux de bord (dev/staging) — tests: n/a
- [ ] NC-4004 Alerting erreurs — tests: `test_alerting_hook.py`

---

## 5. Sécurité

- [ ] NC-5001 Gestion secrets (.env, Vault/Doppler) — tests: `test_secrets_loading.py`
- [ ] NC-5002 Chiffrement au repos (AES‑256) côté serveur — tests: `test_storage_encryption.py`
- [ ] NC-5003 E2EE (optionnelle) design & POC — tests: `test_e2ee_poc.py`
- [ ] NC-5004 AuthZ basique (propriétaire ressource) — tests: `test_authorization.py`
- [ ] NC-5005 Scans sécurité (pip-audit, npm audit) CI — tests: job ci `security`

---

## 6. Qualité & Tests

- [ ] NC-6001 Lint/format Python & JS/TS (CI) — tests: job ci `lint`
- [ ] NC-6002 Unit & intégration backend (≥ 80% cov) — tests: job ci `test`
- [ ] NC-6003 E2E mobile Detox scénarios critiques — tests: job ci `e2e`
- [ ] NC-6004 Jeux d’or pertinence (RAG) + évaluation — tests: `test_rag_relevance.py`

---

## 7. Build & Déploiement

- [ ] NC-7001 Build backend (container) + staging — tests: job ci `build_backend`
- [ ] NC-7002 Backend déployé (Render/Heroku) — tests: smoke `test_deploy_backend.py`
- [ ] NC-7003 Build Expo EAS (iOS/Android) — tests: job ci `build_mobile`
- [ ] NC-7004 Canaux release (alpha/beta/prod) — tests: n/a

---

## 8. Lancement & Conformité Stores

- [ ] NC-8001 Privacy labels & App Tracking transparency — tests: n/a
- [ ] NC-8002 Justifications background (Android/iOS) — tests: n/a
- [ ] NC-8003 Pages Store (captions, screenshots) — tests: n/a
- [ ] NC-8004 Beta TestFlight / Play internal — tests: n/a

---

## 9. Pro

- [ ] NC-9001 Bot notetaker serveur (Zoom/Meet/Teams) — tests: `test_bot_notetaker.py`
- [ ] NC-9002 Intégrations Calendrier avancées — tests: `test_calendar_integration.py`
- [ ] NC-9003 Abonnements & facturation (Stripe) — tests: `test_billing.py`
- [ ] NC-9004 Espaces d’équipe & rôles — tests: `test_teams_roles.py`

---

## Règles d’auto-validation

- Chaque tâche mappée à un ou plusieurs tests. Si tous passent sur `main`, la CI remplace `- [ ]` par `- [x]` pour l’ID correspondant.
- Les tâches sans tests n’autocochent pas; elles restent manuelles.
- Ajouter le mapping dans `scripts/update_progress.py` au fur et à mesure des nouveaux tests.
