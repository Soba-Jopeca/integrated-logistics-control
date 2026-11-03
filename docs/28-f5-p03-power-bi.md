# F5-P03 — Power BI local e reconciliação

Base SQL: d6f7e6d, documento 27. Execução Power BI e aceite central pendentes.
F5 aberta, F6 bloqueada. Sem publicação no serviço ou merge.

Na raiz do projeto, com a instância PostgreSQL dedicada e a venv:

```powershell
python -m scripts.export_powerbi_fixture --database ilc_f2p02b_test --out "$env:TEMP/ilc-f5-p03"
```

O exportador executa M1–M4 do P02 sobre a fixture, verifica três cenários,
exporta CSV UTF-8 e escreve o resultado efetivo em sql-reference.json.
O corte é 17/10/2026 às 12:00 UTC, a coorte local é [16/10,17/10) e o fuso
é America/Sao_Paulo. EMPTY restringe a coorte a nenhuma linha e LATE à
entrega sintética 2, atrasada. M2/M3 mantêm o escopo do corte. A transação
usa apenas objetos temporários e termina em rollback.

## Montagem no Desktop

Importar scenarios.csv, deliveries.csv e documents.csv via Texto/CSV.
Em Transformar dados, manter chaves como Texto, converter contested,
in_cohort e has_received_document em Verdadeiro/Falso e receipt_hours em
Número decimal com localidade Inglês (Estados Unidos), preservando nulos.
Manter completed_at como texto com nulo para vazio; verificar em Power Query.
Criar relações 1:N unidirecionais de scenarios[scenario] para cada fato,
sem relacionar fatos entre si. Grão: cenário + delivery_key ou document_key.
Dimensões e ponte de motivos também são exportadas para auditoria; não
expandir a ponte nas tabelas de métricas.

Adicionar segmentação de cenário com seleção única, quatro cartões e uma
tabela de reconciliação por cenário. Criar M2–M4 a partir de
analytics/powerbi/measures.dax. Para M1, João deve filtrar deliveries por
in_cohort, não contested e prazo informado. Entre as elegíveis, comparar
conclusão e prazo. Para comparar com segurança, converter completed_at e
promised_at em Data/Hora/Fuso no Power Query e normalizar ambos para UTC
antes de remover o fuso e carregar como Data/Hora. Usar DIVIDE, sem
alternativa, e formatar como porcentagem. SQL usa escala 0–100.

| Cenário | M1 | M2 | M3 | M4 horas | DAX observado |
|---|---:|---:|---:|---:|---|
| BASE | 75% | 2 | 1 | 0,0833333333 (5 min) | Pendente |
| EMPTY | BLANK | 2 | 1 | BLANK | Pendente |
| LATE | 0% | 2 | 1 | BLANK | Pendente |

Em BASE, filtrar a tabela de entregas para conferir os dois intervalos
elegíveis de 0 e 10 minutos. Conferir dois motivos para B1-eval na ponte
exportada e uma única versão B1 em revisão em documents.csv. Usar
ISBLANK em uma medida temporária se o cartão não distinguir vazio de zero.
Guardar a saída do exportador, valores SQL × DAX, captura e relatório local.
Registrar o M1 de João em arquivo DAX e publicar evidências e commit somente
após a execução. Não versionar credenciais ou arquivos temporários.
