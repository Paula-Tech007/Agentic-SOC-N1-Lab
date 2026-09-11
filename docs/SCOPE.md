# Agentic SOC N1 Lab

## SCOPE — Escopo Oficial do Projeto

**Versão:** 1.0  
**Status:** Definido  
**Fase:** 0 — Escopo e Arquitetura  
**Projeto:** Agentic SOC N1 Lab

---

# 1. Visão do projeto

O Agentic SOC N1 Lab é um laboratório defensivo criado para desenvolver e validar a automação de ponta a ponta das atividades operacionais executadas por um Security Operations Center de nível N1.

O laboratório será baseado em uma arquitetura multiagente, na qual diferentes agentes de inteligência artificial representarão profissionais especializados do SOC.

Cada agente possuirá:

- responsabilidade específica;
- dados de entrada definidos;
- formato de saída estruturado;
- ferramentas autorizadas;
- permissões limitadas;
- regras de segurança;
- mecanismos de auditoria;
- critérios de sucesso.

Os agentes serão coordenados por um SOC Supervisor Agent.

---

# 2. Objetivo principal

Construir um SOC N1 automatizado capaz de:

1. receber alertas de segurança;
2. normalizar eventos;
3. realizar triagem;
4. identificar indicadores;
5. enriquecer informações;
6. consultar identidade;
7. consultar contexto de ativos;
8. analisar ameaças;
9. investigar phishing;
10. consultar playbooks e conhecimento interno;
11. correlacionar evidências;
12. produzir uma investigação;
13. revisar a própria investigação;
14. documentar o incidente;
15. decidir entre encerramento N1 ou escalonamento N2.

O operador humano não deverá precisar orientar manualmente cada etapa da investigação.

---

# 3. Resultado esperado

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
        v
ESPECIALISTAS NECESSÁRIOS
        |
        +-- Threat Intelligence
        +-- Identity
        +-- Asset Context
        +-- Phishing
        +-- Knowledge/RAG
        |
        v
INCIDENT ANALYST
        |
        v
REFLECTION / QA
        |
        v
CASE MANAGEMENT
        |
        v
ESCALATION
        |
        +-- CLOSED_N1
        +-- ESCALATED_N2
        +-- WAITING_HUMAN
```

---

# 4. Equipe virtual do SOC

## AG-01 — SOC Supervisor Agent

Responsável por coordenar toda a investigação.

Principais responsabilidades:

- acompanhar o estado do caso;
- decidir quais agentes serão acionados;
- distribuir tarefas;
- identificar informações faltantes;
- controlar retries;
- encaminhar investigação para revisão;
- coordenar o encerramento do fluxo.

O Supervisor não poderá modificar evidências nem executar ações críticas.

## AG-02 — Alert Intake Agent

Responsável por receber e normalizar eventos.

Funções:

- receber evento bruto;
- identificar campos importantes;
- extrair indicadores;
- normalizar estrutura;
- validar formato;
- iniciar o caso.

## AG-03 — Triage Analyst Agent

Responsável pela triagem inicial do SOC N1.

Funções:

- classificar alerta;
- identificar categoria;
- definir severidade inicial;
- identificar IOC;
- identificar informações faltantes;
- determinar especialistas necessários.

## AG-04 — Threat Intelligence Agent

Responsável pelo enriquecimento de indicadores.

Indicadores suportados:

- IP;
- domínio;
- URL;
- hash.

O agente deverá utilizar fontes e ferramentas autorizadas.

O modelo de IA não poderá inventar reputação de indicadores.

## AG-05 — Identity Analyst Agent

Responsável pelo contexto relacionado a usuários e contas.

Funções:

- verificar existência da conta;
- verificar status;
- verificar privilégio;
- verificar MFA;
- analisar atividade recente;
- identificar fatores de risco.

Não poderá modificar contas.

## AG-06 — Asset Context Agent

Responsável pelo contexto do ativo.

Funções:

- identificar hostname;
- sistema operacional;
- tipo de ativo;
- criticidade;
- proprietário;
- departamento;
- ambiente;
- exposição.

Não poderá alterar ou isolar dispositivos.

## AG-07 — Phishing Analyst Agent

Responsável por investigar alertas relacionados a e-mail.

Funções:

- analisar remetente;
- Reply-To;
- Return-Path;
- SPF;
- DKIM;
- DMARC;
- URLs;
- domínios;
- anexos;
- inconsistências.

Poderá utilizar o Threat Intelligence Agent para enriquecimento.

## AG-08 — Knowledge/RAG Agent

Responsável pela consulta à base de conhecimento.

Fontes previstas:

- playbooks;
- runbooks;
- policies;
- documentação interna;
- MITRE ATT&CK;
- conhecimento aprovado do laboratório.

Toda resposta deverá possuir fonte.

## AG-09 — Incident Analyst Agent

Responsável por consolidar a investigação.

Funções:

- correlacionar evidências;
- criar timeline;
- separar fatos de inferências;
- identificar lacunas;
- calcular severidade final;
- calcular confidence;
- produzir conclusão;
- recomendar próximo passo.

## AG-10 — Reflection/QA Agent

Responsável pela revisão da investigação.

Funções:

- validar evidências;
- verificar contradições;
- detectar afirmações sem suporte;
- identificar consultas faltantes;
- revisar severidade;
- revisar confidence;
- aprovar ou reprovar a investigação.

Não poderá criar evidências para corrigir uma análise.

## AG-11 — Case Management Agent

Responsável pela documentação do incidente.

Funções:

- criar incident_id;
- registrar timeline;
- registrar evidências;
- registrar agentes utilizados;
- registrar ferramentas utilizadas;
- salvar decisões;
- gerar JSON;
- gerar relatório Markdown.

## AG-12 — Escalation Agent

Responsável pela decisão operacional final.

Possíveis decisões:

- CLOSED_N1;
- ESCALATED_N2;
- WAITING_HUMAN.

A decisão deverá possuir justificativa auditável.

---

# 5. Catálogo inicial de alertas

A versão inicial deverá suportar:

1. AUTH_BRUTE_FORCE
2. SUSPICIOUS_LOGIN
3. CREDENTIAL_EXPOSURE
4. PHISHING
5. MALWARE_DETECTION
6. SUSPICIOUS_POWERSHELL
7. MALICIOUS_IOC
8. PRIVILEGED_ACCOUNT_ACTIVITY
9. LATERAL_MOVEMENT_SUSPECTED
10. DATA_EXFILTRATION_SUSPECTED

Alertas fora das categorias suportadas deverão ser classificados como não suportados e encaminhados para escalonamento.

---

# 6. Estados oficiais do caso

Estados principais:

- RECEIVED
- NORMALIZING
- TRIAGING
- ENRICHING
- INVESTIGATING
- CORRELATING
- REVIEWING
- DOCUMENTING
- DECIDING

Estados auxiliares:

- WAITING_DATA
- WAITING_HUMAN
- RETRYING
- FAILED
- CANCELLED

Estados finais:

- CLOSED_N1
- ESCALATED_N2

---

# 7. Critérios para encerramento no N1

Um caso somente poderá ser fechado automaticamente no N1 quando:

- investigação estiver completa;
- QA estiver aprovado;
- confidence atingir o limite definido;
- evidências forem suficientes;
- não houver contradições importantes;
- playbook aplicável tiver sido concluído;
- não houver indício relevante de comprometimento;
- não existir regra obrigatória de escalonamento.

Limite inicial de confidence:

```text
90/100
```

Esse valor poderá ser ajustado após os testes do laboratório.

---

# 8. Critérios obrigatórios de escalonamento

O caso deverá ser escalado quando existir:

- severidade CRITICAL;
- atividade suspeita envolvendo conta privilegiada;
- ativo crítico potencialmente comprometido;
- IOC malicioso confirmado;
- evidência de comprometimento;
- possível movimentação lateral;
- possível exfiltração;
- investigação inconclusiva relevante;
- categoria não suportada;
- QA reprovado após o limite máximo de retries.

---

# 9. Classificações finais

O sistema poderá classificar um caso como:

- FALSE_POSITIVE;
- BENIGN_POSITIVE;
- SUSPICIOUS;
- CONFIRMED_INCIDENT;
- INCONCLUSIVE.

A classificação e a decisão operacional são campos independentes.

Exemplo:

```text
Classification: SUSPICIOUS
Decision: ESCALATED_N2
```

---

# 10. Schema Universal

Todos os agentes trabalharão sobre um Case State comum.

O Case State deverá conter:

- identificação do caso;
- fonte do alerta;
- evento original;
- indicadores;
- identidade;
- ativo;
- triagem;
- threat intelligence;
- phishing;
- conhecimento;
- evidências;
- investigação;
- QA;
- escalonamento;
- estado do workflow;
- auditoria.

Regras:

- `raw_event` será imutável;
- evidências serão append-only;
- auditoria será append-only;
- `correlation_id` permanecerá durante todo o fluxo;
- cada agente escreverá somente em sua área autorizada;
- `null` significa informação desconhecida;
- `false` significa informação verificada e negativa;
- confidence utilizará escala de 0 a 100.

---

# 11. Princípios de segurança

O projeto seguirá:

1. Least Privilege
2. Deny by Default
3. Evidence Before Conclusion
4. Read Before Write
5. Tool Data Before LLM Guess
6. No Critical Autonomous Action
7. Everything Audited
8. Human Escalation Available
9. Bounded Loops
10. Fail Closed

---

# 12. Regra de autoridade

A prioridade das informações será:

1. políticas e hard rules;
2. dados obtidos por ferramentas;
3. evidências;
4. interpretação do modelo de IA.

Um modelo de IA não poderá ignorar uma regra determinística.

---

# 13. Permissões

Os agentes terão permissões mínimas necessárias.

Tipos iniciais:

- READ;
- WRITE;
- TOOL;
- DECISION.

Nenhum agente do MVP possuirá:

```text
EXECUTE_CRITICAL_ACTION
```

---

# 14. Ações críticas

Durante o MVP não serão executadas ações reais como:

- bloquear IP;
- alterar firewall;
- desabilitar usuário;
- resetar senha;
- revogar sessão;
- isolar endpoint;
- excluir arquivos;
- modificar ambientes reais.

Essas ações poderão existir apenas como:

```text
RECOMMENDED_ACTION
```

ou:

```text
SIMULATED_ACTION
```

---

# 15. Fora do escopo

Não fazem parte do MVP:

- Red Team autônomo;
- pentest autônomo;
- exploração de vulnerabilidades;
- desenvolvimento de malware;
- ataque automatizado;
- resposta ofensiva;
- execução autônoma de ações críticas;
- alterações não autorizadas em sistemas reais.

---

# 16. Tecnologias previstas

A versão inicial poderá utilizar:

- Python;
- VS Code;
- Git/GitHub;
- Ollama;
- LLM local;
- embeddings locais;
- Pydantic;
- SQLite;
- JSON;
- Markdown;
- pytest;
- MCP.

Frameworks multiagentes não serão utilizados inicialmente.

O objetivo é compreender e construir primeiro os mecanismos fundamentais.

---

# 17. Persistência

A primeira versão utilizará:

### SQLite

- casos;
- evidências;
- decisões;
- execução dos agentes;
- auditoria.

### JSON

- estado completo do incidente.

### Markdown

- relatório legível da investigação.

---

# 18. Governança

O laboratório deverá possuir:

- Permission Matrix;
- Tool Allowlist;
- deny-by-default;
- schema validation;
- timeout;
- max_steps;
- max_retries;
- Human Review;
- audit logs;
- fail closed.

---

# 19. Observabilidade

O sistema deverá registrar:

- correlation_id;
- agentes executados;
- ferramentas utilizadas;
- duração;
- retries;
- erros;
- severity;
- confidence;
- decisão;
- escalamentos;
- encerramentos;
- consumo do modelo quando disponível.

---

# 20. Avaliação

O laboratório deverá possuir casos de teste com resultados esperados.

Categorias iniciais:

- benigno;
- falso positivo;
- suspeito;
- confirmado;
- crítico.

Serão avaliados:

- precisão;
- falsos positivos;
- falsos negativos;
- classificação;
- severidade;
- escalonamento;
- tempo de investigação;
- número de passos;
- retries.

---

# 21. Critério de sucesso

O Agentic SOC N1 Lab será considerado funcional quando conseguir:

1. receber um alerta pertencente às categorias suportadas;
2. normalizar o evento;
3. realizar triagem;
4. escolher autonomamente os especialistas necessários;
5. consultar ferramentas e conhecimento permitido;
6. coletar evidências;
7. produzir investigação consolidada;
8. revisar a investigação;
9. documentar o caso;
10. decidir corretamente entre encerramento N1 e escalonamento N2;

sem que um operador precise informar manualmente qual agente deve executar cada etapa.

---

# 22. Roadmap

## Marco 1 — Fundação

- Fase 0: Escopo e Arquitetura
- Fase 1: Fundação Técnica
- Fase 2: Dados e Estado

## Marco 2 — Profissionais do SOC

- Alert Intake
- Triage
- Threat Intelligence
- Identity
- Asset
- Phishing
- Knowledge/RAG

## Marco 3 — Investigação

- Incident Analyst
- Reflection/QA
- Case Management
- Escalation

## Marco 4 — Agentic SOC

- Supervisor
- MCP
- Harness
- Guardrails

## Marco 5 — Validação

- Observabilidade
- Evaluation
- Simulações
- Dashboard

---

# 23. Status da Fase 0

- [x] Objetivo definido
- [x] Escopo SOC N1 definido
- [x] Arquitetura multiagente definida
- [x] 12 agentes definidos
- [x] Responsabilidades definidas
- [x] Matriz de permissões definida
- [x] Critérios N1/N2 definidos
- [x] Catálogo inicial de alertas definido
- [x] Schema Universal V1 definido
- [x] Estados oficiais definidos
- [x] Arquitetura Oficial V1 definida
- [x] SCOPE.md definido
- [x] ARCHITECTURE.md definido
- [x] Fase 0 aprovada

---

# Regra do projeto

Toda nova funcionalidade deverá responder:

> "Isso ajuda diretamente a automatizar, controlar, validar ou observar o processo operacional do SOC N1?"

Caso a resposta seja não, a funcionalidade será colocada no backlog de evolução e não interromperá o desenvolvimento do MVP.