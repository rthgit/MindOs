# MindOs Roadmap

Roadmap esecutiva ufficiale di MindOs.

Stato aggiornato: 2026-04-18  
Owner: @rthgit

## Principi

- Una sola mente orchestratrice.
- Programmi trattati come plugin.
- Memoria integrata nel core operativo.
- Policy/trust/sandbox obbligatorie.
- Ogni milestone deve avere test e criteri di done verificabili.

## Stato complessivo

- Track Core Platform: `COMPLETATO (v1)`
- Track Governance & Security Baseline: `COMPLETATO (v1)`
- Track Developer/Operator Experience: `PARZIALE`
- Track Production Hardening: `IN CORSO`
- Track Ecosystem & Distribution: `PIANIFICATO`

---

## Fase 1 - Core operativo unificato (COMPLETATO)

### Obiettivo

Confermare un vertical slice reale: boot -> orchestrazione -> plugin -> memoria -> retrieval cross-surface.

### Deliverable

- Orchestratore unico.
- Memory substrate multi-livello.
- Runtime unificato.
- Surface CLI/IDE/Desktop minimale.
- Event log + audit + rollback.

### Done criteria

- E2E stabile con replay consistente.
- Continuita cross-surface verificata.
- CI locale verde.

### Evidenze

- `scripts/ci_local.ps1`
- test E2E e integrazione in `tests/`

---

## Fase 2 - Plugin OS e Programmi cross-platform (COMPLETATO)

### Obiettivo

Gestire allo stesso modo plugin interni e programmi esterni (Windows/Linux).

### Deliverable

- Plugin manager persistente (`install/list/remove/upgrade`).
- Catalogo plugin + catalogo programmi.
- Program wrapper plugin con capability gating.
- Comandi CLI per gestione programmi/plugin.

### Done criteria

- Installazione e run programma via orchestratore.
- Lockfile e stato installazione persistiti.
- Preflight con smoke cycle plugin/program verde.

---

## Fase 3 - Security baseline (COMPLETATO)

### Obiettivo

Bloccare bypass logici su autorizzazioni, trust e runtime execution.

### Deliverable

- ACL user/surface/capability.
- Trust chain: signer + integrity + signature.
- Revoca signer.
- Program sandbox policy (timeout + allowlist real execution).
- SECURITY.md, CODEOWNERS, CONTRIBUTING, LICENSE.

### Done criteria

- Test dedicati trust/revoca/sandbox verdi.
- Policy enforcement verificato su flussi reali.
- Governance pack pubblicato su GitHub.

---

## Fase 4 - Production Hardening (IN CORSO)

### Obiettivo

Portare MindOs da piattaforma funzionale a piattaforma robusta per ambienti reali.

### Work items

1. Signature upgrade: HMAC -> firma asimmetrica (Ed25519/RSA) con key rotation.
2. Registry service enterprise: endpoint autenticati, metadata firmati, policy rollout.
3. Sandboxing hard: isolamento processo/namespace/container dove disponibile.
4. Incident response: audit export, tamper checks, disaster recovery.
5. Release discipline: changelog, versioning policy, migration notes.

### Done criteria

- PKI attiva e testata su plugin/program install.
- Registry remoto con trust end-to-end verificato.
- Hardening tests + failure injection suite.
- Release candidate documentata.

---

## Fase 5 - Ecosystem & Distribution (PIANIFICATO)

### Obiettivo

Scalare oltre il maintainer singolo senza perdere coerenza operativa.

### Work items

1. Marketplace plugin/programmi.
2. Policy packs per team/tenant.
3. Desktop shell completa (plugin/job/memory live).
4. Telemetria operativa e SLO.
5. Installer multi-host (Windows/Linux) con provisioning guidato.

### Done criteria

- Onboarding nuovo plugin esterno senza intervento core.
- Pipeline release plugin/programmi con trust policy enforced.
- UX desktop operativa per uso quotidiano.

---

## Piano 30/60/90

### 0-30 giorni (ALTO)

- Chiudere PKI asimmetrica.
- Definire formato ufficiale registry remoto.
- Introdurre test di regressione security su PR.

### 31-60 giorni (MEDIO)

- Registry service in staging.
- Hard sandbox per classi capability ad alto rischio.
- Incident runbook e export audit.

### 61-90 giorni (MEDIO)

- Marketplace preview.
- Desktop shell avanzata.
- Release candidate pubblico.

---

## Blocchi critici aperti

- Mancanza firma asimmetrica in produzione.
- Registry remoto ancora JSON-oriented (non servizio full enterprise).
- Sandbox kernel-grade non ancora disponibile.

Se uno di questi resta aperto, MindOs rimane in stato `platform-ready` ma non `enterprise-ready`.

---

## Regola operativa finale

Nessuna nuova feature entra in roadmap attiva senza:

- capability definita
- policy definita
- trust model definito
- test minimi definiti
- criterio di done verificabile
