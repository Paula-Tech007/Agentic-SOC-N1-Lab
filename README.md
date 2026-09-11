# Agentic SOC N1 Lab

Laboratório multiagente para automação defensiva ponta a ponta das operações de um SOC N1.

O projeto tem como objetivo construir uma equipe virtual de agentes de IA especializados capazes de executar triagem, enriquecimento, investigação, correlação, revisão, documentação e escalonamento de incidentes de segurança.

## Objetivo

Automatizar o processo operacional de um SOC N1 utilizando:

- agentes especializados;
- Supervisor Agent;
- ferramentas controladas;
- RAG;
- MCP;
- regras determinísticas;
- auditoria;
- Guardrails;
- Human Review.

O sistema deverá conseguir receber um alerta e decidir autonomamente quais especialistas precisam participar da investigação.

## Fluxo principal

```text
EVENTO / ALERTA
       |
       v
ALERT INTAKE
       |
       v
SOC SUPERVISOR
       |
       v
TRIAGE
       |
       +-----------------------+
       |          |            |
       v          v            v
THREAT INTEL   IDENTITY      ASSET
       |          |            |
       +----------+------------+
                  |
          +-------+-------+
          |               |
          v               v
      PHISHING       KNOWLEDGE/RAG
          |               |
          +-------+-------+
                  |
                  v
          INCIDENT ANALYST
                  |
                  v
          REFLECTION / QA
                  |
           +------+------+
           |             |
         RETRY        APPROVED
                         |
                         v
                 CASE MANAGEMENT
                         |
                         v
                 ESCALATION AGENT
                    |     |     |
                    v     v     v
              CLOSED_N1  N2   HUMAN
```

## Profissionais virtuais

O laboratório será composto inicialmente por 12 agentes:

- AG-01 — SOC Supervisor Agent
- AG-02 — Alert Intake Agent
- AG-03 — Triage Analyst Agent
- AG-04 — Threat Intelligence Agent
- AG-05 — Identity Analyst Agent
- AG-06 — Asset Context Agent
- AG-07 — Phishing Analyst Agent
- AG-08 — Knowledge / RAG Agent
- AG-09 — Incident Analyst Agent
- AG-10 — Reflection / QA Agent
- AG-11 — Case Management Agent
- AG-12 — Escalation Agent

## Alertas iniciais

O MVP deverá suportar inicialmente:

- `AUTH_BRUTE_FORCE`
- `SUSPICIOUS_LOGIN`
- `CREDENTIAL_EXPOSURE`
- `PHISHING`
- `MALWARE_DETECTION`
- `SUSPICIOUS_POWERSHELL`
- `MALICIOUS_IOC`
- `PRIVILEGED_ACCOUNT_ACTIVITY`
- `LATERAL_MOVEMENT_SUSPECTED`
- `DATA_EXFILTRATION_SUSPECTED`

## Princípios de segurança

- Least Privilege
- Deny by Default
- Evidence Before Conclusion
- Tool Data Before LLM Guess
- No Critical Autonomous Action
- Everything Audited
- Human Escalation Available
- Bounded Loops
- Fail Closed

## Tecnologias previstas

- Python
- Ollama
- LLM local
- Embeddings locais
- Pydantic
- SQLite
- pytest
- JSON
- Markdown
- MCP
- RAG

## Estrutura

```text
agents/
core/
docs/
knowledge/
logs/
mcp/
rag/
simulations/
storage/
tests/
tools/
```

## Status

### Fase 0 — Escopo e Arquitetura

✅ Concluída

### Fase 1 — Fundação Técnica

🚧 Em desenvolvimento

## Segurança do laboratório

O MVP não executará ações críticas reais como:

- bloquear IP;
- isolar endpoint;
- desabilitar contas;
- resetar senhas;
- alterar firewall.

Essas ações serão inicialmente representadas apenas como:

- `RECOMMENDED_ACTION`
- `SIMULATED_ACTION`

## Documentação

A documentação detalhada será mantida em:

```text
docs/
```

Documentos principais:

- `SCOPE.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `PERMISSIONS.md`
- `ALERT_CATALOG.md`

---

**Agentic SOC N1 Lab**

Automação defensiva de SOC N1 baseada em arquitetura multiagente.# Agentic SOC N1 Lab

Laboratório multiagente para automação defensiva ponta a ponta das operações de um SOC N1.

O projeto tem como objetivo construir uma equipe virtual de agentes de IA especializados capazes de executar triagem, enriquecimento, investigação, correlação, revisão, documentação e escalonamento de incidentes de segurança.

## Objetivo

Automatizar o processo operacional de um SOC N1 utilizando:

- agentes especializados;
- Supervisor Agent;
- ferramentas controladas;
- RAG;
- MCP;
- regras determinísticas;
- auditoria;
- Guardrails;
- Human Review.

O sistema deverá conseguir receber um alerta e decidir autonomamente quais especialistas precisam participar da investigação.

## Fluxo principal

```text
EVENTO / ALERTA
       |
       v
ALERT INTAKE
       |
       v
SOC SUPERVISOR
       |
       v
TRIAGE
       |
       +-----------------------+
       |          |            |
       v          v            v
THREAT INTEL   IDENTITY      ASSET
       |          |            |
       +----------+------------+
                  |
          +-------+-------+
          |               |
          v               v
      PHISHING       KNOWLEDGE/RAG
          |               |
          +-------+-------+
                  |
                  v
          INCIDENT ANALYST
                  |
                  v
          REFLECTION / QA
                  |
           +------+------+
           |             |
         RETRY        APPROVED
                         |
                         v
                 CASE MANAGEMENT
                         |
                         v
                 ESCALATION AGENT
                    |     |     |
                    v     v     v
              CLOSED_N1  N2   HUMAN
```

## Profissionais virtuais

O laboratório será composto inicialmente por 12 agentes:

- AG-01 — SOC Supervisor Agent
- AG-02 — Alert Intake Agent
- AG-03 — Triage Analyst Agent
- AG-04 — Threat Intelligence Agent
- AG-05 — Identity Analyst Agent
- AG-06 — Asset Context Agent
- AG-07 — Phishing Analyst Agent
- AG-08 — Knowledge / RAG Agent
- AG-09 — Incident Analyst Agent
- AG-10 — Reflection / QA Agent
- AG-11 — Case Management Agent
- AG-12 — Escalation Agent

## Alertas iniciais

O MVP deverá suportar inicialmente:

- `AUTH_BRUTE_FORCE`
- `SUSPICIOUS_LOGIN`
- `CREDENTIAL_EXPOSURE`
- `PHISHING`
- `MALWARE_DETECTION`
- `SUSPICIOUS_POWERSHELL`
- `MALICIOUS_IOC`
- `PRIVILEGED_ACCOUNT_ACTIVITY`
- `LATERAL_MOVEMENT_SUSPECTED`
- `DATA_EXFILTRATION_SUSPECTED`

## Princípios de segurança

- Least Privilege
- Deny by Default
- Evidence Before Conclusion
- Tool Data Before LLM Guess
- No Critical Autonomous Action
- Everything Audited
- Human Escalation Available
- Bounded Loops
- Fail Closed

## Tecnologias previstas

- Python
- Ollama
- LLM local
- Embeddings locais
- Pydantic
- SQLite
- pytest
- JSON
- Markdown
- MCP
- RAG

## Estrutura

```text
agents/
core/
docs/
knowledge/
logs/
mcp/
rag/
simulations/
storage/
tests/
tools/
```

## Status

### Fase 0 — Escopo e Arquitetura

✅ Concluída

### Fase 1 — Fundação Técnica

🚧 Em desenvolvimento

## Segurança do laboratório

O MVP não executará ações críticas reais como:

- bloquear IP;
- isolar endpoint;
- desabilitar contas;
- resetar senhas;
- alterar firewall.

Essas ações serão inicialmente representadas apenas como:

- `RECOMMENDED_ACTION`
- `SIMULATED_ACTION`

## Documentação

A documentação detalhada será mantida em:

```text
docs/
```

Documentos principais:

- `SCOPE.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `PERMISSIONS.md`
- `ALERT_CATALOG.md`

---

**Agentic SOC N1 Lab**

Automação defensiva de SOC N1 baseada em arquitetura multiagente.