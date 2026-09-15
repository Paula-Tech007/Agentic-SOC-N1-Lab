<div align="center">

<img src="assets/banner-agentic-soc-n1-lab.png" alt="Agentic SOC N1 Lab" width="100%">

<br>

> AGENTIC_SOC_N1_LAB

SECURITY OPERATIONS // MULTI-AGENT AI // EVIDENCE-DRIVEN

<br>











<br>

┌──────────────────────────────────────────────────────────────────────────────┐
│  AI INTERPRETS  //  TOOLS VERIFY  //  GOVERNANCE DECIDES  //  HUMAN CAN ACT │
└──────────────────────────────────────────────────────────────────────────────┘

</div>

01 // SYSTEM DASHBOARD

<table>
<tr>
<td width="25%" align="center">
<strong>ARCHITECTURE</strong><br><br>
<code>MULTI-AGENT</code>
</td>
<td width="25%" align="center">
<strong>AGENTS</strong><br><br>
<code>12 OFFICIAL</code>
</td>
<td width="25%" align="center">
<strong>TEST SUITE</strong><br><br>
<code>151 PASSED</code>
</td>
<td width="25%" align="center">
<strong>SECURITY MODE</strong><br><br>
<code>READ_ONLY</code>
</td>
</tr>
<tr>
<td align="center">
<strong>CURRENT PHASE</strong><br><br>
<code>4.4 COMPLETE</code>
</td>
<td align="center">
<strong>INTEGRATIONS</strong><br><br>
<code>4 ACTIVE</code>
</td>
<td align="center">
<strong>CRITICAL ACTIONS</strong><br><br>
<code>0 AUTONOMOUS</code>
</td>
<td align="center">
<strong>NEXT TARGET</strong><br><br>
<code>PHASE 4.5</code>
</td>
</tr>
</table>

SYSTEM        Agentic SOC N1 Lab
MISSION       Automate SOC N1 safely
STATE         ONLINE / DEVELOPMENT
EVIDENCE      REQUIRED
AUDIT         APPEND-ONLY
PRIVILEGE     LEAST PRIVILEGE
FAILURE MODE  FAIL CLOSED
NEXT MODULE   Email / Phishing Metadata

02 // MISSION

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança criado para implementar um SOC N1 multiagente, com agentes especializados trabalhando de forma coordenada para:

receber e normalizar alertas;

executar triagem;

enriquecer evidências;

consultar ferramentas de segurança;

investigar identidade e ativos;

analisar phishing;

consultar conhecimento interno;

consolidar investigação;

revisar qualidade;

documentar o caso;

decidir fechamento N1 ou escalonamento;

registrar todo o processo em auditoria.

Regra central: a LLM pode interpretar contexto, mas uma ferramenta ou evidência verificável deve sustentar a conclusão.

03 // THREAT-TO-DECISION PIPELINE

flowchart LR
    A[ALERT / EVENT] --> B[AG-02<br/>ALERT INTAKE]
    B --> C[AG-03<br/>TRIAGE]
    C --> S[AG-01<br/>SOC SUPERVISOR]

    S --> TI[AG-04<br/>THREAT INTEL]
    S --> ID[AG-05<br/>IDENTITY]
    S --> AS[AG-06<br/>ASSET]
    S --> PH[AG-07<br/>PHISHING]
    S --> KG[AG-08<br/>KNOWLEDGE / RAG]

    TI --> INV[AG-09<br/>INCIDENT ANALYST]
    ID --> INV
    AS --> INV
    PH --> INV
    KG --> INV

    INV --> QA[AG-10<br/>REFLECTION / QA]

    QA -->|REJECTED| S
    QA -->|APPROVED| CM[AG-11<br/>CASE MANAGEMENT]

    CM --> ESC[AG-12<br/>ESCALATION]

    ESC --> N1[CLOSED_N1]
    ESC --> N2[ESCALATED_N2]
    ESC --> HU[WAITING_HUMAN]

O loop multiagente automático completo Supervisor → Especialistas → Supervisor pertence à Fase 7.

04 // AGENT MATRIX

NODE

AGENTE

FUNÇÃO OPERACIONAL

AG-01

SOC Supervisor

Coordena fluxo, roteamento e decisões de controle

AG-02

Alert Intake

Recebe, valida e normaliza alertas

AG-03

Triage Analyst

Classifica alerta, severidade e contexto inicial

AG-04

Threat Intelligence

Consulta e consolida Threat Intelligence

AG-05

Identity Analyst

Analisa usuário, conta, MFA e grupos

AG-06

Asset Context

Recupera ativo, IP, criticidade e EDR

AG-07

Phishing Analyst

Analisa metadados, headers, autenticação e anexos

AG-08

Knowledge / RAG

Recupera políticas, playbooks e runbooks

AG-09

Incident Analyst

Consolida evidências e investigação

AG-10

Reflection / QA

Revisa qualidade, lacunas e inconsistências

AG-11

Case Management

Mantém histórico e documentação do caso

AG-12

Escalation

Fecha N1, escala N2 ou aguarda humano

05 // CASE STATE CORE

┌─────────────┐
│    ALERT    │
└──────┬──────┘
       │
       ├── IOCs
       ├── Identity Context
       ├── Asset Context
       ├── Evidence
       ├── Triage
       ├── Threat Intelligence
       ├── Phishing
       ├── Knowledge / RAG
       ├── Investigation
       ├── QA
       ├── Escalation
       ├── Audit
       └── Workflow
                │
                ▼
           ┌───────────┐
           │ CaseState │
           └───────────┘

O CaseState é a ficha viva da investigação.

Ele mantém:

case_id;

correlation_id;

versionamento;

timestamps;

evidências;

resultados dos agentes;

estados do workflow;

auditoria;

dados consolidados da investigação.

06 // WORKFLOW STATES

flowchart LR
    A[RECEIVED] --> B[NORMALIZING]
    B --> C[TRIAGING]
    C --> D[ENRICHING]
    D --> E[INVESTIGATING]
    E --> F[CORRELATING]
    F --> G[REVIEWING]
    G --> H[DOCUMENTING]
    H --> I[DECIDING]
    I --> J[CLOSED_N1]
    I --> K[ESCALATED_N2]

Auxiliary states

WAITING_DATA · WAITING_HUMAN · RETRYING · FAILED · CANCELLED

Agent execution states

PENDING · RUNNING · COMPLETED · FAILED · SKIPPED

07 // EVIDENCE PRIORITY

╔═══════════════════════════════╗
║          HARD RULES           ║
╠═══════════════════════════════╣
║           TOOL DATA           ║
╠═══════════════════════════════╣
║           EVIDENCE            ║
╠═══════════════════════════════╣
║     CONSOLIDATED CONTEXT      ║
╠═══════════════════════════════╣
║      LLM INTERPRETATION       ║
╚═══════════════════════════════╝

Fontes de evidência

SOURCE

PURPOSE

ALERT

Evento original

MISP

Threat Intelligence

ELASTIC

Alertas, eventos e documentos

IAM

Usuário, MFA, grupos e status

ASSET / CMDB

Ativo, IP, criticidade e EDR

EMAIL

Metadados e autenticação

RAG

Políticas, playbooks e runbooks

AUDIT

Rastreabilidade da execução

08 // SECURITY CONTROL PLANE

<table>
<tr>
<td width="50%">

ACCESS CONTROL

deny-by-default;

least privilege;

autorização por agente;

catálogo oficial de tools;

rotas explicitamente permitidas;

ferramentas proibidas bloqueadas.

</td>
<td width="50%">

EXECUTION CONTROL

fail closed;

timeout;

retries limitados;

bounded loops;

validação de binding;

sem shell irrestrito.

</td>
</tr>
<tr>
<td>

DATA INTEGRITY

raw_event imutável;

evidências imutáveis;

auditoria append-only;

versionamento do caso;

rastreabilidade ponta a ponta.

</td>
<td>

HUMAN CONTROL

escalonamento N2;

espera por humano;

hard rules;

nenhuma contenção crítica autônoma;

QA antes da decisão final.

</td>
</tr>
</table>

09 // CRITICAL ACTION LOCK

[LOCKED]  iam.reset_password
[LOCKED]  iam.disable_user
[LOCKED]  iam.delete_user

[LOCKED]  network.block_ip
[LOCKED]  network.unblock_ip

[LOCKED]  firewall.add_rule
[LOCKED]  firewall.delete_rule
[LOCKED]  firewall.modify_rule

[LOCKED]  endpoint.isolate_host
[LOCKED]  endpoint.kill_process
[LOCKED]  endpoint.delete_file

[LOCKED]  email.open_url
[LOCKED]  email.execute_attachment
[LOCKED]  email.download_attachment

O laboratório trabalha, quando necessário, apenas com:

RECOMMENDED_ACTION
SIMULATED_ACTION

Nenhuma ação crítica real é executada automaticamente.

10 // TOOLING LAYER

PHASE 4.0 // FOUNDATION

Tool Catalog
Authorization
Tool Registry
Tool Runtime
Timeout
Retry Control
Fail Closed
Evidence Requirement
Forbidden Tool Guardrails

Modes:

READ_ONLY · RECOMMENDED_ACTION · SIMULATED_ACTION

PHASE 4.1 // MISP

misp.search_ioc
misp.get_event
misp.get_attribute

Status: READ_ONLY ✅

PHASE 4.2 // ELASTIC

elastic.search_alerts
elastic.search_events
elastic.get_document

Status: READ_ONLY ✅

PHASE 4.3 // IDENTITY / IAM

iam.get_user
iam.get_account_status
iam.get_mfa_status
iam.get_group_membership

Status: READ_ONLY ✅

PHASE 4.4 // ASSET / CMDB

asset.get_asset
asset.get_ip_context
asset.get_criticality
asset.get_edr_status

Status: READ_ONLY ✅

PHASE 4.5 // EMAIL / PHISHING

email.get_message_metadata
email.get_headers
email.get_authentication_results
email.get_attachment_metadata

Status: NEXT ⏭️

O objetivo é fornecer evidências ao AG-07 Phishing Analyst sem abrir URLs, executar anexos ou baixar conteúdo perigoso.

11 // TOOL EXECUTION PATH

flowchart LR
    A[AGENT] --> B[ToolRequest]
    B --> C{AUTHORIZATION}
    C -->|DENIED| X[FAIL CLOSED]
    C -->|ALLOWED| D[ToolRegistry]
    D --> E[ToolRuntime]
    E --> F[READ-ONLY INTEGRATION]
    F --> G[ToolResult]
    G --> H[Evidence]

12 // AUDIT STREAM

CASE_CREATED
CASE_UPDATED
AGENT_STARTED
AGENT_COMPLETED
TOOL_CALLED
EVIDENCE_ADDED
QA_REVIEWED
DECISION_CREATED
ERROR
HUMAN_ACTION

A auditoria registra:

audit_id
case_id
correlation_id
actor
action
status
message
references
payload
timestamp

Eventos anteriores não são sobrescritos.

13 // ESCALATION LOGIC

CLOSED_N1

Requisitos conservadores:

confiança elevada;

QA aprovado;

evidências suficientes;

playbook concluído;

sem regra obrigatória de escalonamento;

sem comprometimento crítico confirmado.

ESCALATED_N2

Prioridade de escalonamento em casos como:

conta privilegiada;

ativo crítico;

IOC malicioso confirmado;

movimentação lateral;

exfiltração;

comprometimento confirmado;

alerta não suportado;

QA falhando após o limite de retries.

14 // ALERT CATALOG

AUTH_BRUTE_FORCE
SUSPICIOUS_LOGIN
CREDENTIAL_EXPOSURE
PHISHING
MALWARE_DETECTION
SUSPICIOUS_POWERSHELL
MALICIOUS_IOC
PRIVILEGED_ACCOUNT_ACTIVITY
LATERAL_MOVEMENT_SUSPECTED
DATA_EXFILTRATION_SUSPECTED
UNSUPPORTED

UNSUPPORTED não é interpretado livremente: deve ser escalado.

15 // STORAGE

<table>
<tr>
<td width="50%">

JSON

O CaseState pode ser serializado e restaurado.

storage/incidents/

</td>
<td width="50%">

SQLITE

Banco local padrão:

storage/database/
agentic_soc.db

Estruturas principais:

cases
audit_events

</td>
</tr>
</table>

16 // LOCAL AI

O laboratório foi preparado para uso de IA local com Ollama.

Benefícios:

execução local;

menor dependência de APIs externas;

experimentação com modelos abertos;

maior controle sobre dados do laboratório;

separação entre interpretação e comprovação.

LLM  → interpreta
TOOL → verifica
RULE → governa
HUMAN → decide quando necessário

17 // KNOWLEDGE / RAG

Estrutura preparada:

knowledge/
├── mitre/
├── playbooks/
├── policies/
└── runbooks/

Metadados esperados:

chunk_id
document_name
document_type
section
content
similarity_score
source_path
metadata

Implementação completa: PHASE 5

18 // MCP

Estrutura planejada:

mcp/
├── client/
└── server/

Implementação completa: PHASE 6

19 // TEST MATRIX

MODULE

TESTS

STATUS

Foundation

8

✅

Phase 2

20

✅

Phase 3

19

✅

Phase 4.0 — Tools

20

✅

Phase 4.1 — MISP

17

✅

Phase 4.2 — Elastic

19

✅

Phase 4.3 — Identity / IAM

24

✅

Phase 4.4 — Asset / CMDB

24

✅

TOTAL

151

PASS

python -m pytest -q

Expected:

151 passed

20 // TECHNOLOGY STACK

<table>
<tr>
<td align="center"><strong>Python</strong><br><code>3.14</code></td>
<td align="center"><strong>Pydantic</strong><br><code>v2</code></td>
<td align="center"><strong>Ollama</strong><br><code>Local AI</code></td>
<td align="center"><strong>SQLite</strong><br><code>Storage</code></td>
</tr>
<tr>
<td align="center"><strong>HTTPX</strong><br><code>HTTP Client</code></td>
<td align="center"><strong>Pytest</strong><br><code>Testing</code></td>
<td align="center"><strong>Git</strong><br><code>Versioning</code></td>
<td align="center"><strong>GitHub</strong><br><code>Repository</code></td>
</tr>
</table>

Dependencies:

pydantic==2.13.5
ollama==0.6.2
numpy==2.5.3
pytest==9.1.1
httpx==0.28.1

21 // PROJECT TREE

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
├── assets/
│   └── banner-agentic-soc-n1-lab.png
│
├── core/
│   ├── config/
│   ├── llm/
│   ├── orchestrator/
│   ├── permissions/
│   ├── schemas/
│   └── state/
│
├── docs/
├── knowledge/
├── mcp/
├── rag/
├── simulations/
│
├── storage/
│   ├── audit/
│   ├── database/
│   └── incidents/
│
├── tests/
│   ├── test_foundation.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   ├── test_phase4_misp.py
│   ├── test_phase4_elastic.py
│   ├── test_phase4_identity.py
│   └── test_phase4_asset.py
│
├── tools/
│   ├── threat_intel/
│   ├── elastic/
│   ├── identity/
│   └── asset/
│
├── main.py
├── requirements.txt
└── README.md

22 // BOOT SEQUENCE

git clone https://github.com/Paula-Tech007/Agentic-SOC-N1-Lab.git
cd Agentic-SOC-N1-Lab

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pytest -q

23 // ENVIRONMENT

Nunca versionar credenciais reais.

# MISP
MISP_URL
MISP_API_KEY
MISP_VERIFY_SSL
MISP_TIMEOUT_SECONDS

# ELASTIC
ELASTIC_URL
ELASTIC_API_KEY
ELASTIC_VERIFY_SSL
ELASTIC_TIMEOUT_SECONDS
ELASTIC_ALERTS_INDEX
ELASTIC_EVENTS_INDEX

# IDENTITY / IAM
IAM_URL
IAM_API_TOKEN
IAM_PROVIDER
IAM_VERIFY_SSL
IAM_TIMEOUT_SECONDS

# ASSET / CMDB
ASSET_URL
ASSET_API_TOKEN
ASSET_PROVIDER
ASSET_VERIFY_SSL
ASSET_TIMEOUT_SECONDS

24 // ROADMAP

[██████████] PHASE 0    Scope / Architecture / Governance
[██████████] PHASE 1    Technical Foundation
[██████████] PHASE 2    Schemas / State / Persistence / Audit
[██████████] PHASE 3    Agents / Runtime / Orchestration
[██████████] PHASE 4.0  Tools Foundation
[██████████] PHASE 4.1  MISP Read-Only
[██████████] PHASE 4.2  Elastic Read-Only
[██████████] PHASE 4.3  Identity / IAM Read-Only
[██████████] PHASE 4.4  Asset / CMDB Read-Only
[░░░░░░░░░░] PHASE 4.5  Email / Phishing Metadata
[░░░░░░░░░░] PHASE 5    Knowledge / RAG
[░░░░░░░░░░] PHASE 6    MCP
[░░░░░░░░░░] PHASE 7    Multi-Agent SOC End-to-End

Todas as fases são evoluções do mesmo projeto e do mesmo repositório.

25 // CURRENT CHECKPOINT

╔════════════════════════════════════════════════════╗
║ AGENTIC SOC N1 LAB // CHECKPOINT                   ║
╠════════════════════════════════════════════════════╣
║ PHASE 4.4                         COMPLETE         ║
║ ASSET / CMDB                      READ_ONLY        ║
║ MISP                              READ_ONLY        ║
║ ELASTIC                           READ_ONLY        ║
║ IDENTITY / IAM                    READ_ONLY        ║
║ AG-06                             ALIGNED          ║
║ TOOL GOVERNANCE                   ACTIVE           ║
║ TEST SUITE                        151 PASSED        ║
║ NEXT                              PHASE 4.5        ║
╚════════════════════════════════════════════════════╝

26 // SAFETY NOTICE

Este repositório é um laboratório educacional e defensivo de Segurança Cibernética.

As integrações atuais foram implementadas para consulta controlada, validação de arquitetura e estudo de automação defensiva.

O projeto não representa autorização para execução automática de ações críticas em ambientes de produção.

<div align="center">

// PAULA SABINO

Cybersecurity · SOC · Security Automation · AI for Security




<br>

DEFENSIVE AUTOMATION // VERIFIABLE EVIDENCE // CONTROLLED AI

</div>