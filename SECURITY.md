# Security Policy

La sicurezza in MindOs è parte del core architetturale (policy, trust, sandbox, audit), non un add-on.

## 1. Supported versions

| Version | Supported |
|---|---|
| `main` | Yes |
| release branches | [ASSENTE] |

Nota: al momento la branch `main` è la linea supportata.

## 2. Report di vulnerabilità

Per vulnerabilità reali:

- usa **GitHub Security Advisories** (Private vulnerability reporting) del repository.
- non aprire issue pubbliche con dettagli exploitabili.

Per problemi non sensibili:

- apri issue pubblica con label `security`.

## 3. Cosa includere nel report

- Descrizione sintetica del rischio.
- Impatto atteso (confidenzialità/integrità/disponibilità).
- Componenti/file coinvolti.
- Passi riproducibili.
- Proof of concept minima.
- Mitigazioni temporanee suggerite.

## 4. SLA di risposta target

- Ack iniziale: entro 72 ore.
- Triaging: entro 7 giorni.
- Patch iniziale: best effort in base a severità.

## 5. Ambiti ad alta criticità

- `core/orchestrator/**`
- `core/plugin/trust.py`
- `core/plugin/manager.py`
- `core/plugin/program_plugin.py`
- `runtime.env.json` (`policy.*`)
- `scripts/install_os.ps1`

## 6. Classi di vulnerabilità prioritarie

- Bypass ACL/capability gating.
- Bypass trust/signature verification.
- Esecuzione programma fuori sandbox policy.
- Escalation tramite program registry esterno.
- Corruzione audit/event log.
- RCE tramite payload plugin/program.

## 7. Disclosure policy

- Coordinated disclosure.
- Niente PoC pubblica prima del fix.
- Advisory pubblica dopo remediation e validazione.

## 8. Hardening raccomandato in produzione

- Rotazione `signer_keys`.
- Gestione segreti fuori repo.
- Branch protection su `main`.
- Required checks CI/preflight.
- Restrizioni su chi può fare merge in aree critiche.
