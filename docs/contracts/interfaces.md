# Contratti Minimi v0

- `SubmitIntent(raw_intent)` -> intent normalizzato.
- `DispatchExecution(plan)` -> esecuzione runtime.
- `AppendEvent(event_type, correlation_id, payload)` -> evento append-only.
- `RetrieveContext(user_id, project)` -> contesto cross-surface.
- `RegisterPlugin(manifest)` -> validazione capability/determinismo.
- `RollbackInternal(run_id)` -> rollback stato operativo interno.
- `RunProceduralPattern(pattern_id, overrides)` -> esecuzione workflow riusabile.
- `ExecuteWorkflowDocumentToPresentation(...)` -> pipeline multi-step documento->presentazione.
- `CreateSchedule(schedule_id, pattern_id, interval_seconds, ...)` -> schedule ricorrente.
- `RunSchedulerTick(now_epoch)` -> esecuzione deterministica dei job dovuti.
- `ListSchedules()` -> stato schedule persistito.
- `PluginInstall(plugin_id)` -> installazione plugin dal catalogo.
- `PluginList()` -> elenco plugin installati.
- `PluginRemove(plugin_id)` -> rimozione plugin.
- `PluginUpgrade(plugin_id)` -> riallineamento versione plugin.
- `ProgramInstall(program_id, execute_install)` -> installazione programma/plugin cross-platform.
- `ProgramList()` -> elenco programmi/plugin installati.
- `ProgramRun(capability, args)` -> esecuzione programma via orchestratore.
- `ProgramCatalog()` -> catalogo programmi/plugin cross-platform disponibili.
- `ProgramRegistryFile` -> estensione catalogo da file esterno JSON (provenance controllata).

Policy:

- Capability non presenti in `runtime.env.json.allowed_capabilities` sono rifiutate.
- Plugin con `deterministic=false` sono rifiutati.
- Azioni classificate `confirm_required` richiedono conferma esplicita.
- ACL utente/surface/capability applicata da `policy.acl.users`.
- Trust policy plugin (`policy.plugin_trust`) valida signer e hash integrità.
- Firma plugin obbligatoria (`policy.plugin_trust.require_signature`) con verifica su `signer_keys`.
- Catena trust include revoca signer (`policy.plugin_trust.revoked_signers`).
- Program sandbox (`policy.program_sandbox`) applica limiti timeout e allowlist capability per esecuzione reale.
