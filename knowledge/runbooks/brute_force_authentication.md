# Runbook LAB — AUTH_BRUTE_FORCE

## Objetivo

Este runbook define o procedimento defensivo de triagem e investigação
para alertas de múltiplas tentativas de autenticação no
Agentic SOC N1 Lab.

Tipo de alerta relacionado:

AUTH_BRUTE_FORCE

## Princípios

A análise deve utilizar somente evidências disponíveis no caso
e resultados obtidos por ferramentas autorizadas.

Nenhuma evidência deve ser inventada.

Ausência de informação deve permanecer registrada como lacuna.

Ações críticas de contenção não devem ser executadas
automaticamente pelo SOC N1 Lab.

Quando houver risco elevado, incerteza relevante ou necessidade
de contenção, o caso deve permanecer disponível para
escalonamento ao N2 ou para revisão humana.

## Etapa 1 — Validar o alerta

Confirmar:

- existência de múltiplas falhas de autenticação;
- usuário ou conta relacionada;
- endereço IP de origem, quando disponível;
- horário e sequência dos eventos;
- severidade inicial;
- fonte que gerou o alerta.

## Etapa 2 — Threat Intelligence

Quando existir um IOC, como endereço IP de origem,
consultar fontes de Threat Intelligence autorizadas.

Registrar:

- IOC consultado;
- fonte consultada;
- reputação somente quando explicitamente fornecida;
- nível de confiança;
- evidências disponíveis.

Ausência de reputação não significa que o IOC seja
malicioso ou benigno.

## Etapa 3 — Identidade

Consultar o contexto da identidade em fonte IAM autorizada.

Verificar, quando disponível:

- existência da conta;
- estado habilitado ou desabilitado;
- uso de MFA;
- privilégio da conta;
- quantidade de falhas de login;
- último login conhecido;
- grupos ou funções relevantes.

Contas privilegiadas exigem atenção adicional.

## Etapa 4 — Ativo

Consultar Asset ou CMDB para identificar o contexto
do ativo relacionado ao evento.

Verificar, quando disponível:

- asset_id;
- hostname;
- endereço IP;
- criticidade;
- sistema operacional;
- gerenciamento corporativo;
- presença de EDR;
- exposição à Internet.

Ativos críticos aumentam a necessidade de revisão
e possível escalonamento.

## Etapa 5 — Correlação

Correlacionar as evidências disponíveis.

Itens importantes:

- quantidade e frequência das falhas;
- origem das tentativas;
- conta envolvida;
- criticidade do ativo;
- reputação do IOC;
- presença ou ausência de MFA;
- existência de login bem-sucedido após as falhas.

Um login bem-sucedido após múltiplas falhas é uma informação
importante para a investigação e deve ser comprovado por evidência.

## Etapa 6 — Lacunas

Registrar explicitamente informações ainda ausentes.

Exemplos:

- login_success_after_failures;
- identity_context;
- source_ip_reputation;
- asset_context.

Uma lacuna não deve ser preenchida por suposição.

## Etapa 7 — Decisão

O SOC N1 deve consolidar as evidências e encaminhar
o resultado para investigação, QA e decisão de escalonamento.

Escalonar para N2 ou revisão humana quando aplicável,
especialmente em situações envolvendo:

- conta privilegiada;
- ativo crítico;
- evidência consistente de comprometimento;
- login bem-sucedido suspeito;
- conflito entre evidências;
- ausência de evidência suficiente para uma conclusão segura.

## Guardrails do laboratório

Permitido:

- consultas read-only;
- enriquecimento de contexto;
- correlação;
- documentação;
- recomendação de ação;
- escalonamento.

Não permitido de forma autônoma:

- bloquear conta;
- alterar senha;
- isolar máquina;
- matar processo;
- apagar arquivo;
- executar anexo;
- abrir URL suspeita;
- executar contenção crítica real.

## Resultado esperado

O fluxo deve produzir uma investigação rastreável,
baseada em evidências e sem afirmações não comprovadas.

Ferramenta comprova.

Agente interpreta e estrutura.

Orchestrator valida e aplica.

Supervisor controla o fluxo.