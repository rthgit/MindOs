# MindOs

MindOs non è un altro strato sopra software scollegati: è un modello operativo in cui sistema, memoria e automazione sono un unico organismo coerente.

L’idea centrale è semplice e radicale:

- esiste una sola mente orchestratrice che interpreta intenti, applica policy e governa l’esecuzione;
- i programmi non sono entità isolate, ma plugin/capability sotto controllo del core;
- ogni azione significativa diventa memoria strutturata (evento, contesto, stato, audit), quindi il sistema ricorda, collega e riusa;
- `desktop`, `cli` e `ide` non sono prodotti separati, ma viste diverse della stessa semantica operativa;
- bootstrap, policy e trust vivono in una configurazione unica (`runtime.env.json`) per ridurre deriva e complessità.

In termini pratici, MindOs nasce per risolvere un problema concreto: permettere anche a un singolo maintainer di orchestrare flussi ad alta complessità con continuità cognitiva, sicurezza e ripetibilità, senza perdere tempo nel passaggio tra tool separati.

---

## 1) Cosa fa MindOs oggi

### 1.1 Core funzionale

- Orchestratore centrale: decide, pianifica, delega ai plugin, applica policy e capability gating.
- Memoria multi-livello:
  - episodica (`episodic_events.jsonl`)
  - operativa (`operational_state.json`)
  - contesto (`active_context.json`)
  - semantica (`semantic_memory.json`)
  - procedurale (`procedural_memory.json`)
  - scheduler (`scheduler_state.json`)
  - audit (`audit_log.jsonl`)
- Runtime unico: stessa pipeline per interazioni manuali e automazioni.
- Plugin manager:
  - plugin interni (documento/presentazione)
  - programmi esterni cross-platform (Windows/Linux) trattati come plugin
  - catalogo, installazione, upgrade, remove, lockfile.
- Trust & security:
  - ACL utente/surface/capability
  - trust policy signer/integrità/firma
  - revoca signer
  - sandbox programmi (timeout, allowlist esecuzione reale)
- Scheduler integrato: pattern procedurali riusabili e tick deterministico.

### 1.2 Superfici

- CLI: controllo completo (run, retrieval, plugin/program manager, scheduler).
- IDE view: recupero contesto cross-surface.
- Desktop shell minimale: workflow unificato documento -> presentazione.

---

## 2) Architettura repository

```text
E:\OS
├─ core
│  ├─ bootstrap
│  ├─ memory
│  ├─ orchestrator
│  ├─ platform
│  ├─ plugin
│  └─ runtime
├─ plugins
├─ surfaces
│  ├─ cli
│  ├─ desktop
│  └─ ide
├─ docs
│  ├─ architecture
│  ├─ contracts
│  └─ milestones
├─ tests
├─ scripts
├─ fixtures
└─ runtime.env.json
```

### 2.1 File chiave

- `runtime.env.json`: configurazione unica del sistema.
- `core/orchestrator/engine.py`: mente centrale.
- `core/plugin/manager.py`: installazione/gestione plugin e programmi.
- `core/plugin/trust.py`: policy trust/firme/revoche.
- `core/plugin/program_plugin.py`: wrapper programmi esterni.
- `core/llm/`: provider LLM pluggable (`mock`, `ollama`, `llamacpp`, `openai_compatible`).
- `surfaces/cli/main.py`: interfaccia operativa principale.
- `scripts/install_os.ps1`: installazione one-shot completa.

---

## 3) Prerequisiti

- Windows PowerShell.
- Accesso internet (solo se vuoi download runtime o installazione programma reale).
- Git e GitHub CLI opzionale per pubblicazione.

---

## 4) Bootstrap e installazione

### 4.1 Installazione Python locale in workspace

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python.ps1
```

### 4.2 Preflight completo (struttura + contratti + smoke)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

### 4.3 CI locale completa

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ci_local.ps1
```

### 4.4 Installazione one-shot MindOs

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_os.ps1
```

Questo script esegue: bootstrap -> preflight -> CI -> init runtime health.

---

## 5) Configurazione unica (`runtime.env.json`)

Campi principali:

- `system_name`: nome sistema (`MindOs`).
- `deterministic_mode`: modalità deterministica.
- `data_dir`: cartella dati runtime.
- `allowed_capabilities`: capability globali autorizzabili.
- `bootstrap_plugins`: plugin caricati all’avvio.
- `llm`: provider LLM e parametri runtime (`enabled`, `provider`, `model`, `base_url`, `timeout_sec`).
- `program_registry_file`: registry esterno opzionale (file/http/https).
- `policy`:
  - `acl`: autorizzazioni user/surface/capability
  - `plugin_trust`: integrità/firma/revoca signer
  - `program_sandbox`: limiti esecuzione programmi.

---

## 6) Comandi CLI operativi

### 6.1 Flussi documentali

```bash
python -m surfaces.cli.main run --project demo-project --title "Doc" --body "Contenuto"
python -m surfaces.cli.main run-presentation --project demo-project --title "Deck" --from-latest
python -m surfaces.cli.main run-workflow --project demo-project --document-title "Doc" --document-body "Testo" --presentation-title "Deck"
```

### 6.2 Memoria procedurale e scheduler

```bash
python -m surfaces.cli.main promote --project demo-project --pattern-id weekly_doc --title "Doc" --body "Contenuto"
python -m surfaces.cli.main run-pattern --pattern-id weekly_doc --title "Doc Aggiornato"
python -m surfaces.cli.main create-schedule --schedule-id weekly_job --pattern-id weekly_doc --interval-seconds 3600 --max-runs 1
python -m surfaces.cli.main tick-scheduler
python -m surfaces.cli.main list-schedules
```

### 6.3 Plugin interni

```bash
python -m surfaces.cli.main plugin-catalog
python -m surfaces.cli.main plugin-install --plugin-id document.plugin.v1
python -m surfaces.cli.main plugin-list
python -m surfaces.cli.main plugin-upgrade --plugin-id document.plugin.v1
python -m surfaces.cli.main plugin-remove --plugin-id document.plugin.v1
```

### 6.4 Programmi cross-platform come plugin

```bash
python -m surfaces.cli.main program-catalog
python -m surfaces.cli.main program-install --program-id shell.echo.program.v1
python -m surfaces.cli.main program-list
python -m surfaces.cli.main program-run --project demo-project --capability program.echo.execute --arg "hello"
python -m surfaces.cli.main program-remove --program-id shell.echo.program.v1
python -m surfaces.cli.main program-upgrade --program-id shell.echo.program.v1
```

Installazione reale pacchetto programma (se supportata e policy/tool disponibili):

```bash
python -m surfaces.cli.main program-install --program-id python.runner.program.v1 --execute-install
```

### 6.5 Recovery e continuità

```bash
python -m surfaces.cli.main retrieve --project demo-project
python -m surfaces.cli.main resume --run-id run-3
python -m surfaces.cli.main rollback --run-id run-3
python -m surfaces.ide.view --project demo-project
python -m surfaces.desktop.shell --project demo-project --document-title "Doc" --document-body "Testo" --presentation-title "Deck"
```

### 6.6 LLM runtime (cloud e on-prem)

```bash
python -m surfaces.cli.main llm-health
python -m surfaces.cli.main llm-generate --prompt "Summarize system state"
```

Profili supportati:

- `provider: "ollama"` -> endpoint locale Ollama (`http://127.0.0.1:11434`).
- `provider: "llamacpp"` -> server locale `llama.cpp`.
- `provider: "openai_compatible"` -> endpoint compatibile OpenAI.
- `provider: "mock"` -> test offline deterministici.

Modalita di selezione dal file env (`runtime.env.json`):

- `llm.source: "env"` -> usa profilo `llm.env` (o fallback flat `llm.*`)
- `llm.source: "api"` -> usa profilo `llm.api` (endpoint API)
- `llm.source: "local"` -> usa profilo `llm.local` (Ollama/llama.cpp on-prem)

---

## 7) Program registry esterno

`program_registry_file` può puntare a:

- path locale (es. `E:\OS\registry\programs.json`)
- `file://...`
- `http://...`
- `https://...`

Formato supportato:

- **Legacy**: array JSON di programmi (retrocompatibilità).
- **Preferred**: envelope firmato con metadata (`meta`) + `programs`.

### 7.1 Formato envelope firmato (raccomandato)

```json
{
  "meta": {
    "signer": "core-team",
    "integrity": "<sha256-registry>",
    "signature": {
      "alg": "hmac-sha256-v1",
      "key_id": "core-v1",
      "sig": "<signature>"
    },
    "issued_at_epoch": 1760000000,
    "expires_at_epoch": 1760086400
  },
  "programs": [
    {
      "plugin_id": "custom.echo.program.v1",
      "version": "1.0.0",
      "capabilities": ["program.custom.execute"],
      "deterministic": true,
      "command_by_platform": {
        "windows": ["powershell", "-NoProfile", "-Command", "Write-Output"],
        "linux": ["/bin/echo"]
      },
      "install_by_platform": {},
      "signer": "core-team",
      "integrity": "<sha256-program>",
      "signature": {
        "alg": "hmac-sha256-v1",
        "key_id": "core-v1",
        "sig": "<signature>"
      }
    }
  ]
}
```

### 7.2 Formato legacy (compatibile)

```json
[
  {
    "plugin_id": "custom.echo.program.v1",
    "version": "1.0.0",
    "capabilities": ["program.custom.execute"],
    "deterministic": true,
    "command_by_platform": {
      "windows": ["powershell", "-NoProfile", "-Command", "Write-Output"],
      "linux": ["/bin/echo"]
    },
    "install_by_platform": {},
    "signer": "core-team",
    "integrity": "<sha256>",
    "signature": {
      "alg": "hmac-sha256-v1",
      "key_id": "core-v1",
      "sig": "<signature>"
    }
  }
]
```

---

## 8) Trust & sicurezza operativa

### 8.1 Trust chain plugin/programmi

- `integrity` obbligatoria (hash payload canonico).
- `signature` obbligatoria (HMAC con envelope strutturato) se `require_signature=true`.
- `signer` deve essere:
  - in `trusted_signers`
  - non in `revoked_signers`
  - con chiave presente in `signer_keys`.
- supporto **key rotation** con `key_id`.
- revoca chiavi granulari con `revoked_key_ids` (formato `signer:key_id`).
- registry esterno firmato con controllo expiry (`expires_at_epoch`).

### 8.2 ACL

Accesso filtrato per:

- utente
- superficie (`cli`, `ide`, `desktop`)
- capability consentite/negate.

### 8.3 Sandbox programmi

- `max_timeout_sec`
- `allow_real_execution`
- `allowed_capabilities_for_real_execution`

Le capability fuori allowlist possono fare solo `dry_run`.

---

## 9) Testing e qualità

### 9.1 Test suite

```bash
python -m unittest discover -s tests -p "test_*.py"
```

La suite valida:

- orchestrazione E2E
- guardrail/policy
- continuità cross-surface
- scheduler
- plugin manager
- program plugin cross-platform
- trust/revoca/sandbox/registry esterno.

### 9.2 Preflight

`scripts/preflight.ps1` include smoke reali su:

- flow CLI->IDE->resume->rollback
- ciclo plugin manager
- ciclo programma cross-platform come plugin.

### 9.3 Metriche test e qualità (baseline attuale)

Baseline verificata localmente:

- **Test totali**: `24`
- **Esito**: `OK`
- **Pipeline**: `scripts/ci_local.ps1` -> bootstrap + preflight + unit/integration/E2E
- **Installer smoke**: `scripts/install_os.ps1` verde

Comandi canonical:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ci_local.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install_os.ps1
```

### 9.4 Matrice test dettagliata

| File test | Copertura principale |
|---|---|
| `tests/test_e2e_vertical_slice.py` | Vertical slice E2E, continuità CLI->IDE, audit, rollback |
| `tests/test_guardrails_and_plugins.py` | Guardrail azioni sensibili, reject plugin non deterministici |
| `tests/test_workflow_presentation.py` | Pipeline documento->presentazione, memoria procedurale |
| `tests/test_policy_and_desktop.py` | ACL/policy + workflow desktop unificato |
| `tests/test_scheduler.py` | Scheduler ricorrente, max-runs, disable automatico |
| `tests/test_plugin_manager.py` | Ciclo plugin manager install/list/remove/upgrade |
| `tests/test_program_plugins.py` | Programmi come plugin cross-platform via orchestratore |
| `tests/test_trust_sandbox_registry.py` | Trust signer/revoca/key rotation, sandbox, registry envelope |
| `tests/test_preflight_contracts.py` | Contratti minimi, schema env/policy/trust |

---

## 10) Stato avanzamento

MindOs è pronto come piattaforma AI-native funzionante nel perimetro attuale:

- orchestrazione centralizzata
- memoria integrata
- programmi/plugin unificati
- governance policy/trust/sandbox
- installazione e CI automatizzate.

---

## 11) Limiti attuali (trasparenti)

- Firma attuale HMAC (non PKI enterprise asimmetrica).
- Sandbox applicativa (non isolamento kernel-grade).
- Registry remoto supportato via JSON; mancano endpoint enterprise con attestazioni complete.
- Desktop UX ancora minima rispetto a un OS commerciale completo.

---

## 12) Roadmap immediata consigliata

1. PKI asimmetrica (Ed25519/RSA), rotazione chiavi, attestazione artifact.
2. Registry service dedicato con metadata firmati server-side.
3. Sandboxing più forte (container/jail/process constraints per host).
4. Marketplace plugin/programmi con policy rollout/canary.
5. Desktop shell completa con gestione plugin/job/live memory.

---

## 13) Licenza e contributi

Definisci nel repository GitHub:

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODEOWNERS`

per rendere MindOs collaborabile e governabile su larga scala.

---

## 14) Roadmap ufficiale

La roadmap esecutiva aggiornata vive in:

- `ROADMAP.md`

---

## 15) Contribuzione possibile (percorsi concreti)

Per contribuire in modo utile e non dispersivo:

### 15.1 Security contributor track

- hardening trust model
- test bypass ACL/capability
- regression pack su registry/sandbox

Output atteso:

- test nuovi
- aggiornamento `SECURITY.md` e `docs/contracts/*` se necessario

### 15.2 Platform contributor track

- nuovi plugin interni
- nuovi program plugin cross-platform
- miglioramenti scheduler/orchestrator

Output atteso:

- capability dichiarate
- policy/trust/sandbox allineate
- preflight e CI verdi

### 15.3 DevEx contributor track

- miglioramento script install/bootstrap/ci
- miglioramento osservabilità locale
- miglioramenti documentazione operativa

Output atteso:

- riduzione tempo setup
- runbook chiari
- automazione più robusta

### 15.4 Regole di ingresso PR

- seguire `CONTRIBUTING.md`
- commit firmati DCO (`git commit -s`)
- nessuna PR senza test o without rationale
- nessuna modifica a core policy/trust senza aggiornamenti contrattuali
