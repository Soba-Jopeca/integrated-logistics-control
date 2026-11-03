# F5-P02 — Referência analítica SQL

Base: `7e9b07f`, com **VAL-F5-P01-001** registrado conforme cartão humano.
F5 aberta. F6 bloqueada. Sem Power BI, DAX, IA ou merge.
Contratos: documento 06 e proposta 08. Estado: preparação,
aguardando execução PostgreSQL e contribuição de João.

## Dicionário e cortes

| Objeto | Grão | Uso |
|---|---|---|
| reference | Um corte e período por sessão | Corte UTC, publicação, período local, fuso e horário da consulta |
| dim_delivery | delivery_key | ID, pedido, liberação e prazo |
| dim_document | document_key | ID, família, versão e origem |
| dim_date | local_date | Calendário da coorte selecionada |
| dim_source / dim_result / dim_reason / dim_rules | Uma chave por origem / resultado / código / versão de regras | Atributos para filtro e detalhamento |
| fact_delivery_reference | reference_key + delivery_key | Prazo, conclusão selecionada, contestação, presença e recebimento original válido |
| fact_document_reference | reference_key + document_key vigente | Entrega, origem e avaliação vigente ou NOT_EVALUATED |
| fact_evaluation_history | evaluation_key | Histórico de avaliações até o corte |
| bridge_evaluation_reason | evaluation_key + code + affected_field | Motivos; não usar join direto para contar versões |

Conclusão: decisão persistida mais recente conhecida no corte, com evento aceito
e ocorrido até o corte. Contestação segue a política conservadora F4 de conflito
não documental aberto. A coorte M1/M4 usa a data da conclusão selecionada,
inclusive provisória para contar exclusões, em America/Sao_Paulo, intervalo
[start, end). Horários de conclusão não conhecidos ficam fora da coorte; prazo
ausente é contado separadamente, com precedência da contestação.

M2 usa o corte inclusivo, sem filtro de período. Documento estruturalmente
aceito e vinculado até o corte conta como recebido, inclusive divergente,
malformado após aceite estrutural ou substituído. M3 usa vigência [from,to)
do documento e da avaliação. Motivos não multiplicam resultados. Não avaliado
é separado. M4 usa o mínimo de received_at original dentre versões vinculadas
e aceitas até o corte, sem exigir aprovação ou extração bem-sucedida. Conflito
de identidade exclui a versão do cálculo de M4; as tentativas rejeitadas por
identidade seguem o bloqueio conservador de F4. Intervalos negativos e ausências
de recebimento válido são separados. Zero horas é válido. Não buscar o próximo
documento só porque o primeiro resultou em intervalo negativo.

A consulta usa uma transação REPEATABLE READ e objetos temporários, com
rollback no fim; não grava em tabelas operacionais. A fixture exercita o mesmo
SQL dos fatos sobre entradas sintéticas normalizadas, separada dos dados
operacionais. Liberação do pedido é o proxy de conhecimento da entrega no
esquema atual. Prazo e demais atributos correntes não têm histórico de
alteração nesta publicação: cortes retroativos não são snapshots congelados.
O adaptador operacional deve ser executado separadamente para testar o vínculo
com o esquema real. Não somar cortes nem relacionar fatos diretamente.

## Comandos e evidência

Na raiz, ambiente existente, banco de teste configurado:

```powershell
python -m scripts.check_sql_analytics --database ilc_f2p02b_test --prepared
```

`--prepared` executa M2–M4 e verifica coorte vazia. João implementa M1 em
`analytics/sql/m1.sql`, mantendo colunas eligible, on_time, missing_promise,
contested e rate_pct. Usar completion_cohort; contar com FILTER e dividir
por NULLIF do denominador. Executar sem `--prepared` para comparar tudo.

| Métrica | Esperado na fixture | Observado |
|---|---|---|
| M1 | 3/4 = 75%; 1 sem prazo e 1 contestada | Pendente |
| M2 | 6 concluídas; 2 sem documento | Pendente |
| M3 | 1 em revisão com 2 motivos; 1 não avaliado | Pendente |
| M4 | 2 elegíveis (0 e 1/6 hora), mediana 1/12 hora; 2 sem recebimento válido, 1 negativo e 1 contestado | Pendente |

Corte 17/10/2026 12:00 UTC; período local 16/10 inclusivo a 17/10 exclusivo.
Na coorte vazia, M1 e M4 retornam nulo para taxa/mediana e contagens zero.
M2/M3 conservam o mesmo corte. Números do mockup não são usados.

```powershell
python -m scripts.check_sql_analytics --database ilc_f2p02b_test --mode operational --start 2026-10-16 --end 2026-10-17 --cutoff 2026-11-04T00:00:00-03:00
```

Os dados do banco de teste podem variar conforme cargas anteriores; guardar
os resultados observados com o corte e a publicação. Nenhum número
operacional é esperado por construção. Registrar o commit autoral e a
interpretação de João antes da passagem ao gerente.
