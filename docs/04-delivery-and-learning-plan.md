# 04 — Plano de execução e aprendizagem

Data-base: 16/10/2026.
21/10/2026 é alvo de demonstração inicial, não compromisso comprovado.
A estimativa antiga de 20–25 horas não constitui esforço medido.
Tempo dedicado: não medido.

## Governança

Negócio → contratos → modelos.
Cada passo depende de liberação e validação pelo chat 00.
Chats executores produzem artefatos e evidências e retornam ao gerente.
Preparação de chat não significa início da fase.
Trivialidades são resolvidas sem aprovação ritual.

## Histórico — sequência e dependências no início de F1-P04

| Fase | Ordem interna | Estado no início de F1-P04 |
|---|---|---|
| F1 | Negócio → contratos → modelos → consolidação | P01/P02/H01/P03 aceitos; P04 em execução; fase aberta |
| F2 | Diagnóstico/ambiente → banco/migrações → gerador | Bloqueada |
| F3 | API → ingestão → falhas/reprocessamento | Bloqueada |
| F4 | Extração → conferência/histórico → experimento IA | Bloqueada |
| F5 | Aplicação → camada analítica → Power BI | Bloqueada |
| F6 | Scheduler/CI → recuperação/reprodução → release/demo | Bloqueada |

Não instalar dependências nem criar banco durante a F1.
Versões, ambiente virtual, lock e .env.example pertencem à F2.
O .gitignore foi antecipado exclusivamente como proteção do repositório.

## Prática e evidências

João aplica alterações, executa verificações e interpreta resultados.
O assistente prepara rascunhos, esclarece conceitos e revisa evidências.
Registrar precisamente autoria, prática observada e limitações;
não atribuir respostas simuladas a João.

Passagem contém fase, passo, data, estado, repositório, branch,
commit, requisitos, artefatos, comandos, esperado/observado,
aprendizagem, limitações, bloqueadores e próximo passo.

Fechamento de fase exige validação central, artefatos versionados,
evidências, commit, aprendizagem registrada e passagem atualizada.

## Prazo e apresentação

Reestimar após evidências das primeiras fases.
Reduzir volume e acabamento antes de integridade e testes essenciais.
OCR, RAG e evolução para Docker/Linux não bloqueiam o núcleo.

Demonstração futura: problema, arquitetura, caso correto,
divergente, reexecução, painel, trade-off e limitações.
Separar resultados sintéticos de impacto empresarial real.

## Histórico — fechamento documental VAL-F1-P04-001

F1 FECHADA no escopo documental em 16/10/2026, por VAL-F1-P04-001.
F2 pronta para receber o primeiro cartão do gerente, ainda não iniciada.
F3–F6 bloqueadas pelas dependências anteriores.

Fechamento limitado aos artefatos documentais. Evidências e limitações
na passagem final do documento 08; histórico anterior preservado.
Aguardar cartão específico antes de executar qualquer atividade da F2.


## Histórico — consolidação F2-P04, anterior à decisão central

| Fase | Estado atual |
|---|---|
| F1 | Fechada no escopo documental, VAL-F1-P04-001 |
| F2 | P01, P02A–D e P03 aceitos com limitações; P04 verificado localmente, aguarda decisão central; fase aberta |
| F3–F6 | Bloqueadas; nenhum início autorizado por esta consolidação |

Base técnica aceita: 33ba8d02931883cc31d0312049587abae444e9ef.
P04 reúne README executável, evidências, fronteira banco/aplicação, PR
revisável para main e verificação final. Não autoriza merge.
A autorização humana dos passos é a referência; IDs não fornecidos não
são inventados. Decisão de fechamento pertence à gestão central.

Verificação final executada por João em 20/10/2026: Ruff aprovado,
24 testes e 11 subtestes do gerador, 147 testes de integração em 0003,
fixture, sentinelas e conexão aprovadas. Instância existente reiniciada
após diagnóstico de indisponibilidade; nenhum downgrade repetido.
Próximo passo: retornar ao gerente para decisão de fechamento. PR #2 em
rascunho, sem merge e sem implementação F3.
Evidências e pendências: [consolidação F2](15-f2-p04-consolidation.md).


## Estado atual — fechamento autorizado VAL-F2-P04-001

Decisão central encaminhada por João em 20/10/2026:
**F2 FECHADA COM LIMITAÇÕES**. R03 e R04 aceitos no escopo demonstrado,
preservando os limites de ambiente, integridade e referências sintéticas.

| Fase | Estado central |
|---|---|
| F1 | Fechada documentalmente |
| F2 | Fechada com limitações — VAL-F2-P04-001 |
| F3 | Pronta para receber cartão; aguarda passagem atualizada e primeiro cartão, ainda não iniciada |
| F4–F6 | Bloqueadas |

PR #2 permanece sem merge. Atualização exclusivamente documental:
README, plano e passagem; nenhum código alterado ou teste repetido.
Evidências anteriores, limitações e responsabilidades futuras da aplicação
continuam válidas. Próximo passo: incluir a passagem nas fontes compartilhadas
e aguardar cartão específico; este fechamento não inicia a F3.
