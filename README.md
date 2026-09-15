<div align="center">

<img src="assets/banner-agentic-soc-n1-lab.png" alt="Agentic SOC N1 Lab" width="100%">

🛡️ Agentic SOC N1 Lab

Multi-Agent AI Architecture for SOC N1 Automation

Security Engineering • Local AI • Evidence-Driven Analysis • Governance • Audit • Human Escalation

<br>












</div>

📊 Status do Projeto

Projeto ................................ Agentic SOC N1 Lab
Arquitetura ............................ Multiagente
Agentes oficiais ....................... 12
Fase atual concluída ................... 4.4 — Asset / CMDB Read-Only
Testes automatizados ................... 151 passed
Integrações concluídas ................. MISP / Elastic / IAM / Asset
Política atual das integrações ......... READ_ONLY
Execuções críticas autônomas ........... 0
Contenções reais ........................ 0
Escalonamento humano ................... Disponível
Repositório ............................ Projeto único / evolução contínua

Princípio central: a LLM interpreta; a ferramenta comprova.

🔎 Visão Geral

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança desenvolvido para estudar e implementar uma arquitetura multiagente capaz de automatizar atividades operacionais de SOC N1 de forma controlada, auditável e orientada por evidências.

O projeto combina:

agentes especializados;

Inteligência Artificial local;

regras determinísticas;

ferramentas defensivas autorizadas;

enriquecimento de contexto;

correlação de evidências;

auditoria append-only;

persistência de casos;

controle de permissões;

revisão de qualidade;

escalonamento N1 → N2 / humano.

O objetivo não é permitir que uma LLM tome decisões críticas livremente.

A arquitetura foi projetada para separar claramente:

INTERPRETAÇÃO
     ≠
EVIDÊNCIA
     ≠
DECISÃO
     ≠
AUTORIZAÇÃO
     ≠
EXECUÇÃO

Uma conclusão produzida por IA não é considerada prova por si só.

🎯 Objetivo

O laboratório busca automatizar tarefas repetitivas normalmente realizadas pelo SOC N1, mantendo rastreabilidade e limites de segurança.

O fluxo planejado deve ser capaz de:

receber e normalizar alertas;

classificar eventos;

calcular severidade;

identificar IOCs;

consultar Threat Intelligence;

analisar identidade;

verificar MFA e privilégios;

recuperar contexto do ativo;

avaliar criticidade;

investigar phishing;

consultar conhecimento interno;

consolidar evidências;

produzir uma investigação;

revisar a qualidade da análise;

documentar o caso;

decidir fechamento N1 ou escalonamento;

registrar toda a execução em auditoria.

🧠 Arquitetura End-to-End

                         AGENTIC SOC N1 LAB
                                │
                                ▼
                        SECURITY ALERT / EVENT
                                │
                                ▼
                      AG-02 ALERT INTAKE AGENT
                                │
                                ▼
                       AG-03 TRIAGE ANALYST
                                │
                                ▼
                      AG-01 SOC SUPERVISOR
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        AG-04 THREAT       AG-05 IDENTITY    AG-06 ASSET
        INTELLIGENCE          ANALYST           CONTEXT
              │                 │                 │
              ├─────────────────┼─────────────────┤
              │                 │                 │
              ▼                 ▼                 ▼
        AG-07 PHISHING    AG-08 KNOWLEDGE    SPECIALIZED
           ANALYST           / RAG              CONTEXT
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                      AG-09 INCIDENT ANALYST
                                │
                                ▼
                       AG-10 REFLECTION / QA
                         │                 │
                    REJECTED           APPROVED
                         │                 │
                         └──────► AG-01    ▼
                                      AG-11 CASE
                                      MANAGEMENT
                                           │
                                           ▼
                                    AG-12 ESCALATION
                                      │     │     │
                                      ▼     ▼     ▼
                                  CLOSED  N2   HUMAN
                                    N1

O fluxo automático completo Supervisor → Especialistas → Supervisor será consolidado na Fase 7.

🤖 Arquitetura Multiagente

O projeto possui 12 agentes oficiais.

ID

Agente

Responsabilidade principal

AG-01

SOC Supervisor Agent

Coordena o fluxo e decide quais agentes devem participar

AG-02

Alert Intake Agent

Recebe, valida e normaliza alertas

AG-03

Triage Analyst Agent

Classifica o alerta, severidade e contexto inicial

AG-04

Threat Intelligence Agent

Consulta e consolida inteligência de ameaças

AG-05

Identity Analyst Agent

Analisa identidade, conta, MFA, grupos e privilégios

AG-06

Asset Context Agent

Analisa ativo, IP, criticidade e status de EDR

AG-07

Phishing Analyst Agent

Analisa metadados, cabeçalhos, autenticação e anexos

AG-08

Knowledge / RAG Agent

Recupera políticas, playbooks, runbooks e conhecimento

AG-09

Incident Analyst Agent

Consolida evidências e constrói a investigação

AG-10

Reflection / QA Agent

Revisa qualidade, lacunas e inconsistências

AG-11

Case Management Agent

Mantém documentação e histórico do caso

AG-12

Escalation Agent

Decide fechamento N1, escalonamento N2 ou ação humana

🧩 CaseState

O CaseState funciona como a ficha viva da investigação.

Ele concentra os dados produzidos ao longo do fluxo:

Alert
  +
IOCs
  +
Identity Context
  +
Asset Context
  +
Evidence
  +
Triage
  +
Threat Intelligence
  +
Phishing
  +
Knowledge / RAG
  +
Investigation
  +
QA
  +
Escalation
  +
Audit
  +
Workflow
  =
CaseState

Principais características:

controle de case_id;

controle de correlation_id;

versionamento;

timestamps;

serialização;

persistência;

prevenção de duplicação de evidências;

prevenção de duplicação de auditoria;

suporte a estados do workflow;

rastreabilidade ponta a ponta.

🔄 Ciclo de Vida do Caso

Estados principais:

RECEIVED
   │
   ▼
NORMALIZING
   │
   ▼
TRIAGING
   │
   ▼
ENRICHING
   │
   ▼
INVESTIGATING
   │
   ▼
CORRELATING
   │
   ▼
REVIEWING
   │
   ▼
DOCUMENTING
   │
   ▼
DECIDING
   │
   ├──► CLOSED_N1
   └──► ESCALATED_N2

Estados auxiliares:

WAITING_DATA
WAITING_HUMAN
RETRYING
FAILED
CANCELLED

Estados de execução dos agentes:

PENDING
RUNNING
COMPLETED
FAILED
SKIPPED

🧾 Evidências e Rastreabilidade

Toda conclusão relevante deve estar associada a evidências verificáveis.

Fontes previstas:

alerta original;

IOC;

MISP;

Elastic;

IAM;

Asset / CMDB;

e-mail;

logs;

ferramentas SOC;

RAG;

investigação consolidada.

Fluxo conceitual:

INFORMAÇÃO OBSERVADA
        │
        ▼
     EVIDÊNCIA
        │
        ▼
      ACHADO
        │
        ▼
   INVESTIGAÇÃO
        │
        ▼
 REFLECTION / QA
        │
        ▼
     DECISÃO

A prioridade de confiança segue a filosofia:

HARD RULES
    >
TOOL DATA
    >
EVIDENCE
    >
CONSOLIDATED CONTEXT
    >
LLM INTERPRETATION

🔐 Imutabilidade

A arquitetura protege dados que não devem ser alterados silenciosamente.

raw_event

O evento bruto recebido é preservado como estrutura imutável.

Evento recebido
      │
      ▼
   FrozenDict
      │
      ▼
raw_event imutável

Evidências

Evidências são tratadas como registros imutáveis.

Auditoria

Eventos de auditoria também seguem abordagem imutável e append-only.

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

A auditoria registra, entre outros:

audit_id;

case_id;

correlation_id;

ator;

ação;

status;

mensagem;

referências;

payload;

timestamp.

Eventos anteriores não são sobrescritos.

🛠️ Fase 4 — Ferramentas e Integrações

A Fase 4 cria a camada controlada de acesso a ferramentas externas.

Todos os conectores implementados até a Fase 4.4 operam em READ_ONLY.

✅ Fase 4.0 — Fundação de Tools

Implementa a base de governança para ferramentas:

catálogo oficial;

políticas de autorização;

registro de handlers;

runtime;

timeout;

retry limitado;

validação de binding;

fail closed;

evidência obrigatória;

bloqueio de ferramentas proibidas.

Modos definidos

READ_ONLY
RECOMMENDED_ACTION
SIMULATED_ACTION

Nenhuma ferramenta crítica real foi liberada.

✅ Fase 4.1 — MISP Read-Only

Integração defensiva de Threat Intelligence.

Ferramentas:

misp.search_ioc
misp.get_event
misp.get_attribute

Características:

autenticação por API key;

acesso controlado;

rotas permitidas;

validação de resposta;

timeout;

tratamento de erro;

sem operações de escrita.

✅ Fase 4.2 — Elastic Read-Only

Integração com Elastic para consulta de alertas, eventos e documentos.

Ferramentas:

elastic.search_alerts
elastic.search_events
elastic.get_document

Controles:

índices autorizados;

rotas permitidas;

GET / POST de busca controlados;

bloqueio de endpoints de escrita;

timeout;

retry limitado;

fail closed.

✅ Fase 4.3 — Identity / IAM Read-Only

Integração de contexto de identidade.

Ferramentas:

iam.get_user
iam.get_account_status
iam.get_mfa_status
iam.get_group_membership

Permite ao AG-05 consultar:

usuário;

status da conta;

MFA;

grupos;

contexto de identidade.

Nenhuma alteração de usuário é executada.

✅ Fase 4.4 — Asset / CMDB Read-Only

Integração para contexto de ativos.

Ferramentas:

asset.get_asset
asset.get_ip_context
asset.get_criticality
asset.get_edr_status

Permite recuperar:

identificação do ativo;

hostname;

contexto por IP;

criticidade;

sistema operacional;

exposição;

gerenciamento;

status de EDR;

metadados adicionais.

O AG-06 Asset Context Agent utiliza somente os IDs oficiais da camada de ferramentas.

⏭️ Próxima Etapa — Fase 4.5

Integração Email / Phishing Metadata Read-Only.

Ferramentas previstas:

email.get_message_metadata
email.get_headers
email.get_authentication_results
email.get_attachment_metadata

Essa etapa fornecerá evidências ao AG-07 Phishing Analyst Agent sem abrir URLs, baixar anexos ou executar conteúdo.

🔒 Política de Ferramentas

A arquitetura adota deny-by-default.

Um agente só pode utilizar ferramentas explicitamente autorizadas.

Exemplo conceitual:

AGENTE
  │
  ▼
ToolRequest
  │
  ▼
Authorization
  │
  ├── DENIED ──► Fail Closed
  │
  ▼
ToolRegistry
  │
  ▼
ToolRuntime
  │
  ▼
Read-Only Integration
  │
  ▼
ToolResult + Evidence

Ferramentas críticas de escrita permanecem proibidas no MVP.

⛔ Ações Críticas Não Executadas

O projeto não executa autonomamente:

Troca real de senha
Desativação real de conta
Exclusão de usuário
Bloqueio real de IP
Alteração real de firewall
Isolamento real de endpoint
Encerramento real de processo
Exclusão real de arquivo
Abertura automática de URL
Execução automática de anexo
Download automático de anexo

Quando necessário, uma ação pode ser representada apenas como:

RECOMMENDED_ACTION

ou:

SIMULATED_ACTION

🛡️ Segurança e Governança

Princípios fundamentais:

deny by default;

least privilege;

evidência antes da conclusão;

ferramentas acima de suposições da LLM;

raw_event imutável;

evidências imutáveis;

auditoria append-only;

fail closed;

loops limitados;

retries limitados;

sem shell irrestrito;

sem contenção crítica autônoma;

possibilidade de escalonamento humano.

Uma resposta de LLM, isoladamente, nunca deve ser considerada evidência de comprometimento.

🚨 Regras de Escalonamento

O fechamento automático N1 é conservador.

Condições previstas para fechamento incluem:

confiança elevada;

QA aprovado;

evidências suficientes;

playbook concluído;

ausência de regra obrigatória de escalonamento;

ausência de comprometimento crítico confirmado.

Cenários com prioridade de escalonamento incluem:

conta privilegiada;

ativo crítico;

IOC malicioso confirmado;

movimentação lateral;

exfiltração de dados;

comprometimento confirmado;

tipo de alerta não suportado;

falha de QA após limite de retries.

As hard rules possuem prioridade sobre interpretações da LLM.

📋 Catálogo Inicial de Alertas

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

Alertas não suportados devem ser escalados, não interpretados livremente.

💾 Persistência

O laboratório trabalha com persistência de estado e auditoria.

JSON

O CaseState pode ser serializado e restaurado.

CaseState
   │
   ▼
  JSON
   │
   ▼
CaseState

Incidentes operacionais podem ser armazenados em:

storage/incidents/

SQLite

Banco local padrão:

storage/database/agentic_soc.db

Estruturas principais:

cases
audit_events

Arquivos operacionais locais permanecem fora do versionamento quando aplicável.

🧠 Inteligência Artificial Local

O laboratório foi projetado para trabalhar com IA local usando Ollama.

Isso permite:

desenvolvimento local;

redução de dependência de APIs externas;

maior controle sobre dados do laboratório;

experimentação com modelos abertos;

uso futuro no fluxo multiagente.

A camada de IA permanece separada da camada de comprovação por ferramentas.

📚 Knowledge / RAG

O projeto possui estrutura preparada para o AG-08 Knowledge / RAG Agent.

Fontes previstas:

knowledge/
├── mitre/
├── playbooks/
├── policies/
└── runbooks/

O RAG deverá recuperar conteúdo com origem rastreável:

chunk_id
document_name
document_type
section
content
similarity_score
source_path
metadata

A implementação completa do RAG pertence à Fase 5.

🔌 MCP

A estrutura para Model Context Protocol está prevista no projeto:

mcp/
├── client/
└── server/

A implementação completa está planejada para a Fase 6.

🧪 Testes Automatizados

Situação atual:

Foundation .......................... 8
Fase 2 ............................. 20
Fase 3 ............................. 19
Fase 4.0 ........................... 20
Fase 4.1 — MISP .................... 17
Fase 4.2 — Elastic ................. 19
Fase 4.3 — Identity / IAM .......... 24
Fase 4.4 — Asset / CMDB ............ 24
---------------------------------------
TOTAL ............................... 151

Resultado atual:

151 passed

Executar a suíte completa:

python -m pytest -q

Os testes cobrem, entre outros:

schemas;

validações;

imutabilidade;

CaseState;

auditoria;

persistência;

agentes;

runtime;

orquestração;

tool authorization;

tool registry;

tool runtime;

timeouts;

retries;

fail closed;

MISP;

Elastic;

IAM;

Asset / CMDB;

permissões por agente.

⚙️ Tecnologias

Tecnologia

Utilização

Python

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

Mermaid / Markdown

Arquitetura e documentação

Dependências principais atualmente utilizadas incluem:

pydantic==2.13.5
ollama==0.6.2
numpy==2.5.3
pytest==9.1.1
httpx==0.28.1

📂 Estrutura do Projeto

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
│
├── knowledge/
│   ├── mitre/
│   ├── playbooks/
│   ├── policies/
│   └── runbooks/
│
├── mcp/
│   ├── client/
│   └── server/
│
├── rag/
│   ├── embeddings/
│   ├── index/
│   ├── ingestion/
│   └── retrieval/
│
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

▶️ Executando o Projeto

1. Clonar o repositório

git clone https://github.com/Paula-Tech007/Agentic-SOC-N1-Lab.git
cd Agentic-SOC-N1-Lab

2. Criar o ambiente virtual

python -m venv .venv

3. Ativar no PowerShell

.\.venv\Scripts\Activate.ps1

4. Instalar dependências

python -m pip install -r requirements.txt

5. Executar os testes

python -m pytest -q

Resultado esperado no estado atual:

151 passed

🔑 Configuração de Integrações

As credenciais devem ser fornecidas por variáveis de ambiente.

Exemplos utilizados pelas integrações atuais:

MISP_URL
MISP_API_KEY
MISP_VERIFY_SSL
MISP_TIMEOUT_SECONDS

ELASTIC_URL
ELASTIC_API_KEY
ELASTIC_VERIFY_SSL
ELASTIC_TIMEOUT_SECONDS
ELASTIC_ALERTS_INDEX
ELASTIC_EVENTS_INDEX

IAM_URL
IAM_API_TOKEN
IAM_PROVIDER
IAM_VERIFY_SSL
IAM_TIMEOUT_SECONDS

ASSET_URL
ASSET_API_TOKEN
ASSET_PROVIDER
ASSET_VERIFY_SSL
ASSET_TIMEOUT_SECONDS

Nunca publique tokens, API keys, credenciais ou arquivos .env reais no GitHub.

🗺️ Roadmap

Fase

Escopo

Status

Fase 0

Escopo, arquitetura, agentes e governança

✅ Concluída

Fase 1

Fundação técnica do laboratório

✅ Concluída

Fase 2

Schemas, CaseState, persistência, auditoria e imutabilidade

✅ Concluída

Fase 3

Runtime dos agentes e orquestração

✅ Concluída

Fase 4.0

Fundação de Tools

✅ Concluída

Fase 4.1

MISP Read-Only

✅ Concluída

Fase 4.2

Elastic Read-Only

✅ Concluída

Fase 4.3

Identity / IAM Read-Only

✅ Concluída

Fase 4.4

Asset / CMDB Read-Only

✅ Concluída

Fase 4.5

Email / Phishing Metadata Read-Only

⏭️ Próxima

Fase 5

RAG e camada de conhecimento

🗓️ Planejada

Fase 6

MCP

🗓️ Planejada

Fase 7

SOC multiagente End-to-End

🗓️ Planejada

Todas as fases são evoluções do mesmo projeto e do mesmo repositório.

🧭 Filosofia da Arquitetura

LLM
│
├── interpreta contexto
├── resume informações
├── analisa evidências
└── propõe conclusões


FERRAMENTAS
│
├── consultam sistemas
├── recuperam dados
├── verificam fatos
└── produzem evidências


GOVERNANÇA
│
├── controla permissões
├── aplica hard rules
├── limita loops e retries
├── exige rastreabilidade
└── permite escalonamento humano

A arquitetura não delega autoridade irrestrita ao modelo.

📌 Estado Atual

Checkpoint atual do laboratório:

Fase 4.4 ............................ CONCLUÍDA
Asset / CMDB Read-Only .............. IMPLEMENTADO
AG-06 ............................... ALINHADO
Tool Governance ..................... ATIVA
MISP ................................ READ_ONLY
Elastic ............................. READ_ONLY
Identity / IAM ...................... READ_ONLY
Asset / CMDB ........................ READ_ONLY
Testes .............................. 151 PASSED
Próxima etapa ....................... FASE 4.5

⚠️ Aviso

Este repositório é um laboratório educacional e defensivo de Segurança Cibernética.

As integrações atuais foram construídas para consulta controlada e validação de arquitetura.

O projeto não deve ser interpretado como autorização para execução automática de ações críticas em ambientes de produção.

👩‍💻 Autoria

Paula Sabino

Cybersecurity • SOC • Security Automation • AI for Security

GitHub: @Paula-Tech007

LinkedIn: Paula Sabino

<div align="center">

🛡️ Agentic SOC N1 Lab

AI assists. Evidence validates. Governance decides.

</div>