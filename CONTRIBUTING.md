# Contributing to MindOs

MindOs accetta contributi tecnici, documentali e operativi con un principio guida: mantenere coerenza deterministica, governance chiara e sicurezza by default.

## 1. Principi di contribuzione

- Nessuna modifica deve bypassare orchestratore, policy o audit.
- Ogni nuova capability deve essere dichiarata esplicitamente.
- Nessun plugin/programma entra senza controlli trust/sandbox.
- Ogni modifica deve essere testabile e riproducibile.

## 2. Tipi di contributo accettati

- Bug fix
- Miglioramenti sicurezza/policy/trust
- Nuovi plugin interni
- Nuovi program plugin cross-platform
- Miglioramenti test, CI, preflight, documentazione

## 3. Flusso di lavoro consigliato

1. Apri una Issue con problema e impatto.
2. Crea branch da `main` (`feat/...`, `fix/...`, `docs/...`, `security/...`).
3. Implementa con commit atomici.
4. Esegui test locali completi.
5. Apri Pull Request con checklist compilata.

## 4. Setup locale

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_python.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\ci_local.ps1
```

## 5. Requisiti minimi per una PR

- Preflight verde.
- CI locale verde.
- Nessuna regressione su orchestrazione/memoria/policy/trust.
- Aggiornamento docs contrattuali se modifichi interfacce o policy.
- Test nuovi/aggiornati per comportamento cambiato.

## 6. Standard di codice

- Default ASCII.
- Commenti brevi solo dove necessario.
- Nomi espliciti, contratti stabili.
- Evita dipendenze non motivate.
- Non introdurre side-effect impliciti.

## 7. Contratti e breaking changes

Se tocchi uno di questi ambiti, PR bloccata senza aggiornamenti correlati:

- `docs/contracts/interfaces.md`
- `docs/contracts/events.md`
- `runtime.env.json` (policy/capability/trust/sandbox)

## 8. Plugin e programmi

Per nuovi plugin/programmi devi includere:

- capability dichiarate
- metadati trust (signer, integrity, signature)
- regole sandbox applicabili
- test install/run/remove/upgrade

## 9. Commit policy

Formato consigliato:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `test: ...`
- `security: ...`
- `refactor: ...`

## 10. DCO (Developer Certificate of Origin)

Ogni commit deve includere il `Signed-off-by`:

```text
Signed-off-by: Nome Cognome <email@example.com>
```

Puoi usare:

```bash
git commit -s -m "feat: ..."
```

## 11. PR checklist (copiare nella descrizione)

- [ ] Ho letto `CONTRIBUTING.md`.
- [ ] Ho eseguito `scripts/preflight.ps1`.
- [ ] Ho eseguito `scripts/ci_local.ps1`.
- [ ] Ho aggiunto/aggiornato test.
- [ ] Ho aggiornato la documentazione rilevante.
- [ ] Ho aggiunto `Signed-off-by` ai commit.

## 12. Governance review

Le modifiche a queste aree richiedono review esplicita del maintainer:

- `core/orchestrator/**`
- `core/plugin/trust.py`
- `core/plugin/manager.py`
- `core/plugin/program_plugin.py`
- `runtime.env.json`
- `scripts/install_os.ps1`

## 13. Scope esclusi

- Cambi non tracciati in file temporanei runtime (`.runtime_data`, `.ci_*`, `.test_tmp`).
- Commit che saltano preflight/CI.
- Introduzione di backdoor o bypass policy.
