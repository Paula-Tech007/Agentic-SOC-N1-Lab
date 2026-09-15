<div align="center">

<img src="assets/banner-agentic-soc-n1-lab.png" alt="Agentic SOC N1 Lab" width="100%">

<br>









<br>

SOC N1 multiagente com IA local, ferramentas defensivas, evidências verificáveis, governança e escalonamento humano.

A LLM interpreta. A ferramenta comprova.

</div>

📌 Visão rápida

Item

Estado atual

Arquitetura

Multiagente

Agentes oficiais

12

Fase concluída

Fase 4.4 — Asset / CMDB Read-Only

Testes automatizados

151 passed

Integrações concluídas

MISP · Elastic · Identity/IAM · Asset/CMDB

Política de integração

READ_ONLY

Ações críticas autônomas

Nenhuma

Escalonamento humano

Disponível

Próxima etapa

Fase 4.5 — Email / Phishing Metadata Read-Only

🔎 Sobre o projeto

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança voltado à automação controlada de atividades operacionais de um SOC N1.

A arquitetura combina agentes especializados, IA local, regras determinísticas, ferramentas defensivas, enriquecimento de contexto, persistência, auditoria e revisão de qualidade.

O objetivo é reduzir tarefas repetitivas do N1 sem entregar autoridade irrestrita ao modelo de linguagem.

O laboratório foi projetado para

receber e normalizar alertas;

classificar eventos e severidade;

enriquecer IOCs;

consultar Threat Intelligence;

analisar identidades, MFA e privilégios;

recuperar contexto de ativos;

investigar phishing;

consultar conhecimento interno;

consolidar evidências;

produzir uma investigação estruturada;

revisar a qualidade da análise;

documentar o caso;

fechar no N1 ou escalar para N2/humano;

registrar toda a execução em auditoria.

🧠 Arquitetura geral

flowchart TD
    A[Alerta / Evento] --> B[AG-02 Alert Intake]
    B --> C[AG-03 Triage]
    C --> S[AG-01 SOC Supervisor]

    S --> D[AG-04 Threat Intelligence]
    S --> E[AG-05 Identity]
    S --> F[AG-06 Asset Context]
    S --> G[AG-07 Phishing]
    S --> H[AG-08 Knowledge / RAG]

    D --> I[AG-09 Incident Analyst]
    E --> I
    F --> I
    G --> I
    H --> I

    I --> J[AG-10 Reflection / QA]

    J -->|Reprovado| S
    J -->|Aprovado| K[AG-11 Case Management]

    K --> L[AG-12 Escalation]

    L --> M[CLOSED_N1]
    L --> N[ESCALATED_N2]
    L --> O[WAITING_HUMAN]

O fluxo automático completo Supervisor → Especialistas → Supervisor será consolidado na Fase 7.

🤖 Os 12 agentes

ID

Agente

Responsabilidade

AG-01

SOC Supervisor Agent

Coordenação e roteamento da investigação

AG-02

Alert Intake Agent

Recebimento, validação e normalização

AG-03

Triage Analyst Agent

Classificação, severidade e triagem

AG-04

Threat Intelligence Agent

Enriquecimento de IOCs e Threat Intelligence

AG-05

Identity Analyst Agent

Usuário, conta, MFA, grupos e privilégios

AG-06

Asset Context Agent

Ativo, IP, criticidade e EDR

AG-07

Phishing Analyst Agent

Metadados, cabeçalhos, autenticação e anexos

AG-08

Knowledge / RAG Agent

Políticas, playbooks, runbooks e conhecimento

AG-09

Incident Analyst Agent

Consolidação das evidências e investigação

AG-10

Reflection / QA Agent

Revisão, lacunas, inconsistências e qualidade

AG-11

Case Management Agent

Histórico e documentação do caso

AG-12

Escalation Agent

Fechamento N1, N2 ou ação humana

🔄 Ciclo de vida do caso

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

Estados auxiliares:

WAITING_DATA · WAITING_HUMAN · RETRYING · FAILED · CANCELLED

Estados de execução dos agentes:

PENDING · RUNNING · COMPLETED · FAILED · SKIPPED

🧩 CaseState

O CaseState funciona como a ficha viva da investigação.

Ele concentra os dados produzidos por todo o pipeline:

Alert
  + IOCs
  + Identity Context
  + Asset Context
  + Evidence
  + Triage
  + Threat Intelligence
  + Phishing
  + Knowledge / RAG
  + Investigation
  + QA
  + Escalation
  + Audit
  + Workflow
  = CaseState

Principais características:

case_id e correlation_id;

versionamento;

timestamps;

serialização;

persistência;

prevenção de evidência duplicada;

prevenção de auditoria duplicada;

rastreabilidade ponta a ponta.

🧾 Evidência antes da conclusão

Toda conclusão relevante deve estar associada a dados verificáveis.

HARD RULES
    >
TOOL DATA
    >
EVIDENCE
    >
CONSOLIDATED CONTEXT
    >
LLM INTERPRETATION

Fontes previstas e implementadas ao longo do projeto:

alerta original;

MISP;

Elastic;

IAM;

Asset / CMDB;

e-mail;

logs;

RAG;

investigação consolidada.

Uma resposta isolada de LLM nunca é considerada evidência suficiente de comprometimento.

🔐 Segurança e governança

A arquitetura utiliza princípios de segurança desde a fundação:

Controle

Aplicação

Deny by default

O acesso só existe quando explicitamente autorizado

Least privilege

Cada agente possui somente as ferramentas necessárias

Evidence first

Evidência antes da conclusão

Fail closed

Falhas não liberam acesso adicional

Bounded loops

Loops e retries possuem limites

Immutable raw event

O evento bruto não pode ser alterado silenciosamente

Append-only audit

Eventos anteriores de auditoria não são sobrescritos

Human escalation

Casos sensíveis podem aguardar decisão humana

No unrestricted shell

Agentes não recebem shell irrestrito

No critical autonomy

Ações críticas reais continuam bloqueadas

Ações críticas não executadas automaticamente

troca real de senha;

desativação ou exclusão de conta;

bloqueio real de IP;

alteração real de firewall;

isolamento real de endpoint;

encerramento real de processo;

exclusão real de arquivo;

abertura automática de URL;

execução ou download automático de anexo.

Quando necessário, o sistema trabalha apenas com:

RECOMMENDED_ACTION ou SIMULATED_ACTION

🛠️ Fase 4 — Tools e integrações

A Fase 4 introduz a camada governada de acesso a sistemas externos.

✅ Fase 4.0 — Fundação de Tools

Implementado:

catálogo oficial de ferramentas;

autorização;

registry;

runtime;

timeout;

retries limitados;

validação de binding;

fail closed;

evidência obrigatória;

bloqueio de ferramentas proibidas.

Modos definidos:

READ_ONLY · RECOMMENDED_ACTION · SIMULATED_ACTION

✅ Fase 4.1 — MISP Read-Only

Ferramentas:

misp.search_ioc
misp.get_event
misp.get_attribute

Controles:

API key;

rotas permitidas;

validação de resposta;

timeout;

tratamento de erros;

nenhuma operação de escrita.

✅ Fase 4.2 — Elastic Read-Only

Ferramentas:

elastic.search_alerts
elastic.search_events
elastic.get_document

Controles:

índices autorizados;

rotas controladas;

endpoints de escrita bloqueados;

timeout;

retries limitados;

fail closed.

✅ Fase 4.3 — Identity / IAM Read-Only

Ferramentas:

iam.get_user
iam.get_account_status
iam.get_mfa_status
iam.get_group_membership

Contexto recuperado:

usuário;

status da conta;

MFA;

grupos;

informações de identidade.

✅ Fase 4.4 — Asset / CMDB Read-Only

Ferramentas:

asset.get_asset
asset.get_ip_context
asset.get_criticality
asset.get_edr_status

Contexto recuperado:

ativo;

hostname;

IP;

criticidade;

sistema operacional;

exposição;

gerenciamento;

status de EDR;

metadados adicionais.

O AG-06 Asset Context Agent utiliza somente os IDs oficiais da camada de ferramentas.

⏭️ Fase 4.5 — Email / Phishing Metadata Read-Only

Próxima integração:

email.get_message_metadata
email.get_headers
email.get_authentication_results
email.get_attachment_metadata

Objetivo:

fornecer evidências ao AG-07 Phishing Analyst Agent sem abrir URLs, executar anexos ou baixar conteúdo perigoso.

🔒 Fluxo de autorização de ferramentas

flowchart LR
    A[Agent] --> B[ToolRequest]
    B --> C{Authorization}
    C -->|Denied| D[Fail Closed]
    C -->|Allowed| E[ToolRegistry]
    E --> F[ToolRuntime]
    F --> G[Read-Only Integration]
    G --> H[ToolResult + Evidence]

🧾 Auditoria

Eventos relevantes podem ser registrados como:

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

identificador do evento;

caso;

correlação;

ator;

ação;

status;

mensagem;

referências;

payload;

timestamp.

A filosofia é append-only.

🚨 Escalonamento

O fechamento automático no N1 é propositalmente conservador.

Fechamento N1

Pode ocorrer quando houver:

confiança elevada;

QA aprovado;

evidências suficientes;

playbook concluído;

ausência de regra obrigatória de escalonamento;

ausência de comprometimento crítico confirmado.

Escalonamento prioritário

conta privilegiada;

ativo crítico;

IOC malicioso confirmado;

movimentação lateral;

exfiltração de dados;

comprometimento confirmado;

alerta não suportado;

falha de QA após o limite de retries.

As hard rules possuem prioridade sobre interpretações da LLM.

📋 Catálogo inicial de alertas

Categoria

Status

AUTH_BRUTE_FORCE

Suportado

SUSPICIOUS_LOGIN

Suportado

CREDENTIAL_EXPOSURE

Suportado

PHISHING

Suportado

MALWARE_DETECTION

Suportado

SUSPICIOUS_POWERSHELL

Suportado

MALICIOUS_IOC

Suportado

PRIVILEGED_ACCOUNT_ACTIVITY

Suportado

LATERAL_MOVEMENT_SUSPECTED

Suportado

DATA_EXFILTRATION_SUSPECTED

Suportado

UNSUPPORTED

Escalonar

💾 Persistência

JSON

O CaseState pode ser serializado e restaurado.

Incidentes operacionais:

storage/incidents/

SQLite

Banco local padrão:

storage/database/agentic_soc.db

Estruturas principais:

cases
audit_events

🧠 Inteligência Artificial local

O laboratório foi projetado para trabalhar com Ollama, permitindo:

desenvolvimento local;

testes sem dependência obrigatória de APIs externas;

maior controle dos dados do laboratório;

experimentação com modelos abertos.

A camada de IA permanece separada da camada de comprovação por ferramentas.

📚 Knowledge / RAG

Estrutura prevista:

knowledge/
├── mitre/
├── playbooks/
├── policies/
└── runbooks/

Cada conteúdo recuperado deverá possuir origem rastreável.

A implementação completa do RAG pertence à Fase 5.

🔌 MCP

Estrutura prevista:

mcp/
├── client/
└── server/

A implementação completa está planejada para a Fase 6.

🧪 Testes automatizados

Conjunto

Testes

Fundação

8

Fase 2

20

Fase 3

19

Fase 4.0 — Tools

20

Fase 4.1 — MISP

17

Fase 4.2 — Elastic

19

Fase 4.3 — Identity / IAM

24

Fase 4.4 — Asset / CMDB

24

Total

151

Resultado atual:

151 passed

Executar:

python -m pytest -q

⚙️ Tecnologias

Tecnologia

Utilização

Python 3.14

Desenvolvimento principal

Pydantic v2

Schemas e validação

Ollama

IA local

SQLite

Persistência

HTTPX

Clientes HTTP controlados

Pytest

Testes automatizados

Git

Controle de versão

GitHub

Repositório e documentação

Mermaid

Diagramas de arquitetura

Dependências principais:

pydantic==2.13.5
ollama==0.6.2
numpy==2.5.3
pytest==9.1.1
httpx==0.28.1

📂 Estrutura do projeto

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

▶️ Executando o projeto

git clone https://github.com/Paula-Tech007/Agentic-SOC-N1-Lab.git
cd Agentic-SOC-N1-Lab

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pytest -q

Resultado esperado no estado atual:

151 passed

🔑 Variáveis de ambiente

As credenciais devem permanecer fora do Git.

MISP

MISP_URL
MISP_API_KEY
MISP_VERIFY_SSL
MISP_TIMEOUT_SECONDS

Elastic

ELASTIC_URL
ELASTIC_API_KEY
ELASTIC_VERIFY_SSL
ELASTIC_TIMEOUT_SECONDS
ELASTIC_ALERTS_INDEX
ELASTIC_EVENTS_INDEX

Identity / IAM

IAM_URL
IAM_API_TOKEN
IAM_PROVIDER
IAM_VERIFY_SSL
IAM_TIMEOUT_SECONDS

Asset / CMDB

ASSET_URL
ASSET_API_TOKEN
ASSET_PROVIDER
ASSET_VERIFY_SSL
ASSET_TIMEOUT_SECONDS

Nunca publique tokens, API keys, senhas ou arquivos .env reais no repositório.

🗺️ Roadmap

Fase

Escopo

Status

0

Escopo, arquitetura e governança

✅ Concluída

1

Fundação técnica

✅ Concluída

2

Schemas, CaseState, persistência e auditoria

✅ Concluída

3

Agentes, runtime e orquestração

✅ Concluída

4.0

Fundação de Tools

✅ Concluída

4.1

MISP Read-Only

✅ Concluída

4.2

Elastic Read-Only

✅ Concluída

4.3

Identity / IAM Read-Only

✅ Concluída

4.4

Asset / CMDB Read-Only

✅ Concluída

4.5

Email / Phishing Metadata Read-Only

⏭️ Próxima

5

Knowledge / RAG

🗓️ Planejada

6

MCP

🗓️ Planejada

7

SOC Multiagente End-to-End

🗓️ Planejada

Todas as fases são evoluções do mesmo projeto e do mesmo repositório.

<details>
<summary><strong>📐 Decisões de arquitetura</strong></summary>

<br>

Separação de responsabilidade

LLM
├── interpreta
├── resume
├── correlaciona contexto
└── propõe conclusões

TOOLS
├── consultam sistemas
├── recuperam dados
├── verificam fatos
└── produzem evidências

GOVERNANÇA
├── controla permissões
├── aplica hard rules
├── limita loops e retries
├── exige rastreabilidade
└── permite escalonamento humano

Filosofia operacional

A arquitetura não delega autoridade irrestrita ao modelo.

A IA participa da interpretação.

As ferramentas comprovam fatos.

A governança determina o que pode ou não ser executado.

</details>

<details>
<summary><strong>📎 Imutabilidade e integridade</strong></summary>

<br>

raw_event

O evento bruto recebido é preservado em estrutura imutável.

Evidências

Evidências são tratadas como registros imutáveis.

Auditoria

Eventos de auditoria seguem modelo append-only.

Isso reduz o risco de alterações silenciosas durante a investigação.

</details>

⚠️ Aviso

Este repositório é um laboratório educacional e defensivo de Segurança Cibernética.

As integrações atuais foram construídas para consulta controlada, validação de arquitetura e estudo de automação defensiva.

O projeto não representa autorização para execução automática de ações críticas em ambientes de produção.

<div align="center">

👩‍💻 Paula Sabino

Cybersecurity · SOC · Security Automation · AI for Security

GitHub · LinkedIn

<br>

🛡️ Agentic SOC N1 Lab

AI assists. Evidence validates. Governance decides.

</div>