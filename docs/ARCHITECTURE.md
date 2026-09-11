# Agentic SOC N1 Lab

## ARCHITECTURE — Arquitetura Oficial V1

**Versão:** 1.0  
**Status:** Definida  
**Projeto:** Agentic SOC N1 Lab  
**Fase:** 0 — Escopo e Arquitetura

---

# 1. Visão Geral

O Agentic SOC N1 Lab utiliza uma arquitetura multiagente para automatizar o fluxo operacional de um SOC N1.

A arquitetura possui:

- agentes especializados;
- SOC Supervisor Agent;
- Orchestrator;
- Case State compartilhado;
- ferramentas controladas;
- Knowledge Base;
- Agentic RAG;
- MCP;
- persistência;
- auditoria;
- Guardrails;
- Human Review.

Princípio central:

> Cada agente possui uma função específica e somente as permissões necessárias para executá-la.

---

# 2. Arquitetura de Alto Nível

```text
EVENTO / ALERTA
       |
       v
+----------------------+
| AG-02 ALERT INTAKE   |
+----------+-----------+
           |
           v
+----------------------+
| AG-01 SOC SUPERVISOR |
+----------+-----------+
           |
           v
+----------------------+
| AG-03 TRIAGE         |
+----------+-----------+
           |
    +------+-------+---------+
    |              |         |
    v              v         v
 AG-04          AG-05      AG-06
 THREAT         IDENTITY   ASSET
 INTEL
    |              |         |
    +--------------+---------+
                   |
          +--------+--------+
          |                 |
          v                 v
       AG-07             AG-08
       PHISHING          RAG
          |                 |
          +--------+--------+
                   |
                   v
             AG-09 INCIDENT
                   |
                   v
          AG-10 REFLECTION/QA
                   |
             +-----+-----+
             |           |
           RETRY        PASS
                         |
                         v
                AG-11 CASE MANAGEMENT
                         |
                         v
                  AG-12 ESCALATION
                    |      |      |
                    v      v      v
               CLOSED_N1  N2   HUMAN
```

---

# 3. Separação de Responsabilidades

A arquitetura separa:

```text
AGENT
TOOL
DATA
POLICY
STATE
KNOWLEDGE
```

Um agente não é uma ferramenta.

Exemplo:

```text
Threat Intelligence Agent
        |
        v
decide consultar IP
        |
        v
lookup_ip()
        |
        v
fonte de Threat Intelligence
        |
        v
resultado
        |
        v
agente interpreta
```

---

# 4. Agents Layer

Os agentes serão armazenados em:

```text
agents/
```

Agentes oficiais:

- AG-01 — SOC Supervisor
- AG-02 — Alert Intake
- AG-03 — Triage Analyst
- AG-04 — Threat Intelligence
- AG-05 — Identity Analyst
- AG-06 — Asset Context
- AG-07 — Phishing Analyst
- AG-08 — Knowledge/RAG
- AG-09 — Incident Analyst
- AG-10 — Reflection/QA
- AG-11 — Case Management
- AG-12 — Escalation

Cada agente deverá possuir:

- responsabilidade;
- input schema;
- output schema;
- prompt;
- ferramentas permitidas;
- permissões;
- timeout;
- limites;
- testes.

---

# 5. SOC Supervisor

O AG-01 será responsável por coordenar a equipe.

Fluxo conceitual:

```text
Receber Case State
      |
      v
Verificar estado
      |
      v
Identificar informações faltantes
      |
      v
Selecionar agente necessário
      |
      v
Executar agente
      |
      v
Atualizar Case State
      |
      v
Verificar próximo passo
```

O Supervisor poderá:

- escolher agentes;
- distribuir tarefas;
- acompanhar estado;
- solicitar retry;
- encaminhar para análise;
- encaminhar para QA;
- encaminhar para escalonamento.

Não poderá:

- criar evidências falsas;
- alterar o raw_event;
- modificar resultados das ferramentas;
- ignorar hard rules;
- executar ações críticas.

---

# 6. Orchestrator

O Orchestrator será responsável pela execução técnica das decisões do Supervisor.

Exemplo:

```text
Supervisor:
"Execute AG-05 Identity"

        |
        v

Orchestrator

1. verifica permissão
2. monta entrada
3. executa agente
4. controla timeout
5. recebe resultado
6. valida schema
7. atualiza estado
8. registra auditoria
```

Regra:

> O Supervisor decide. O Orchestrator executa.

---

# 7. Case State

Todos os agentes trabalharão sobre um estado central do incidente.

Principais áreas:

```text
case
source
event
indicators
identity
asset
triage
threat_intel
phishing
knowledge
evidence
investigation
qa
escalation
workflow
audit
```

Campos principais:

- alert_id;
- correlation_id;
- incident_id;
- status;
- created_at;
- updated_at.

---

# 8. Ownership dos Dados

Cada agente será responsável por uma área.

| Área | Responsável |
|---|---|
| source/event | Alert Intake |
| triage | Triage |
| threat_intel | Threat Intel |
| identity | Identity |
| asset | Asset |
| phishing | Phishing |
| knowledge | RAG |
| investigation | Incident Analyst |
| qa | Reflection |
| escalation | Escalation |
| workflow | Supervisor |
| audit | Sistema |

---

# 9. Imutabilidade

## raw_event

Será imutável.

Nenhum agente poderá alterar o evento original.

## evidence

Será append-only.

Novas evidências poderão ser adicionadas, mas evidências anteriores não poderão ser apagadas.

## audit

Também será append-only.

---

# 10. Tools Layer

Ferramentas previstas:

```text
tools/
├── threat_intel/
├── identity/
├── assets/
├── email/
├── knowledge/
└── case/
```

Exemplos:

```text
lookup_ip()
lookup_domain()
lookup_url()
lookup_hash()

lookup_identity()
lookup_asset()

search_playbook()

create_case()
write_audit_event()
```

---

# 11. Contrato das Ferramentas

Cada ferramenta deverá possuir configuração semelhante a:

```json
{
  "name": "lookup_ip",
  "allowed_agents": ["AG-04"],
  "read_only": true,
  "timeout_seconds": 10,
  "audit": true
}
```

Regra:

```text
DENY BY DEFAULT
```

Se o agente não estiver explicitamente autorizado, a chamada será bloqueada.

---

# 12. Permission Layer

Tipos de permissão:

```text
READ
WRITE
TOOL
DECISION
```

Nenhum agente do MVP possuirá:

```text
EXECUTE_CRITICAL_ACTION
```

---

# 13. Knowledge Base

Estrutura prevista:

```text
knowledge/
├── playbooks/
├── runbooks/
├── policies/
└── mitre/
```

Exemplos de playbooks:

```text
brute_force.md
phishing.md
credential_exposure.md
malware.md
suspicious_login.md
```

---

# 14. Agentic RAG

Fluxo:

```text
Pergunta/contexto
       |
       v
Planejamento da consulta
       |
       v
Retrieval
       |
       v
Chunks relevantes
       |
       v
Validação das fontes
       |
       v
Resposta estruturada
```

Se a informação for insuficiente, o agente poderá realizar nova busca.

Toda resposta deverá conter:

- fonte;
- documento;
- trecho;
- score.

---

# 15. Embeddings

Fluxo de indexação:

```text
Documento
   |
   v
Chunking
   |
   v
Embedding
   |
   v
Vector
   |
   v
Index
```

Fluxo de consulta:

```text
Pergunta
   |
   v
Embedding
   |
   v
Cosine Similarity
   |
   v
Resultados mais relevantes
```

Inicialmente não será obrigatório utilizar banco vetorial externo.

---

# 16. MCP

O MCP será adicionado depois que as ferramentas locais estiverem funcionando.

Estrutura:

```text
mcp/
├── server/
└── client/
```

Ferramentas futuras:

```text
threat_intel.lookup_ip
identity.lookup_user
asset.lookup_host
knowledge.search_playbook
case.create_case
```

---

# 17. Segurança MCP

Fluxo:

```text
AGENT
  |
  v
PERMISSION CHECK
  |
  +---- DENIED ---> AUDIT
  |
  v
ALLOWED
  |
  v
MCP TOOL
  |
  v
RESULT
  |
  v
AUDIT
```

Toda chamada deverá possuir:

- agent_id;
- case_id;
- correlation_id;
- tool;
- input validado;
- timeout;
- resultado;
- auditoria.

---

# 18. Fluxo do Caso

Fluxo normal:

```text
RECEIVED
↓
NORMALIZING
↓
TRIAGING
↓
ENRICHING
↓
INVESTIGATING
↓
CORRELATING
↓
REVIEWING
↓
DOCUMENTING
↓
DECIDING
```

Resultados finais:

```text
CLOSED_N1
ESCALATED_N2
WAITING_HUMAN
```

Estados auxiliares:

```text
WAITING_DATA
RETRYING
FAILED
CANCELLED
```

---

# 19. Estado dos Agentes

Um agente poderá estar em:

```text
PENDING
RUNNING
COMPLETED
FAILED
SKIPPED
```

`SKIPPED` significa que o agente não era necessário para aquele incidente.

---

# 20. Reflection / QA

O Reflection Agent deverá verificar:

- evidências;
- contradições;
- fontes;
- severidade;
- confidence;
- afirmações sem suporte;
- informações faltantes.

Saída exemplo:

```json
{
  "approved": false,
  "issues": [
    "Asset criticality missing"
  ],
  "retry": true
}
```

O agente não poderá criar evidências.

---

# 21. Retry

Valor inicial:

```text
MAX_REFLECTION_RETRIES = 2
```

Fluxo:

```text
QA REJECTED
    |
    v
Supervisor
    |
    v
Agente necessário
    |
    v
Incident Analyst
    |
    v
QA novamente
```

Após o limite:

```text
ESCALATED_N2
```

---

# 22. Incident Analyst

Entrada:

```text
TRIAGE
+
THREAT INTEL
+
IDENTITY
+
ASSET
+
PHISHING
+
RAG
+
EVIDENCE
```

Saída:

```text
summary
timeline
findings
gaps
final_severity
final_confidence
classification
recommended_action
```

---

# 23. Escalation

O AG-12 utilizará:

```text
HARD RULES
+
INVESTIGATION
+
QA
+
CONTEXT
```

Exemplo:

```text
IF confirmed_incident == true
AND critical_asset == true
THEN ESCALATED_N2
```

Hard rules terão prioridade sobre a interpretação do LLM.

---

# 24. Hierarquia de Autoridade

A ordem será:

```text
1. HARD RULES / POLICIES
2. TOOL DATA
3. EVIDENCE
4. CONSOLIDATED CONTEXT
5. LLM INTERPRETATION
```

O LLM não será fonte única de verdade.

---

# 25. Persistência

Inicialmente:

```text
SQLite
JSON
Markdown
Logs
```

SQLite deverá armazenar:

```text
cases
agent_runs
evidence
decisions
audit_events
tool_calls
```

---

# 26. Audit

Evento de auditoria previsto:

```json
{
  "timestamp": "",
  "correlation_id": "",
  "case_id": "",
  "agent_id": "",
  "action": "",
  "tool": null,
  "status": "",
  "details": {}
}
```

O Audit Log será append-only.

---

# 27. Guardrails

Guardrails obrigatórios:

- Least Privilege
- Deny by Default
- Tool Allowlist
- Input Validation
- Output Validation
- Schema Validation
- Timeout
- Max Steps
- Max Retries
- Audit
- Human Review
- Fail Closed

---

# 28. Prompt Injection

Conteúdo recebido de alertas, logs, e-mails, documentos e ferramentas será considerado:

```text
UNTRUSTED DATA
```

e não instrução administrativa.

A arquitetura deverá separar:

```text
SYSTEM INSTRUCTIONS
```

de:

```text
UNTRUSTED DATA
```

---

# 29. Fail Closed

Quando uma ação não puder ser validada com segurança:

```text
DENY
```

Quando faltar informação:

```text
WAITING_DATA
```

ou:

```text
WAITING_HUMAN
```

Quando houver risco ou incerteza relevante:

```text
ESCALATED_N2
```

---

# 30. Estrutura Oficial

```text
Agentic-SOC-N1-Lab/
│
├── agents/
│   ├── supervisor/
│   ├── alert_intake/
│   ├── triage/
│   ├── threat_intel/
│   ├── identity/
│   ├── asset/
│   ├── phishing/
│   ├── knowledge/
│   ├── incident/
│   ├── reflection/
│   ├── case_management/
│   └── escalation/
│
├── core/
│   ├── orchestrator/
│   ├── state/
│   ├── schemas/
│   ├── permissions/
│   ├── llm/
│   └── config/
│
├── tools/
├── mcp/
├── rag/
├── knowledge/
├── storage/
├── simulations/
├── tests/
├── logs/
├── docs/
│   ├── SCOPE.md
│   └── ARCHITECTURE.md
│
├── README.md
├── requirements.txt
├── .gitignore
└── main.py
```

---

# 31. Critério de Sucesso da Arquitetura

A arquitetura estará funcional quando:

1. um alerta entrar;
2. um Case State for criado;
3. o Supervisor escolher os agentes necessários;
4. cada agente executar sua função;
5. ferramentas forem chamadas somente com autorização;
6. evidências forem registradas;
7. o Incident Analyst consolidar os resultados;
8. o QA validar a investigação;
9. o caso for documentado;
10. o sistema decidir entre N1, N2 ou humano;
11. todo o processo puder ser reconstruído pela auditoria.

---

# 32. Princípio Final

O objetivo não é criar um único agente que saiba tudo.

O objetivo é combinar:

```text
AGENTES ESPECIALIZADOS
+
FERRAMENTAS CONFIÁVEIS
+
CONHECIMENTO
+
REGRAS
+
AUDITORIA
+
GOVERNANÇA
+
SUPERVISÃO
```

para formar uma equipe virtual capaz de executar o processo operacional de um SOC N1.