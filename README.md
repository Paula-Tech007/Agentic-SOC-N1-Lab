<div align="center">

<img src="assets/banner-agentic-soc-n1-lab.png" alt="Agentic SOC N1 Lab" width="100%">

🛡️ Agentic SOC N1 Lab

SOC N1 Multiagente com Inteligência Artificial Local

Triagem Automatizada • Análise Baseada em Evidências • Governança • Auditoria • Escalonamento Humano










</div>

📌 Sobre o Projeto

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança voltado à construção de uma arquitetura multiagente para automação de operações de SOC N1.

O projeto combina agentes especializados, IA local, ferramentas defensivas, evidências, governança, auditoria e regras determinísticas para investigar alertas de segurança de forma controlada.

A arquitetura segue um princípio central:

A LLM interpreta. A ferramenta comprova.

Nenhuma conclusão crítica deve depender somente da resposta de um modelo de linguagem.

O sistema utiliza ferramentas autorizadas, evidências verificáveis, regras de governança, controle de permissões, execução limitada e possibilidade de escalonamento humano.

🎯 Objetivo

O objetivo é automatizar atividades repetitivas normalmente executadas pelo SOC N1, permitindo que analistas humanos concentrem seus esforços em tarefas de maior complexidade.

O sistema deverá ser capaz de:

receber alertas;

normalizar eventos;

realizar triagem;

enriquecer indicadores;

consultar Threat Intelligence;

analisar identidades;

analisar ativos;

investigar phishing;

consultar conhecimento via RAG;

consolidar evidências;

construir uma investigação;

revisar a qualidade da análise;

documentar o caso;

decidir fechamento ou escalonamento;

registrar todas as etapas em auditoria.

🧠 Arquitetura Multiagente

O projeto possui 12 agentes especializados.

ID

Agente

Responsabilidade

AG-01

SOC Supervisor Agent

Coordena o fluxo completo da investigação

AG-02

Alert Intake Agent

Recebe, valida e normaliza alertas

AG-03

Triage Analyst Agent

Realiza triagem, classificação e severidade

AG-04

Threat Intelligence Agent

Enriquece indicadores utilizando fontes autorizadas

AG-05

Identity Analyst Agent

Analisa contas, autenticação, MFA e privilégios

AG-06

Asset Context Agent

Analisa ativos, criticidade, exposição, gerenciamento e EDR

AG-07

Phishing Analyst Agent

Realiza análise especializada de phishing

AG-08

Knowledge / RAG Agent

Recupera playbooks, políticas, runbooks e conhecimento

AG-09

Incident Analyst Agent

Consolida evidências e investigação

AG-10

Reflection / QA Agent

Revisa evidências, inconsistências e qualidade

AG-11

Case Management Agent

Mantém documentação e registros do caso

AG-12

Escalation Agent

Aplica regras de fechamento e escalonamento

Todos os 12 agentes possuem implementação base integrada à camada de orquestração.

🏗️ Arquitetura Geral

flowchart TD
    A[Alerta de Segurança] --> B[AG-02 Alert Intake]
    B --> C[AG-03 Triage Analyst]
    C --> S[AG-01 SOC Supervisor]

    S --> D[AG-04 Threat Intelligence]
    S --> E[AG-05 Identity Analyst]
    S --> F[AG-06 Asset Context]
    S --> G[AG-07 Phishing Analyst]
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

O SOC Supervisor Agent decide quais especialistas precisam participar de cada investigação.

Nem todos os agentes precisam ser executados em todos os casos.

A execução multiagente ponta a ponta totalmente automática pertence à Fase 7. As fases atuais constroem e validam os componentes necessários sem antecipar o fluxo E2E final.

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

O CaseState funciona como a ficha viva do incidente.

Ele concentra as informações produzidas durante toda a investigação.

Alert
+
IOC
+
Identity
+
Asset
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

Atualmente o CaseState possui suporte a:

validação de correlation_id;

controle de versão;

timestamps;

IOCs;

identidades;

ativos;

evidências;

phishing;

conhecimento/RAG;

investigação;

QA;

escalonamento;

workflow;

auditoria;

prevenção de evidência duplicada;

prevenção de auditoria duplicada;

serialização JSON;

persistência SQLite.

🔐 Imutabilidade

A arquitetura protege informações que não devem ser alteradas silenciosamente durante uma investigação.

raw_event

O evento bruto recebido pelo sistema é convertido para uma estrutura imutável.

Evento recebido
      ↓
FrozenDict
      ↓
raw_event imutável

Isso ajuda a preservar o conteúdo original que iniciou a investigação.

Evidências

As evidências são registros imutáveis.

Depois que uma evidência é criada, seu conteúdo não pode ser modificado silenciosamente.

Auditoria

Os eventos de auditoria também são imutáveis.

O próprio objeto e seu payload interno ficam protegidos contra alteração posterior.

🔍 Modelo de Evidências

Toda conclusão deve possuir rastreabilidade.

Exemplos de fontes de evidência:

alertas;

IOCs;

Threat Intelligence;

identidade;

ativos;

e-mail;

logs;

ferramentas;

conhecimento;

análise de incidente.

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

📧 Análise de Phishing

O projeto possui schema e agente específicos para:

AG-07 Phishing Analyst Agent

O resultado estruturado permite registrar:

remetente;

destinatários;

assunto;

URLs;

anexos;

hashes;

SPF;

DKIM;

DMARC;

indicadores suspeitos;

evidências;

classificação;

severidade;

confiança;

resumo da análise.

A integração read-only com metadados de e-mail permanece prevista para a continuação da Fase 4.

📚 Knowledge / RAG

O projeto possui contrato estruturado para:

AG-08 Knowledge / RAG Agent

A arquitetura exige que informações recuperadas tenham origem conhecida.

Cada trecho recuperado registra:

chunk_id
document_name
document_type
section
content
similarity_score
source_path
metadata

Fluxo esperado:

Consulta
   ↓
Busca semântica
   ↓
Trecho recuperado
   ↓
Documento + seção + score
   ↓
KnowledgeResult

Uma resposta de conhecimento não deve existir sem fonte recuperada.

A implementação completa da camada RAG pertence à Fase 5.

🧾 Auditoria

A arquitetura possui AuditEvent para registrar acontecimentos importantes.

Exemplos:

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

Cada evento pode registrar:

audit_id;

case_id;

correlation_id;

tipo de evento;

tipo de ator;

identificador do ator;

ação;

status;

mensagem;

referências;

payload;

timestamp.

Append-only

A auditoria segue filosofia append-only.

Evento 1
   ↓
Evento 2
   ↓
Evento 3
   ↓
Evento 4

Eventos anteriores não são sobrescritos.

IDs duplicados são rejeitados no CaseState.

💾 Persistência

O projeto possui dois mecanismos principais de persistência.

JSON

Um CaseState completo pode ser serializado e restaurado:

CaseState
   ↓
JSON
   ↓
CaseState

Arquivos operacionais ficam em:

storage/incidents/

Esses arquivos não são versionados pelo Git.

SQLite

O banco padrão é:

storage/database/agentic_soc.db

A persistência inclui:

cases
audit_events

A tabela cases mantém o estado atual do incidente.

A tabela audit_events mantém o histórico append-only da auditoria.

O banco utiliza índices para facilitar consultas por:

correlation_id;

alert_id;

status;

case_id;

tipo de evento;

timestamp.

Arquivos SQLite operacionais são ignorados pelo Git.

🤖 Inteligência Artificial Local

O laboratório utiliza Ollama para execução local dos modelos.

Função

Modelo

LLM / raciocínio dos agentes

qwen3:4b-instruct

Embeddings / RAG

embeddinggemma

A execução local permite desenvolver e testar o núcleo da arquitetura sem depender obrigatoriamente de APIs externas.

⚙️ Tecnologias

Tecnologia

Utilização

Python 3.14

Desenvolvimento principal

Pydantic v2

Schemas e validação

Ollama

Execução local de modelos

Qwen3

LLM

EmbeddingGemma

Embeddings

SQLite

Persistência

HTTPX

Clientes HTTP defensivos e MockTransport

Pytest

Testes automatizados

Git

Controle de versão

GitHub

Versionamento

Mermaid

Diagramas

🧰 Fase 4 — Ferramentas e Integrações

A Fase 4 implementa a camada de ferramentas externas de forma governada.

Princípios obrigatórios:

deny-by-default;

menor privilégio;

autorização por agente;

contratos imutáveis de requisição e resultado;

timeout;

retry limitado;

validação de resultados;

fail-closed;

evidência obrigatória;

nenhum segredo em logs ou resultados;

nenhuma ação crítica real no MVP.

Fase 4.0 — Fundação de Tools ✅

Componentes implementados:

ToolDefinition
ToolPolicy
ToolRequest
ToolResult
ToolAuthorization
ToolRegistry
ToolRuntime

A camada define quais agentes podem utilizar cada ferramenta e bloqueia ferramentas proibidas.

Ações críticas como reset real de senha, desativação real de conta, bloqueio real de IP, alteração de firewall e isolamento real de endpoint não são disponibilizadas.

Fase 4.1 — MISP read-only ✅

Ferramentas oficiais:

misp.search_ioc
misp.get_event
misp.get_attribute

A integração permite somente consultas autorizadas.

Fase 4.2 — Elastic / Elasticsearch read-only ✅

Ferramentas oficiais:

elastic.search_alerts
elastic.search_events
elastic.get_document

A integração restringe operações aos índices configurados e bloqueia rotas de escrita.

Fase 4.3 — Identity / IAM read-only ✅

Ferramentas oficiais:

iam.get_user
iam.get_account_status
iam.get_mfa_status
iam.get_group_membership

O AG-05 utiliza os IDs oficiais da camada Tools.

Consultas IAM são read-only e não alteram usuário, senha, grupos ou estado da conta.

Fase 4.4 — Asset / CMDB read-only ✅

Ferramentas oficiais:

asset.get_asset
asset.get_ip_context
asset.get_criticality
asset.get_edr_status

O AG-06 utiliza somente os IDs oficiais da camada Tools.

A integração Asset / CMDB:

consulta informações gerais de ativo;

consulta contexto por endereço IP;

consulta criticidade cadastrada;

consulta estado registrado do EDR;

utiliza somente operações read-only;

bloqueia métodos e rotas não autorizados;

bloqueia URLs externas internas ao cliente;

não executa nenhuma ação real sobre EDR ou inventário.

Permissões principais:

asset.get_asset
→ AG-06, AG-09

asset.get_ip_context
→ AG-06, AG-09

asset.get_criticality
→ AG-03, AG-06, AG-09

asset.get_edr_status
→ AG-06, AG-09

Próxima etapa da Fase 4

A Fase 4 permanece em andamento.

Próxima integração prevista no checklist mestre:

Fase 4.5 — Email / Phishing metadata read-only

Ferramentas previstas no catálogo:

email.get_message_metadata
email.get_headers
email.get_authentication_results
email.get_attachment_metadata

A Fase 5, Fase 6 e Fase 7 não são antecipadas durante a implementação da Fase 4.

🧪 Testes Automatizados

O projeto possui atualmente:

151 testes automatizados aprovados

Distribuição atual:

8   testes de fundação
20  testes da Fase 2
19  testes da Fase 3
20  testes da Fase 4.0 — Fundação de Tools
17  testes da Fase 4.1 — MISP
19  testes da Fase 4.2 — Elastic
24  testes da Fase 4.3 — Identity / IAM
24  testes da Fase 4.4 — Asset / CMDB
-------------------------------------------
151 testes totais

Os testes validam, entre outros pontos:

schemas;

enums;

limites de confiança;

rejeição de campos desconhecidos;

imutabilidade de evidências;

imutabilidade de raw_event;

imutabilidade de auditoria;

imutabilidade do payload da auditoria;

criação e atualização do CaseState;

consistência de correlation_id;

prevenção de evidência duplicada;

prevenção de auditoria duplicada;

serialização e desserialização JSON;

workflow dos agentes;

QA e retry;

escalonamento;

persistência SQLite;

runtime dos agentes;

registro dos 12 agentes;

limite de passos do workflow;

autorização de ferramentas;

ToolRegistry;

ToolRuntime;

timeout e retry;

fail-closed;

deny-by-default;

MISP read-only;

Elastic read-only;

Identity / IAM read-only;

Asset / CMDB read-only;

bloqueio de operações não autorizadas;

tratamento de respostas HTTP inválidas;

tratamento de JSON inválido;

permissões específicas por agente;

alinhamento do AG-05 aos IDs oficiais;

alinhamento do AG-06 aos IDs oficiais.

Executar todos os testes:

python -m pytest -q

Resultado atual esperado:

151 passed

🛡️ Segurança e Governança

Princípios fundamentais:

Deny by default

Least privilege

Evidência antes da conclusão

Dados de ferramentas acima de suposições da LLM

raw_event imutável

Evidências imutáveis

Auditoria imutável

Auditoria append-only

Execução limitada

Fail closed

Escalonamento humano

Sem shell irrestrito

Sem contenção crítica autônoma

Uma resposta de LLM sozinha nunca deve ser considerada prova de comprometimento.

⛔ Restrições de Ações Autônomas

O MVP não executa automaticamente ações críticas como:

Troca de senha
Desativação de conta
Alteração de firewall
Bloqueio de IP
Isolamento de endpoint
Contenção em produção

Essas ações podem ser representadas como:

RECOMMENDED_ACTION

ou:

SIMULATED_ACTION

A execução real depende de autorização humana e política organizacional.

🚨 Decisão N1 / N2

O fechamento automático pelo N1 é conservador.

Critérios previstos incluem:

confiança mínima elevada;

QA aprovado;

evidências suficientes;

playbook concluído;

ausência de comprometimento confirmado;

ausência de regra obrigatória de escalonamento.

Situações que podem exigir N2:

conta privilegiada;

ativo crítico;

IOC malicioso confirmado;

movimentação lateral;

exfiltração;

comprometimento confirmado;

alerta não suportado;

falha de QA após limite de retries.

As hard rules possuem prioridade sobre interpretação da LLM.

📋 Tipos de Alertas Iniciais

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

Alertas não suportados devem ser escalados em vez de interpretados livremente.

📂 Estrutura do Projeto

Estrutura principal atual:

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
│   │   ├── base_agent.py
│   │   ├── contracts.py
│   │   ├── orchestrator.py
│   │   ├── registry.py
│   │   └── runtime.py
│   ├── permissions/
│   │   └── tool_policy.py
│   ├── schemas/
│   └── state/
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── SCOPE.md
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
│   ├── asset/
│   │   ├── __init__.py
│   │   ├── asset_client.py
│   │   ├── asset_config.py
│   │   └── asset_handlers.py
│   ├── authorization.py
│   ├── contracts.py
│   ├── registry.py
│   └── runtime.py
│
├── main.py
├── requirements.txt
└── README.md

Pastas reservadas para fases futuras permanecem no mesmo repositório.

🗺️ Roadmap

Fase

Escopo

Status

Fase 0

Escopo, arquitetura, governança e definição dos agentes

✅ Concluída

Fase 1

Fundação técnica, IA local e estrutura do projeto

✅ Concluída

Fase 2

Schemas, CaseState, imutabilidade, auditoria, persistência e testes

✅ Concluída

Fase 3

Runtime dos agentes e orquestração

✅ Concluída

Fase 4

Ferramentas e integrações de segurança

🚧 Em andamento — Fases 4.0, 4.1, 4.2, 4.3 e 4.4 concluídas

Fase 5

RAG e camada de conhecimento

⏳ Planejada

Fase 6

MCP

⏳ Planejada

Fase 7

Execução SOC multiagente ponta a ponta

⏳ Planejada

Todas as fases representam evoluções deste mesmo projeto e deste mesmo repositório.

Nenhuma fase cria um projeto ou repositório paralelo.

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
├── recuperam informações
├── validam fatos
└── produzem evidências


GOVERNANÇA
│
├── controla permissões
├── aplica hard rules
├── registra auditoria
├── revisa decisões
└── determina escalonamento

A separação entre interpretação, comprovação e governança é fundamental para o projeto.

🚀 Executando o Projeto

Criar ambiente virtual

python -m venv .venv

Ativar no Windows PowerShell

.\.venv\Scripts\Activate.ps1

Instalar dependências

pip install -r requirements.txt

Executar aplicação base

python main.py

Executar todos os testes

python -m pytest -q

Resultado atual:

151 passed

⚠️ Uso Defensivo

Este projeto é destinado a:

pesquisa defensiva em segurança;

laboratórios SOC;

estudos de automação;

arquitetura de agentes de IA;

engenharia de segurança;

simulações controladas.

O objetivo não é fornecer capacidade ofensiva autônoma.

👩‍💻 Autora

Paula Sabino

Segurança Cibernética • Automação de Segurança • IA Agêntica • SOC

GitHub: @Paula-Tech007

<div align="center">

🛡️ Agentic SOC N1 Lab

Construindo um SOC multiagente auditável, governado e orientado por evidências.

</div>