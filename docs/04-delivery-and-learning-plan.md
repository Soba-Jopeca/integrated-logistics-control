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

## Estado atual — VAL-F1-P04-001

F1 FECHADA no escopo documental em 16/10/2026, por VAL-F1-P04-001.
F2 pronta para receber o primeiro cartão do gerente, ainda não iniciada.
F3–F6 bloqueadas pelas dependências anteriores.

Fechamento limitado aos artefatos documentais. Evidências e limitações
na passagem final do documento 08; histórico anterior preservado.
Aguardar cartão específico antes de executar qualquer atividade da F2.
