<p align="center">

  <img

    src="assets/banner-agentic-soc-n1-lab.png"

    alt="Agentic SOC N1 Lab"

    width="100%"

  />

</p>

<h1 align="center">🛡️ Agentic SOC N1 Lab</h1>

<p align="center">

  <strong>SOC N1 Multiagente com Inteligência Artificial Local</strong>

</p>

<p align="center">

  Triagem Automatizada • Evidências • Governança • Auditoria • RAG • MCP • E2E • Escalonamento Humano

</p>

<p align="center">

</p>


📌 Visão Geral

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança criado para estudar e implementar uma arquitetura multiagente voltada à automação de operações de SOC N1.

O projeto combina:

agentes especializados;

Inteligência Artificial local;

ferramentas defensivas;

integrações de segurança;

análise baseada em evidências;

RAG local;

regras determinísticas;

controle de permissões;

auditoria;

persistência;

QA;

escalonamento humano.

O princípio central da arquitetura é:

A LLM interpreta. A ferramenta comprova.

Nenhuma conclusão crítica deve depender exclusivamente da resposta de um modelo de linguagem.

O sistema prioriza informações verificáveis, evidências, dados de ferramentas e regras de governança.


📊 Status Atual

| Item | Estado |

|---|---|

| Projeto | Agentic SOC N1 Lab |

| Arquitetura | Multiagente |

| Agentes oficiais | 12 |

| Fase atual concluída | Fase 7 — SOC Multiagente Ponta a Ponta |

| Integrações concluídas | MISP, Elastic, IAM, Asset/CMDB e Email |

| Knowledge / RAG | ✅ Implementado |

| Embeddings | ✅ Local com Ollama |

| Índice vetorial | ✅ JSON local |

| Retrieval | ✅ Similaridade cosseno |

| Integração RAG → AG-08 | ✅ Implementada |

| MCP Foundation | ✅ Fase 6.0 concluída |

| MCP Client Local | ✅ Fase 6.1 concluída |

| Tools MCP governadas | 18 |

| Transporte MCP | STDIO / LOCAL_ONLY |

| Política MCP | READ_ONLY / FAIL_CLOSED |

| Orquestração E2E | ✅ Implementada |

| Runner E2E | ✅ Implementado |

| Retry / loops | ✅ Limitados e governados |

| Testes automatizados | 321 passed |

| Ações críticas autônomas | 0 |

| Política das integrações | READ_ONLY |

| Escalonamento humano | ✅ Disponível |

| Roadmap principal | Fases 0–7 concluídas |

| Repositório | Projeto único / evolução contínua |


🎯 Objetivo

O objetivo do laboratório é automatizar atividades repetitivas executadas normalmente por um SOC N1 sem entregar autoridade irrestrita à Inteligência Artificial.

O sistema foi projetado para:

receber alertas;

normalizar eventos;

realizar triagem;

classificar alertas;

enriquecer indicadores;

consultar Threat Intelligence;

analisar identidades;

consultar contexto de ativos;

investigar phishing;

recuperar conhecimento por RAG;

disponibilizar ferramentas defensivas por MCP;

executar o fluxo multiagente E2E de forma controlada;

correlacionar evidências;

construir investigações;

revisar qualidade;

documentar casos;

decidir fechamento ou escalonamento;

registrar auditoria.


🧠 Arquitetura Multiagente

O projeto possui 12 agentes especializados.

| ID | Agente | Responsabilidade |

|---|---|---|

| AG-01 | SOC Supervisor Agent | Coordena, roteia e controla a execução |

| AG-02 | Alert Intake Agent | Recebe, valida e normaliza alertas |

| AG-03 | Triage Analyst Agent | Classifica severidade, contexto e prioridade |

| AG-04 | Threat Intelligence Agent | Consulta e consolida inteligência de ameaças |

| AG-05 | Identity Analyst Agent | Analisa conta, MFA, grupos e privilégios |

| AG-06 | Asset Context Agent | Recupera ativo, IP, criticidade e EDR |

| AG-07 | Phishing Analyst Agent | Analisa metadados e autenticação de e-mail |

| AG-08 | Knowledge / RAG Agent | Recupera conhecimento, políticas e playbooks |

| AG-09 | Incident Analyst Agent | Consolida evidências e investigação |

| AG-10 | Reflection / QA Agent | Revisa qualidade, lacunas e inconsistências |

| AG-11 | Case Management Agent | Mantém documentação e histórico |

| AG-12 | Escalation Agent | Fecha N1, escala N2 ou aguarda humano |


🏗️ Arquitetura Geral


flowchart TD

    A[Alerta / Evento] --> B[AG-02 Alert Intake]

    B --> C[AG-03 Triage]

    C --> S[AG-01 SOC Supervisor]

    S --> TI[AG-04 Threat Intelligence]

    S --> ID[AG-05 Identity]

    S --> AS[AG-06 Asset Context]

    S --> PH[AG-07 Phishing]

    S --> KG[AG-08 Knowledge / RAG]

    TI --> INV[AG-09 Incident Analyst]

    ID --> INV

    AS --> INV

    PH --> INV

    KG --> INV

    INV --> QA[AG-10 Reflection / QA]

    QA -->|Reprovado| S

    QA -->|Aprovado| CM[AG-11 Case Management]

    CM --> ESC[AG-12 Escalation]

    ESC --> N1[CLOSED_N1]

    ESC --> N2[ESCALATED_N2]

    ESC --> HUM[WAITING_HUMAN]



    🔄 Ciclo de Vida do Caso

Estados principais:

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

   ↓

CLOSED_N1 / ESCALATED_N2

Estados auxiliares:

WAITING_DATA

WAITING_HUMAN

RETRYING

FAILED

CANCELLED

Estados dos agentes:

PENDING

RUNNING

COMPLETED

FAILED

SKIPPED



🧩 CaseState

O CaseState funciona como a ficha viva da investigação.

Ele concentra:

Alert

+

IOCs

+

Identidades

+

Ativos

+

Evidências

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

O estado possui suporte a:

case_id;

correlation_id;

alerta original;

IOCs;

identidades;

ativos;

evidências;

triagem;

Threat Intelligence;

phishing;

conhecimento;

investigação;

QA;

escalonamento;

auditoria;

workflow;

versionamento;

timestamps;

serialização;

persistência.



🔐 Segurança e Governança

A arquitetura utiliza princípios defensivos desde a fundação.

Regras principais

Deny by default

Least privilege

Fail closed

Evidência antes da conclusão

Dados de ferramentas acima de suposições da LLM

raw_event imutável

Evidências imutáveis

Auditoria append-only

Permissões por agente

Catálogo oficial de ferramentas

Timeouts

Retries limitados

Loops limitados

Rastreabilidade

QA obrigatório

Escalonamento humano

Sem shell irrestrito

Sem contenção crítica autônoma



🧰 Fase 4 — Tools e Integrações

A Fase 4 estabeleceu a infraestrutura controlada de ferramentas utilizadas pelos agentes.

Fase 4.0 — Fundação de Tools

Foram implementados:

ToolDefinition

ToolRequest

ToolResult

ToolAuthorization

ToolRegistry

ToolRuntime

ToolPolicy

Fluxo:

AGENTE

   ↓

ToolRequest

   ↓

Autorização

   ↓

ToolRegistry

   ↓

ToolRuntime

   ↓

Integração

   ↓

ToolResult

   ↓

Evidência

Política

As integrações atuais funcionam em:

READ_ONLY

Operações críticas de escrita continuam bloqueadas.

Fase 4.1 — MISP

Ferramentas oficiais:

misp.search_ioc

misp.get_event

misp.get_attribute

Objetivo:

consulta de IOC;

consulta de eventos;

consulta de atributos;

Threat Intelligence;

geração de evidência defensiva.

Fase 4.2 — Elastic

Ferramentas oficiais:

elastic.search_alerts

elastic.search_events

elastic.get_document

Objetivo:

consultar alertas;

recuperar eventos;

recuperar documentos;

apoiar triagem e investigação.

Fase 4.3 — Identity / IAM

Ferramentas oficiais:

iam.get_user

iam.get_account_status

iam.get_mfa_status

iam.get_group_membership

Objetivo:

consultar usuário;

validar status da conta;

verificar MFA;

consultar grupos e privilégios.

Fase 4.4 — Asset / CMDB

Ferramentas oficiais:

asset.get_asset

asset.get_ip_context

asset.get_criticality

asset.get_edr_status

Objetivo:

localizar ativo;

correlacionar IP;

validar criticidade;

verificar contexto de EDR.

Fase 4.5 — Email / Phishing

Ferramentas oficiais:

email.get_message_metadata

email.get_headers

email.get_authentication_results

email.get_attachment_metadata

Guardrails:

abrir URL                  BLOQUEADO

executar anexo             BLOQUEADO

baixar anexo               BLOQUEADO

operações de escrita       BLOQUEADAS

A integração fornece somente dados defensivos e metadados para o AG-07 Phishing Analyst Agent.



⛔ Ações Críticas Bloqueadas

O laboratório não autoriza automaticamente:

iam.reset_password

iam.disable_user

iam.delete_user

network.block_ip

network.unblock_ip

firewall.add_rule

firewall.delete_rule

firewall.modify_rule

endpoint.isolate_host

endpoint.kill_process

endpoint.delete_file

email.open_url

email.execute_attachment

email.download_attachment

Quando necessário, uma ação pode existir somente como:

RECOMMENDED_ACTION

ou:

SIMULATED_ACTION

Nenhuma contenção crítica real é executada automaticamente.



📚 Fase 5 — Knowledge / RAG Local

A Fase 5 implementa a camada real de recuperação de conhecimento do projeto.

O RAG utiliza conteúdo local autorizado armazenado em:

knowledge/

├── mitre/

├── playbooks/

├── policies/

└── runbooks/

A implementação é dividida em:

Etapa Função   Status

5.0   Configuração e contratos   ✅

5.1   Ingestão segura   ✅

5.2   Chunking ✅

5.3   Embeddings locais ✅

5.4   Índice vetorial JSON ✅

5.5   Retrieval / Similaridade   ✅

5.6   Integração RAG → AG-08  ✅

5.7   Testes formais ✅


🔄 Pipeline do RAG



📥 Ingestão Segura

O loader permite somente arquivos autorizados dentro de knowledge/.

Extensões suportadas:

.md

.txt

.json

.yaml

.yml

Guardrails:

caminho precisa permanecer dentro de knowledge/;

path traversal é bloqueado;

links simbólicos são bloqueados;

arquivos vazios são rejeitados;

arquivos muito grandes são rejeitados;

conteúdo deve utilizar UTF-8;

nenhuma execução de arquivo ocorre.



✂️ Chunking

A camada de chunking:

divide documentos em blocos controlados;

preserva origem;

preserva metadados;

reconhece seções Markdown;

utiliza overlap;

cria IDs determinísticos;

mantém posição original.

Configuração padrão:

Configuração   Valor

Chunk size  1200

Chunk overlap  200

Top-K 5

Similaridade mínima  0.25



🧬 Embeddings

O projeto utiliza:

Ollama

   ↓

embeddinggemma

Os embeddings são gerados localmente.

A camada rejeita:

vetores vazios;

valores não numéricos;

booleanos;

NaN;

infinito;

dimensões inconsistentes.



🗃️ Índice Vetorial Local

O índice utiliza formato:

JSON

Arquivo padrão:

rag/index/knowledge_index.json

O índice registra:

version

embedding_model

dimension

items

Características:

local;

validado;

escrita atômica;

não executável;

sem pickle;

sem banco vetorial externo obrigatório;

sem serviço em nuvem obrigatório.

O arquivo de índice gerado durante execução não é versionado no Git.


🔎 Retrieval

A busca semântica utiliza:

COSINE_SIMILARITY

Fluxo:

Consulta

   ↓

Embedding

   ↓

Comparação com índice

   ↓

Filtro de similaridade

   ↓

Ordenação

   ↓

Top-K

   ↓

RAGSearchResult

O retrieval:

consulta somente conhecimento indexado;

não realiza busca web;

não inventa chunks;

não inventa evidências;

respeita dimensão vetorial;

respeita score mínimo;

retorna fontes conhecidas.



🔗 Integração com AG-08

A integração final utiliza:

RAGSearchResult

      ↓

RAGKnowledgeAdapter

      ↓

KnowledgeChunk

      ↓

AgentExecutionRequest

      ↓

AG-08

      ↓

KnowledgeResult

O adaptador preserva:

chunk_id

document_id

document_name

document_type

section

content

similarity_score

source_path

metadata

O RAG não inventa:

resposta;

confiança;

evidência;

fonte;

chunk.



## 🔌 Fase 6 — MCP

A **Fase 6** implementou a camada MCP do Agentic SOC N1 Lab de forma local, defensiva e governada, preservando o princípio central do projeto:

> **A LLM interpreta. A ferramenta comprova.**

O MCP não substitui os controles internos. O **ToolRuntime continua soberano**, e nenhuma ferramenta pode contornar `ToolPolicy`, permissões por agente ou regras de governança.


### 6.0 — Fundação MCP Read-Only

Foram implementados:

- namespace oficial `soc_mcp`;
- contratos e configuração MCP;
- registry MCP;
- servidor MCP local;
- bridge MCP → ToolRuntime;
- transporte `STDIO`;
- execução `LOCAL_ONLY`;
- política `READ_ONLY`;
- comportamento `FAIL_CLOSED`;
- bloqueio de transporte de rede;
- bloqueio de ações críticas;
- contexto de agente/caso/correlação controlado pelo servidor;
- 18 ferramentas defensivas governadas.

```text
AGENTE
   ↓
MCP Client
   ↓
MCP Server
   ↓
MCP Bridge
   ↓
ToolRuntime
   ↓
ToolPolicy / Permissions
   ↓
ToolResult
   ↓
Evidence

6.1 — MCP Client Local Controlado

O cliente MCP local:

conecta somente ao servidor MCP local;

lista apenas ferramentas publicadas e autorizadas;

executa somente operações defensivas/read-only;

rejeita ferramentas não publicadas antes da chamada ao SDK;

não permite ao cliente definir livremente agent_id, case_id ou correlation_id;

respeita o contexto definido pelo servidor;

encerra a sessão de forma controlada.

As ações críticas permanecem fora do catálogo autorizado.



🔁 Fase 7 — SOC Multiagente Ponta a Ponta

A Fase 7 integrou os agentes e componentes existentes em um fluxo E2E controlado, auditável e orientado por evidências.

7.1 — Fundação E2E Controlada

Snapshot controlado, próximo agente pendente, estados terminais, bootstrap oficial pelo AG-02 e fail-closed para agentes desconhecidos.

7.2 — Supervisor Automático

O AG-01 SOC Supervisor seleciona e valida o especialista da etapa, respeitando o workflow oficial.

7.3 — Enriquecimento Automático

Coordena AG-04, AG-05, AG-06, AG-07 e AG-08, respeitando a ordem do workflow.

7.4 — Incident Analyst

O AG-09 consolida evidências e constrói a investigação estruturada.

7.5 — Reflection / QA + Retry

O AG-10 revisa qualidade, inconsistências e lacunas, podendo solicitar retry controlado apenas para agentes autorizados.

7.6 — Case Management

O AG-11 consolida documentação, histórico, evidências e estado do caso.

7.7 — Escalation / Finalização

O AG-12 finaliza o fluxo em:

CLOSED_N1
ESCALATED_N2
WAITING_HUMAN

7.8 — Runner E2E Integrado

O Phase7E2ERunner integra o workflow:

Alerta
   ↓
AG-02 Alert Intake
   ↓
AG-03 Triage
   ↓
AG-01 Supervisor
   ↓
AG-04 / AG-05 / AG-06 / AG-07 / AG-08
   ↓
AG-09 Incident Analyst
   ↓
AG-10 Reflection / QA
   ↓
Retry controlado quando necessário
   ↓
AG-11 Case Management
   ↓
AG-12 Escalation
   ↓
CLOSED_N1 / ESCALATED_N2 / WAITING_HUMAN

Guardrails mantidos:

deny by default;

least privilege;

fail closed;

ToolRuntime soberano;

MCP subordinado à ToolPolicy;

permissões por agente;

retries e loops limitados;

nenhuma contenção crítica autônoma;

humano/N2 sempre disponível;

auditoria e rastreabilidade.



🔍 Modelo de Evidências

Toda conclusão deve possuir rastreabilidade.

Fontes possíveis incluem:

alertas;

IOCs;

MISP;

Elastic;

IAM;

Asset/CMDB;

Email;

RAG;

investigação;

ferramentas;

auditoria.

Fluxo conceitual:

Informação observada

        ↓

     Evidência

        ↓

      Achado

        ↓

   Investigação

        ↓

 Reflection / QA

        ↓

      Decisão



🧾 Auditoria

A arquitetura utiliza AuditEvent.

Eventos possíveis incluem:

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

A auditoria segue o princípio:

append-only

Eventos anteriores não são sobrescritos.



💾 Persistência

JSON

Um CaseState pode ser serializado e restaurado.

Arquivos operacionais:

storage/incidents/

SQLite

Banco padrão:

storage/database/agentic_soc.db

Estruturas principais:

cases

audit_events

Os arquivos operacionais de banco não são versionados no Git.



🤖 Inteligência Artificial Local

O laboratório foi projetado para utilizar IA local por meio do Ollama.

Função   Modelo

LLM / agentes  qwen3:4b-instruct

Embeddings / RAG  embeddinggemma

Benefícios:

execução local;

maior controle sobre dados;

experimentação com modelos abertos;

menor dependência de APIs externas;

separação entre interpretação e comprovação.



⚙️ Tecnologias

Tecnologia  Uso

Python 3.14 Desenvolvimento principal

Pydantic 2.13.5   Schemas e validação

Ollama 0.6.2   Modelos locais

Qwen3 LLM

EmbeddingGemma Embeddings

NumPy 2.5.3 Operações numéricas

HTTPX 0.28.1   Clientes HTTP

SQLite   Persistência

Pytest 9.1.1   Testes automatizados

Git   Versionamento

GitHub   Repositório

Mermaid  Diagramas



🧪 Testes Automatizados

O projeto possui atualmente:

321 testes automatizados aprovados

Módulo

Testes

Status

Fundação

8

✅

Fase 2

20

✅

Fase 3

19

✅

Fase 4.0 — Tools

20

✅

Fase 4.1 — MISP

17

✅

Fase 4.2 — Elastic

19

✅

Fase 4.3 — Identity / IAM

24

✅

Fase 4.4 — Asset / CMDB

24

✅

Fase 4.5 — Email / Phishing

24

✅

Fase 5 — Knowledge / RAG

30

✅

Fase 6 — MCP

45

✅

Fase 7 — E2E

71

✅

TOTAL

321

✅

Executar:

python -m pytest -q

Resultado esperado:

321 passed

Os testes cobrem schemas, estado, persistência, agentes, ToolRuntime, integrações defensivas, RAG, MCP Server, MCP Client, Supervisor, enriquecimento, Incident Analyst, Reflection/QA, retry controlado, Case Management, Escalation, Runner E2E, guardrails e fail-closed.


📂 Estrutura Atual

Agentic-SOC-N1-Lab/
│
├── agents/
├── assets/
│   └── banner-agentic-soc-n1-lab.png
├── core/
│   ├── config/
│   ├── llm/
│   ├── orchestrator/
│   │   ├── e2e.py
│   │   ├── supervised.py
│   │   ├── enrichment.py
│   │   ├── incident_stage.py
│   │   ├── reflection_stage.py
│   │   ├── case_management_stage.py
│   │   ├── escalation_stage.py
│   │   └── phase7_runner.py
│   ├── permissions/
│   ├── schemas/
│   └── state/
├── docs/
├── knowledge/
├── rag/
├── soc_mcp/
│   ├── config.py
│   ├── contracts.py
│   ├── registry.py
│   ├── client/
│   │   ├── contracts.py
│   │   └── local.py
│   └── server/
│       ├── app.py
│       └── bridge.py
├── simulations/
├── storage/
├── tests/
│   ├── test_phase6_mcp.py
│   ├── test_phase6_1_mcp_client.py
│   ├── test_phase7_e2e.py
│   ├── test_phase7_2_supervisor.py
│   ├── test_phase7_3_enrichment.py
│   ├── test_phase7_4_incident.py
│   ├── test_phase7_5_reflection.py
│   ├── test_phase7_6_case_management.py
│   ├── test_phase7_7_escalation.py
│   └── test_phase7_8_runner.py
├── tools/
├── main.py
├── requirements.txt
└── README.md


🗺️ Roadmap

Fase

Escopo

Status

Fase 0

Escopo, arquitetura e governança

✅ Concluída

Fase 1

Fundação técnica

✅ Concluída

Fase 2

Schemas, estado, persistência e auditoria

✅ Concluída

Fase 3

Agentes, runtime e orquestração

✅ Concluída

Fase 4

Tools e integrações defensivas

✅ Concluída

Fase 5

Knowledge / RAG local

✅ Concluída

Fase 6

MCP local, read-only e governado

✅ Concluída

Fase 7

SOC multiagente ponta a ponta

✅ Concluída

Todas as fases são evoluções do mesmo projeto e do mesmo repositório.

Roadmap principal 0–7 concluído.


🚀 Executando o Projeto

Clone:

git clone https://github.com/Paula-Tech007/Agentic-SOC-N1-Lab.git

cd Agentic-SOC-N1-Lab

Crie o ambiente virtual:

python -m venv .venv

Ative:

..venv\Scripts\Activate.ps1

Instale as dependências:

python -m pip install -r requirements.txt

Execute os testes:

python -m pytest -q

Resultado atual:

321 passed



⚠️ Uso Defensivo

Este repositório é um laboratório educacional e defensivo de Segurança Cibernética.

Foi desenvolvido para:

pesquisa defensiva;

laboratórios SOC;

automação de segurança;

arquitetura de agentes;

Inteligência Artificial aplicada à segurança;

simulações controladas.

O projeto não representa autorização para executar ações críticas automaticamente em ambientes reais.


👩‍💻 Autora

Paula Sabino

Segurança Cibernética • SOC • Automação de Segurança • IA aplicada à Segurança

<p align="center">

  <strong>🛡️ Agentic SOC N1 Lab</strong>

</p>

<p align="center">

  Construindo um SOC multiagente auditável, governado e orientado por evidências.

</p>