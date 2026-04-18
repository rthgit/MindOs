# Vertical Slice E2E

Scenario implementato:

1. Boot con file unico `runtime.env.json`.
2. CLI invia intent `generate_document`.
3. Orchestratore applica guardrail + capability gating.
4. Runtime esegue plugin deterministico.
5. Memoria persiste eventi, stato run, fatto semantico e audit.
6. IDE recupera contesto cross-surface su stesso progetto.

Obiettivo: dimostrare continuità operativa e auditabilità deterministica del flusso minimo.
