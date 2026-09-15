<div align="center">

<img src="assets/banner-agentic-soc-n1-lab.png" alt="Agentic SOC N1 Lab" width="100%">

<br>

◢ AGENTIC SOC N1 LAB ◣

OPERAÇÕES SOC N1 // IA MULTIAGENTE // EVIDÊNCIAS // GOVERNANÇA

<br>











<br>

A IA INTERPRETA // A FERRAMENTA COMPROVA // A GOVERNANÇA CONTROLA // O HUMANO DECIDE

</div>

00 // TERMINAL DE ACESSO

┌──────────────────────────────────────────────────────────────────────────────┐
│ AGENTIC_SOC_N1_LAB :: AMBIENTE DE PESQUISA PARA OPERAÇÕES DE SEGURANÇA     │
├──────────────────────────────────────────────────────────────────────────────┤
│ SISTEMA ............... ONLINE / EM DESENVOLVIMENTO                         │
│ ARQUITETURA ........... MULTIAGENTE                                         │
│ AGENTES ............... 12 OFICIAIS                                         │
│ FASE .................. 4.4 CONCLUÍDA                                       │
│ TESTES ................ 151 APROVADOS                                       │
│ MODO DAS FERRAMENTAS .. SOMENTE LEITURA                                    │
│ AUTONOMIA CRÍTICA ..... DESABILITADA                                       │
│ ESCALONAMENTO HUMANO .. HABILITADO                                         │
│ PRÓXIMO ALVO .......... FASE 4.5 / E-MAIL + METADADOS DE PHISHING          │
└──────────────────────────────────────────────────────────────────────────────┘

01 // CONTROLE DA MISSÃO

O Agentic SOC N1 Lab é um laboratório de engenharia de segurança criado para estudar e implementar um SOC N1 multiagente, com agentes especializados, Inteligência Artificial local, ferramentas defensivas, evidências verificáveis, auditoria e escalonamento humano.

MISSÃO

Automatizar tarefas repetitivas do SOC N1 sem entregar autoridade irrestrita à IA.

PRINCÍPIO CENTRAL

IA / LLM        → interpreta contexto
FERRAMENTAS     → verificam fatos
EVIDÊNCIAS      → sustentam conclusões
HARD RULES      → impõem limites
GOVERNANÇA      → controla permissões
HUMANO          → decide quando necessário

02 // PIPELINE OPERACIONAL

flowchart LR
    A[ALERTA / EVENTO] --> B[AG-02<br/>RECEBIMENTO]
    B --> C[AG-03<br/>TRIAGEM]
    C --> S[AG-01<br/>SUPERVISOR SOC]

    S --> TI[AG-04<br/>THREAT INTEL]
    S --> ID[AG-05<br/>IDENTIDADE]
    S --> AS[AG-06<br/>ATIVO]
    S --> PH[AG-07<br/>PHISHING]
    S --> KG[AG-08<br/>CONHECIMENTO / RAG]

    TI --> INV[AG-09<br/>ANÁLISE DO INCIDENTE]
    ID --> INV
    AS --> INV
    PH --> INV
    KG --> INV

    INV --> QA[AG-10<br/>REFLEXÃO / QA]
    QA -->|REPROVADO| S
    QA -->|APROVADO| CM[AG-11<br/>GESTÃO DO CASO]

    CM --> ESC[AG-12<br/>ESCALONAMENTO]

    ESC --> N1[FECHADO NO N1]
    ESC --> N2[ESCALADO PARA N2]
    ESC --> HU[AGUARDANDO HUMANO]

O fluxo automático completo Supervisor → Especialistas → Supervisor pertence à Fase 7.

03 // GRADE DE AGENTES

<table>
<tr>
<td width="33%">

AG-01 // SUPERVISOR SOC

Coordena o fluxo, decide roteamento e controla a execução.

</td>
<td width="33%">

AG-02 // RECEBIMENTO

Recebe, valida e normaliza alertas.

</td>
<td width="33%">

AG-03 // TRIAGEM

Classifica severidade, contexto e prioridade inicial.

</td>
</tr>

<tr>
<td>

AG-04 // THREAT INTEL

Consulta e consolida inteligência de ameaças.

</td>
<td>

AG-05 // IDENTIDADE

Analisa conta, MFA, grupos e privilégios.

</td>
<td>

AG-06 // ATIVO

Recupera ativo, IP, criticidade e status de EDR.

</td>
</tr>

<tr>
<td>

AG-07 // PHISHING

Analisa metadados, cabeçalhos e autenticação.

</td>
<td>

AG-08 // CONHECIMENTO

Recupera políticas, playbooks e runbooks.

</td>
<td>

AG-09 // INCIDENTE

Consolida evidências e investigação.

</td>
</tr>

<tr>
<td>

AG-10 // REFLEXÃO / QA

Revisa qualidade, lacunas e inconsistências.

</td>
<td>

AG-11 // GESTÃO DO CASO

Mantém documentação e histórico.

</td>
<td>

AG-12 // ESCALONAMENTO

Fecha N1, escala N2 ou aguarda humano.

</td>
</tr>
</table>

04 // NÚCLEO DO CASO

            ┌──────────────┐
            │    ALERTA    │
            └──────┬───────┘
                   │
        ┌──────────┴───────────┐
        │                      │
        ▼                      ▼
      IOCs                IDENTIDADES
        │                      │
        └──────────┬───────────┘
                   ▼
              CONTEXTO DO ATIVO
                   │
                   ▼
                EVIDÊNCIAS
                   │
                   ▼
         TRIAGEM / THREAT INTEL
                   │
                   ▼
      PHISHING / CONHECIMENTO RAG
                   │
                   ▼
              INVESTIGAÇÃO
                   │
                   ▼
                  QA
                   │
                   ▼
              ESCALONAMENTO
                   │
                   ▼
               CaseState

O CaseState funciona como a ficha viva da investigação.

Ele concentra:

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

timestamps.

05 // ESTADOS DO WORKFLOW

flowchart LR
    A[RECEBIDO] --> B[NORMALIZANDO]
    B --> C[TRIANDO]
    C --> D[ENRIQUECENDO]
    D --> E[INVESTIGANDO]
    E --> F[CORRELACIONANDO]
    F --> G[REVISANDO]
    G --> H[DOCUMENTANDO]
    H --> I[DECIDINDO]
    I --> J[FECHADO_N1]
    I --> K[ESCALADO_N2]

ESTADOS AUXILIARES

WAITING_DATA · WAITING_HUMAN · RETRYING · FAILED · CANCELLED

EXECUÇÃO DOS AGENTES

PENDING · RUNNING · COMPLETED · FAILED · SKIPPED

06 // HIERARQUIA DE CONFIANÇA

┌──────────────────────────────────────┐
│ 01  HARD RULES                       │
├──────────────────────────────────────┤
│ 02  DADOS DE FERRAMENTAS             │
├──────────────────────────────────────┤
│ 03  EVIDÊNCIAS                       │
├──────────────────────────────────────┤
│ 04  CONTEXTO CONSOLIDADO             │
├──────────────────────────────────────┤
│ 05  INTERPRETAÇÃO DA IA / LLM        │
└──────────────────────────────────────┘

FONTES DE EVIDÊNCIA

FONTE

FINALIDADE

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

07 // PLANO DE CONTROLE DE SEGURANÇA

<table>
<tr>
<td width="50%">

ACESSO

negar por padrão;

menor privilégio;

autorização por agente;

catálogo oficial de ferramentas;

rotas explicitamente permitidas;

ferramentas proibidas bloqueadas.

</td>
<td width="50%">

EXECUÇÃO

falhar de forma fechada;

timeout;

retries limitados;

loops limitados;

validação de binding;

sem shell irrestrito.

</td>
</tr>

<tr>
<td>

INTEGRIDADE

raw_event imutável;

evidências imutáveis;

auditoria append-only;

versionamento;

rastreabilidade.

</td>
<td>

CONTROLE HUMANO

escalonamento N2;

espera por humano;

hard rules;

QA obrigatório;

nenhuma contenção crítica autônoma.

</td>
</tr>
</table>

08 // BLOQUEIO DE AÇÕES CRÍTICAS

[ BLOQUEADO ]  iam.reset_password
[ BLOQUEADO ]  iam.disable_user
[ BLOQUEADO ]  iam.delete_user

[ BLOQUEADO ]  network.block_ip
[ BLOQUEADO ]  network.unblock_ip

[ BLOQUEADO ]  firewall.add_rule
[ BLOQUEADO ]  firewall.delete_rule
[ BLOQUEADO ]  firewall.modify_rule

[ BLOQUEADO ]  endpoint.isolate_host
[ BLOQUEADO ]  endpoint.kill_process
[ BLOQUEADO ]  endpoint.delete_file

[ BLOQUEADO ]  email.open_url
[ BLOQUEADO ]  email.execute_attachment
[ BLOQUEADO ]  email.download_attachment

No laboratório, quando necessário, uma ação pode existir somente como:

RECOMMENDED_ACTION
SIMULATED_ACTION

Nenhuma ação crítica real é executada automaticamente.

09 // REDE DE FERRAMENTAS

flowchart LR
    A[AGENTE] --> B[ToolRequest]
    B --> C{AUTORIZAÇÃO}
    C -->|NEGADO| X[FALHA FECHADA]
    C -->|PERMITIDO| D[ToolRegistry]
    D --> E[ToolRuntime]
    E --> F[INTEGRAÇÃO SOMENTE LEITURA]
    F --> G[ToolResult]
    G --> H[EVIDÊNCIA]

10 // NÓS DE INTEGRAÇÃO

NÓ 4.1 // MISP

misp.search_ioc
misp.get_event
misp.get_attribute

STATUS :: SOMENTE LEITURA ✅

NÓ 4.2 // ELASTIC

elastic.search_alerts
elastic.search_events
elastic.get_document

STATUS :: SOMENTE LEITURA ✅

NÓ 4.3 // IDENTIDADE / IAM

iam.get_user
iam.get_account_status
iam.get_mfa_status
iam.get_group_membership

STATUS :: SOMENTE LEITURA ✅

NÓ 4.4 // ASSET / CMDB

asset.get_asset
asset.get_ip_context
asset.get_criticality
asset.get_edr_status

STATUS :: SOMENTE LEITURA ✅

NÓ 4.5 // E-MAIL / PHISHING

email.get_message_metadata
email.get_headers
email.get_authentication_results
email.get_attachment_metadata

STATUS :: PRÓXIMA ETAPA ⏭️

Objetivo: fornecer evidências ao AG-07 Phishing Analyst Agent sem abrir URLs, executar anexos ou baixar conteúdo perigoso.

11 // FLUXO DE AUDITORIA

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

O histórico é append-only: eventos anteriores não são sobrescritos.

12 // PROTOCOLO DE ESCALONAMENTO

<table>
<tr>
<td width="50%">

FECHAMENTO N1

Requer:

confiança elevada;

QA aprovado;

evidências suficientes;

playbook concluído;

nenhuma hard rule exigindo escalonamento;

nenhum comprometimento crítico confirmado.

</td>
<td width="50%">

ESCALONAMENTO N2

Prioridade quando houver:

conta privilegiada;

ativo crítico;

IOC malicioso confirmado;

movimentação lateral;

exfiltração de dados;

comprometimento confirmado;

alerta não suportado;

QA falhando após o limite de retries.

</td>
</tr>
</table>

13 // CATÁLOGO DE ALERTAS

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

UNSUPPORTED deve ser escalado, não interpretado livremente.

14 // CAMADA DE PERSISTÊNCIA

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

15 // INTELIGÊNCIA ARTIFICIAL LOCAL

O laboratório foi projetado para uso de IA local com Ollama.

Benefícios:

execução local;

menor dependência de APIs externas;

experimentação com modelos abertos;

maior controle sobre dados do laboratório;

separação clara entre interpretação e comprovação.

IA / LLM     → interpreta
FERRAMENTA   → comprova
REGRA        → governa
HUMANO       → decide quando necessário

16 // CONHECIMENTO / RAG

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

IMPLEMENTAÇÃO COMPLETA :: FASE 5

17 // MCP

Estrutura planejada:

mcp/
├── client/
└── server/

IMPLEMENTAÇÃO COMPLETA :: FASE 6

18 // MATRIZ DE TESTES

MÓDULO

TESTES

STATUS

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

TOTAL

151

APROVADO

Executar:

python -m pytest -q

Resultado esperado:

151 passed

19 // PILHA TECNOLÓGICA

<table>
<tr>
<td align="center"><strong>Python</strong><br><code>3.14</code></td>
<td align="center"><strong>Pydantic</strong><br><code>v2</code></td>
<td align="center"><strong>Ollama</strong><br><code>IA Local</code></td>
<td align="center"><strong>SQLite</strong><br><code>Persistência</code></td>
</tr>
<tr>
<td align="center"><strong>HTTPX</strong><br><code>Cliente HTTP</code></td>
<td align="center"><strong>Pytest</strong><br><code>Testes</code></td>
<td align="center"><strong>Git</strong><br><code>Versionamento</code></td>
<td align="center"><strong>GitHub</strong><br><code>Repositório</code></td>
</tr>
</table>

Dependências principais:

pydantic==2.13.5
ollama==0.6.2
numpy==2.5.3
pytest==9.1.1
httpx==0.28.1

20 // ÁRVORE DO PROJETO

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

21 // SEQUÊNCIA DE INICIALIZAÇÃO

git clone https://github.com/Paula-Tech007/Agentic-SOC-N1-Lab.git
cd Agentic-SOC-N1-Lab

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pytest -q

22 // VARIÁVEIS DE AMBIENTE

Nunca versionar credenciais reais.

MISP

MISP_URL
MISP_API_KEY
MISP_VERIFY_SSL
MISP_TIMEOUT_SECONDS

ELASTIC

ELASTIC_URL
ELASTIC_API_KEY
ELASTIC_VERIFY_SSL
ELASTIC_TIMEOUT_SECONDS
ELASTIC_ALERTS_INDEX
ELASTIC_EVENTS_INDEX

IDENTIDADE / IAM

IAM_URL
IAM_API_TOKEN
IAM_PROVIDER
IAM_VERIFY_SSL
IAM_TIMEOUT_SECONDS

ASSET / CMDB

ASSET_URL
ASSET_API_TOKEN
ASSET_PROVIDER
ASSET_VERIFY_SSL
ASSET_TIMEOUT_SECONDS

Nunca publique tokens, API keys, senhas ou arquivos .env reais no GitHub.

23 // ROADMAP

[██████████] FASE 0    Escopo / Arquitetura / Governança
[██████████] FASE 1    Fundação Técnica
[██████████] FASE 2    Schemas / Estado / Persistência / Auditoria
[██████████] FASE 3    Agentes / Runtime / Orquestração
[██████████] FASE 4.0  Fundação de Tools
[██████████] FASE 4.1  MISP Somente Leitura
[██████████] FASE 4.2  Elastic Somente Leitura
[██████████] FASE 4.3  Identity / IAM Somente Leitura
[██████████] FASE 4.4  Asset / CMDB Somente Leitura
[░░░░░░░░░░] FASE 4.5  E-mail / Metadados de Phishing
[░░░░░░░░░░] FASE 5    Conhecimento / RAG
[░░░░░░░░░░] FASE 6    MCP
[░░░░░░░░░░] FASE 7    SOC Multiagente End-to-End

Todas as fases são evoluções do mesmo projeto e do mesmo repositório.

24 // CHECKPOINT ATUAL

╔════════════════════════════════════════════════════╗
║ AGENTIC SOC N1 LAB // CHECKPOINT                  ║
╠════════════════════════════════════════════════════╣
║ FASE 4.4                         CONCLUÍDA         ║
║ ASSET / CMDB                     SOMENTE LEITURA   ║
║ MISP                             SOMENTE LEITURA   ║
║ ELASTIC                          SOMENTE LEITURA   ║
║ IDENTITY / IAM                   SOMENTE LEITURA   ║
║ AG-06                            ALINHADO          ║
║ GOVERNANÇA DE TOOLS              ATIVA             ║
║ TESTES                           151 APROVADOS     ║
║ PRÓXIMA ETAPA                    FASE 4.5          ║
╚════════════════════════════════════════════════════╝

25 // AVISO DE SEGURANÇA

Este repositório é um laboratório educacional e defensivo de Segurança Cibernética.

As integrações atuais foram implementadas para consulta controlada, validação de arquitetura e estudo de automação defensiva.

O projeto não representa autorização para execução automática de ações críticas em ambientes de produção.

<div align="center">

// PAULA SABINO

Segurança Cibernética · SOC · Automação de Segurança · IA aplicada à Segurança




<br>

AUTOMAÇÃO DEFENSIVA // EVIDÊNCIAS VERIFICÁVEIS // IA CONTROLADA

</div>