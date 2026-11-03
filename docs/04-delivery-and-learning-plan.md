## Estado atual — F4 FECHADA COM LIMITAÇÕES

**VAL-F4-P04-001 — decisão central encaminhada por João em 03/11/2026.**
O fechamento foi autorizado por mensagem humana neste chat, sem inferência
por memória, testes ou delegação. Aceites P01/P02/P03 e limitações preservados.

| Fase | Estado após a decisão |
|---|---|
| F4 | **FECHADA COM LIMITAÇÕES — VAL-F4-P04-001** |
| F5 | **Pronta para receber o primeiro cartão do gerente, ainda não iniciada** |
| F6 | **Bloqueada** |

**Baseline determinístico padrão; IA experimental isolada; nenhuma aprovação
por IA.** Explicação independente de João continua adiada, não demonstrada.
Prática anterior, autoria, evidências e limites permanecem registrados.
Esforço humano **não medido**.

Esta publicação altera somente README, plano e documento 25. Nenhum merge,
teste novo, inferência, carga, integração ou início de F5. Alterações locais
preservadas; sincronização do novo commit no Windows não é presumida.

[Passagem final e evidências](25-f4-p04-consolidation.md).

As seções anteriores de fase aberta/submissão abaixo são **histórico anterior
ao fechamento** e não substituem esta decisão. Resultados e limitações técnicas
não foram alterados.

---

<!-- Estado atual: seções históricas abaixo não substituem esta consolidação. -->

## Estado atual — F4-P04 entregue para decisão central (03/11/2026)

**F4 permanece ABERTA. F5–F6 não liberadas.** P01/P02/P03 aceitos por
VAL-F4-P01-001, VAL-F4-P02-001 e VAL-F4-P03-001. Consolidação P04 entregue
para o gerente decidir fechamento ou ajustes; executor não declara fechamento.

Extração PDF/XML, conferência determinística, substituição/histórico e experimento
local consolidados. **Baseline padrão; IA experimental isolada; nenhuma aprovação
por IA.** 63 testes acumulados e provas anteriores reutilizados; nenhuma inferência
ou carga repetida em P04. Prompt autoral publicado em 4623f35, evidências em b1e2121,
base documental ce875cf. Explicação independente adiada; esforço não medido.

[Passagem final F4-P04](25-f4-p04-consolidation.md) reúne commits, esperado × observado,
autoria, checagem Git/consulta delegadas e limitações. Histórico abaixo preservado.

---

# 04 — Plano de execução e aprendizagem

Data-base: 16/10/2026.
21/10/2026 é alvo de demonstração inicial, não compromisso comprovado.
A estimativa antiga de 20–25 horas não constitui esforço medido.
Tempo dedicado: não medido.



## Estado atual — fechamento autorizado VAL-F3-P04-001

Decisão humana recebida de João neste chat: registrar **F3 FECHADA COM
LIMITAÇÕES**, preservando o histórico, as evidências e a explicação independente
adiada. A decisão central, e não inferência baseada em testes ou memória,
autoriza esta atualização exclusivamente documental.

| Fase | Estado central |
|---|---|
| F1 | Fechada documentalmente — VAL-F1-P04-001 |
| F2 | Fechada com limitações — VAL-F2-P04-001 |
| F3 | **FECHADA COM LIMITAÇÕES — VAL-F3-P04-001** |
| F4 | Pronta para receber o primeiro cartão do gerente, ainda não iniciada |
| F5–F6 | Bloqueadas |

Base técnica preservada: 702ede1. Consolidação submetida: 48e5205.
Branch: feat/f3-p03-reliability; revisão observada 0006_reliability;
banco ilc_f2p02b_test. R05–R07 aceitos no escopo demonstrado; última regressão
aprovada: 98 testes, nenhum skip, Ruff aprovado; provas não repetidas no fechamento.

Prática de João e conferência delegada ao assistente continuam discriminadas
na [passagem final 21](21-f3-p04-consolidation.md). Explicação independente
permanece **adiada, não demonstrada**; esforço humano permanece não medido.
Limitações de interrupção controlada, retry/snapshot, recuperação explícita,
concorrência não ensaiada, aviso HTTPX/TestClient e reprodução/operação futura
não foram apagadas nem convertidas em conformidade completa.

Feito: README/plano/documento 21 atualizados por VAL-F3-P04-001.
Próximo passo: entregar passagem e commit final ao gerente para inclusão nas
fontes compartilhadas; aguardar primeiro cartão específico de F4 no chat 04.
Sem merge, novos testes, implementação ou início de F4.
As seções seguintes preservam o histórico anterior e não substituem esta decisão.

## Histórico — 02/11/2026, F3-P04 autorizado, anterior ao fechamento

| Fase/cartão | Estado |
|---|---|
| F1 | Fechada documentalmente — VAL-F1-P04-001 |
| F2 | Fechada com limitações — VAL-F2-P04-001 |
| F3-P01 | Aceito: API, paginação e falhas HTTP reais; código 8554901/evidência 4827619 |
| F3-P02A | Aceito: captura preservada; código 2b4b72a/registro de aceite 60cc75f |
| F3-P02B | Aceito: transformação/carga; código 44fcbff/registro de aceite 6e10e91 |
| F3-P03 | Aceito no escopo demonstrado — VAL-F3-P03-001; código 702ede1/evidência d0cba49 |
| F3-P04 | Entrega publicada; SQL/Git de João demonstrados; comandos conferidos pelo assistente por delegação humana; aguarda decisão central |
| F3 | ABERTA; esta documentação não fecha a fase |
| F4–F6 | Bloqueadas; nenhuma autorização de início |

Fonte de autoridade: cartões humanos recebidos neste chat executor; P04 determina
registrar VAL-F3-P03-001 e consolidar os aceites anteriores. IDs separados não
fornecidos não são inventados. Explicação independente de João permanece adiada
para revisão final; não foi declarada concluída.

Branch: feat/f3-p03-reliability. Banco ilc_f2p02b_test, ilc_app,
127.0.0.1:55432, revisão observada 0006_reliability. PR #2 aberto/sem merge,
consultado no início de P04. Código técnico final `702ede1`; evidências `d0cba49`;
consolidação documental descendente, sem funcionalidades ou dependências novas.

R05–R07 demonstrados com API/OpenAPI, CSV/captura, identidade, histórico,
checkpoint/rollback/retomada, retry limitado, rejeição recuperada e evento
atrasado. Fixture original 8/8/13; com sentinelas 9/9/14; após recuperação
legítima 10/10/16, estável em reexecução. Não somar capturas/tentativas como entidades.

Última regressão Windows: 98 testes, nenhum skip, 1 aviso, 14,05 s, saída 0;
Ruff aprovado. P04 reutiliza evidências, sem repetir testes por mudança documental.
Esforço humano total e por etapa **não medido**. Duração de suíte não é esforço.
Apresentação pretendida em 03/11 às 14h; estimativa antiga 20–25 h não é medição.

Prática concluída: João implementou paginação/ligação do endpoint, transação de
captura, normalização UTC e ligação de checkpoint; executou cenários, consultas
e regressões. Em P04 consultou execução/checkpoint existentes e confirmou Git local/remoto,
sem repetir cargas. João delegou explicitamente a conferência dos demais comandos
ao assistente; checagem técnica concluída e registrada no documento 21.

[Passagem consolidada e comandos atuais](21-f3-p04-consolidation.md).
Pendência: decisão central de fechamento/ajustes,
considerando a explicação independente pendente. Não fechar F3 nem iniciar F4.
Os estados anteriores abaixo são histórico, superados pela seção atual.

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


## Histórico — fechamento autorizado VAL-F2-P04-001

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

### Evidência P04 recebida em 02/11/2026

Sincronização local/remoto observada em ee59574, rev-list 0 0, somente
.vscode/ não rastreado; diff check sem saída de erro. Alembic 0006_reliability.
Consulta READ ONLY ao banco ilc_f2p02b_test/ilc_app/55432: captura
capture-p03-02e5146c-2341-4cd9-846a-49922afd3f2a SUCCEEDED, sem erro,
checkpoint 3/13, complete=True, next_cursor=None, query_exit=0.
Nenhum teste ou carga repetido. A conferência do runbook, antes pendente, foi
posteriormente delegada por João ao assistente e concluída. Decisão central
continua pendente; explicação independente adiada.

### Entrega P04 — conferência delegada

João solicitou expressamente ao assistente fazer a checagem documental restante.
Foram conferidas 13 linhas de comandos de sete CLIs contra seus argumentos,
códigos de saída/configuração e consultas contra o esquema, além do launcher
loopback e contrato de paginação. Precisado na documentação que erro de uso
argparse também pode sair com código 2, distinto do PARTIAL informado pela carga.
A checagem não foi atribuída a João nem convertida em explicação independente.
P04 entregue para avaliação central; F3 ABERTA, F4 bloqueada. Sem merge,
funcionalidade nova, repetição de testes ou escrita no banco.


## F4-P01 — preparação autorizada em 02/11/2026

F4 em execução por cartão humano F4-P01, ainda não validado. Estrutura de
extração preparada; transformação central, prática e prova PostgreSQL pendentes.
18 testes offline aprovados e cinco falhas da transformação autoral pendente;
Ruff aprovado. Sem conferência/aprovação/IA, merge ou início de F5–F6.
Detalhes e próximo passo: [passagem 22](22-f4-p01-document-extraction.md).


## F4-P02 — preparação autorizada

F4-P01 aceito por **VAL-F4-P01-001** no cartão humano recebido. F4-P02
em execução: comparação central e provas SQL pendentes; sem aceite inferido.
F4 aberta; experimento IA e F5–F6 não liberados. [Passagem 23](23-f4-p02-document-validation.md).


## F4-P02 — entrega para validação central

Código final **b88f88a** publicado por João: Git 0 0, somente .vscode/ não rastreado.
40 testes de documentos aprovados, Ruff aprovado, verificador PostgreSQL PASS
(10 versões, zero sobreposições, preservação física/P01) e consulta read-only
do histórico com saída 0. F4-P01 aceito por VAL-F4-P01-001.
**F4-P02 entregue para validação, sem aceite inferido; F4 aberta, IA e F5–F6 não liberados.**
Explicação independente adiada; limitações e autoria preservadas na
[passagem 23](23-f4-p02-document-validation.md).
Seções anteriores de preparação são histórico.


## F4-P03 — experimento local autorizado

F4-P02 aceito por VAL-F4-P02-001. Runtime Ollama 0.40.13 e Qwen2.5 1.5B
confirmados por João; smoke local executado. Harness, dois prompts e oito
documentos rotulados preparados; comparação real e utilidade ainda pendentes.
63 testes offline aprovados. F4 aberta; consolidação e F5–F6 não liberadas.
[Passagem 24](24-f4-p03-local-ai-experiment.md).


## F4-P03 — entregue para validação central

Prompt autoral publicado em **4623f35**, evidências/relatório em b1e2121.
63 testes offline aprovados; ensaio real com oito documentos e dois prompts
concluído. Baseline 30/40 campos, V1/V2 39/40; ambos inventaram ADMIN no caso
malicioso. Recomenda-se manter baseline como padrão, IA isolada, sem integração
ou aprovação. Hashes/resumos auditados. Git observado em 4623f35: 0 0,
somente .vscode/ não rastreado. Explicação independente adiada.
[Passagem 24](24-f4-p03-local-ai-experiment.md).
**F4-P03 aguarda aceite central; F4 aberta, sem consolidação e sem liberar F5–F6.**
