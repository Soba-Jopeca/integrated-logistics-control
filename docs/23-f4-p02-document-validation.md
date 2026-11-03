# 23 — F4-P02: conferência, substituição e histórico

Data: 02/11/2026. Estado: PREPARAÇÃO EM EXECUÇÃO; sem aceite central.
Cartão humano F4-P02 recebido no chat 04. Registrar **VAL-F4-P01-001**.
Código P01: 787f327; passagem P01: 80dec06. Base de P02: 80dec06,
que contém o código 787f327 e apenas a consolidação documental posterior.
Branch de trabalho: feat/f4-p02-document-validation. Sem merge.
F4 aberta; experimento IA e F5–F6 não liberados.

## Escopo preparado e decisões

- validation.py: avaliações imutáveis, número por documento, avaliação anterior,
  rules_version, extração da mesma versão, snapshots do esperado e motivos.
- service.py: cadeia linear de substituição, predecessora vigente da mesma
  família/origem/entrega, incremento sem salto; fecha vigência antiga e abre
  nova na mesma transação. Reenvio idêntico não cria nova versão/vigência.
- regularity: consulta somente leitura dos documentos vigentes. Exige algum
  aprovado, nenhum vigente pendente, extração ainda correspondente à avaliação,
  conclusão elegível e ausência de conflitos. Histórico substituído não bloqueia.
- check_document_validation.py: fixtures próprias F4-P02-*; dez versões
  documentais e sete entregas sintéticas (AB e seis cenários independentes).
  Não reutiliza valores nem modifica referências P01/ENT-001.
- fixtures XML reais e expected.json separado; testes de regras.

Não há migração adicional: esquema 0006 contém os campos/FKs/vigências
necessários. Constraints de 0002, incluindo FK composta da extração e EXCLUDE,
continuam ativas. Novas avaliações não atualizam eventos ou decisões de conclusão.
Avaliação e substituição usam o mesmo advisory lock; avaliação também bloqueia
a entrega como a ingestão de eventos. Não alegar concorrência ensaiada.

Conclusão contestada usa o código contratual DELIVERY_NOT_CONFIRMED,
affected_field=delivered_at, detail=COMPLETION_CONTESTED. Ausência de conclusão
usa o mesmo código e detail=NO_ELIGIBLE_COMPLETION. São situações distinguíveis
sem acrescentar enum ou reinterpretar IDENTITY_CONFLICT como conflito de horário.
Conservadoramente, conflito de entrega ainda não resolvido bloqueia conclusão.
Avaliações antigas aprovadas ficam no histórico; regularidade consulta contexto
atual e não as apresenta como regularidade válida após conflito.

Referência do envelope inexistente não pode produzir uma avaliação em
ilc.evaluations: a FK exige documento e entrega reais. Preserva input/tentativa
com INVALID_REFERENCE no recebimento; não cria entrega ou documento fictício.
Referência extraída que difere da entrega vinculada produz avaliação com
REFERENCE_MISMATCH. A função de regras distingue INVALID_REFERENCE quando
não recebe referência resolvida. Esta distinção é decisão de implementação;
o gerente deve avaliar o atendimento do cenário sem supor avaliação inexistente.

Reenvios de identidade conflitante preservados por P01 são bloqueadores de
aprovação/regularidade mediante inputs/attempts. Não há resolução automática
nem limpeza desses casos neste cartão. Novos eventos/conflitos não modificam
retroativamente avaliações já gravadas.

## Prática central de João

Implementar somente same_utc_minute em src/documents/validation.py:

```python
def same_utc_minute(actual, expected):
    """Compara o minuto UTC, descartando segundos e microssegundos."""
    return actual.astimezone(UTC).replace(second=0, microsecond=0) == (
        expected.astimezone(UTC).replace(second=0, microsecond=0)
    )
```

Premissa: argumentos já são datas com fuso, validadas pelo parser e PostgreSQL;
a função não interpreta textos nem decide tolerância comercial. 17:00:00 e
17:00:59 UTC concordam; 17:01:00 diverge. Não arredondar nem aplicar tolerância.
A função está intencionalmente bloqueada por AUTHOR_COMPARISON_PENDING.
Não executar o verificador no banco antes da edição/testes verdes.

Primeiro sincronizar a branch preservando .vscode/.env/alterações existentes:

```powershell
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch interrompido.' }
git switch --track origin/feat/f4-p02-document-validation
if ($LASTEXITCODE -ne 0) { throw 'Preservar alteracoes e investigar branch.' }
```

Após editar:

```powershell
python -m ruff check src/documents scripts/check_document_validation.py tests/documents
python -m pytest -q tests/documents
Write-Output "document_tests_exit=$LASTEXITCODE"
```

Devolver primeiro a saída desses testes. Prática de comparação, execução e
consulta por João ainda pendente. Explicação independente permanece adiada.

## Verificação SQL preparada — não executada nesta entrega

Depois dos testes verdes e da conferência no chat, mesmo cartão:

```powershell
python -m scripts.check_document_validation --database ilc_f2p02b_test
Write-Output "document_validation_exit=$LASTEXITCODE"
```

O verificador não migra nem recria banco. Acrescenta apenas referências
sintéticas próprias (fonte synthetic_documents_p02), eventos/conclusões de
fixture e um conflito sintético, sem resolução. Usa banco explicitamente
permitido pelo test_engine. Semente própria não é alteração operacional da
entrega ENT-001. Snapshots posteriores à semente verificam que avaliações/
extrações não alteraram entregas/eventos/decisões/conflitos/resoluções; prova
P01 de versões/extrações também é comparada antes/depois. A semente preserva
linhas existentes via ON CONFLICT DO NOTHING e confere quantidade/unidade.

| Cenário | Esperado |
|---|---|
| A1 coerente, 10 VOLUME e mesmo minuto UTC | APPROVED; entrega regular quando único vigente |
| B1, outra família, quantidade 9 | REVIEW_REQUIRED/VALUE_MISMATCH; A1 aprovado não encobre B1 |
| B2 corrige B1 | fecha B1/abre B2; pendente antes de avaliar; regular após avaliar |
| A2 substitui A1 com XML inválido | A1 permanece histórico; A2 vigente pendente; regular=false |
| Nome ausente | MISSING_REQUIRED_FIELD, sem inventar nome |
| Referência extraída diferente | REFERENCE_MISMATCH |
| Horário em minuto diferente | VALUE_MISMATCH |
| Unidade diferente | VALUE_MISMATCH |
| Entrega não confirmada | DELIVERY_NOT_CONFIRMED/NO_ELIGIBLE_COMPLETION |
| Conclusão contestada | DELIVERY_NOT_CONFIRMED/COMPLETION_CONTESTED; física DELIVERED |
| Envelope sem referência conhecida | tentativa INVALID_REFERENCE, sem documento/avaliação fictícios |
| B4 após B2, salto de versão | INVALID_VERSION_CHAIN; vigência anterior preservada |
| Reenvio | mesma versão/input; extração nova invalida atualidade da avaliação anterior |
| Nova avaliação | número incrementado e anterior preservada |
| Vigências | zero sobreposições; dez versões documentais P02 |

Na repetição completa, versões antigas podem ser reextraídas e reavaliadas
sem voltar à vigência. O script distingue replay para não atribuir estados
intermediários da primeira execução a uma família já substituída.
Asserções A1/B1/B2/A2 intermediárias pertencem à primeira execução.

Consulta de resultados existentes, em transação SQL somente leitura:

```sql
SELECT d.document_id,d.version,dv.valid_to IS NULL AS document_current,
       e.evaluation_number,e.rules_version,e.result,e.extraction_key,
       er.code,er.affected_field,er.detail
FROM ilc.document_versions d JOIN ilc.document_validities dv USING(document_key)
LEFT JOIN ilc.evaluations e USING(document_key)
LEFT JOIN ilc.evaluation_reasons er USING(evaluation_key)
WHERE d.source_system='synthetic_documents_p02'
ORDER BY d.document_id,e.evaluation_number,er.code,er.affected_field;
```

Não colar SQL diretamente no PowerShell; a orientação de execução da consulta
será fornecida após a prova do verificador, sem pedir ferramenta adicional.

## Evidência desta preparação pelo assistente

Ruff: All checks passed. pytest tests/documents: **34 passed, 6 failed in 0.22s**.
Os 23 testes de extração P01 passaram. As seis falhas são da comparação
reservada a João: consistente, quatro limites de minuto e equivalência de fuso.
Sem skip/xfail e sem declarar suite verde. PostgreSQL NÃO executado aqui.
Não foram instaladas dependências novas, executadas migrações nem repetidas
provas de escrita P01. Schema, FKs e SQL revisados estaticamente, sem alegar
comprovação de execução. Esforço humano total não medido.

Feito: estrutura, regras, substituição, fixtures e verificadores preparados.
Aprendizagem autoral P02: pendente de edição/execução/consulta observadas.
Limitações P01 mantidas (formatos sintéticos, quota/concorrência/sem sandbox).
Resolução manual de conflitos, OCR, IA, interface, métricas e evolução de
esquema não implementadas. Próximo passo único: edição central e testes por João.
Após evidências SQL/commit, retornar ao gerente. Esta passagem não concede aceite.


## Passagem consolidada — F4-P02 entregue para validação central

Estado: **ENTREGUE PARA VALIDAÇÃO**, sem aceite inferido. F4 permanece aberta.
F4-P01 aceito por VAL-F4-P01-001 conforme cartão humano F4-P02.
IA e F5–F6 não liberados. Nenhuma mensagem automática a outro chat.

Código final publicado por João: **b88f88a**, branch feat/f4-p02-document-validation.
Preparação: 5a7473d; base técnica P01 787f327 e passagem 80dec06.
Após push, João demonstrou HEAD=origin em b88f88a, comparação **0 0**,
sem alterações rastreadas pendentes; apenas .vscode/ não rastreado, preservado.
Esta consolidação posterior é somente documental: não modifica o código
testado nem presume sincronização automática do novo documento no Windows.

### Esperado × observado no Windows de João

| Prova | Esperado | Observado |
|---|---|---|
| pytest -q tests/documents | regras/extrator aprovados | **40 passed in 0.40s**, document_tests_exit=0 |
| Ruff após edição central | sem import não usado | um F401 removido por --fix; All checks passed na conferência seguinte |
| check_document_validation --database ilc_f2p02b_test | cenários e persistência corretos | **verification=PASS**, document_validation_exit=0, replay=false |
| A1 coerente | aprovado, entrega regular | APPROVED, 1 vigente/1 aprovado/0 pendentes, regular=true |
| B1 divergente ao lado de A1 | aprovação de A não encobre B | REVIEW_REQUIRED/VALUE_MISMATCH em received_quantity; 2 vigentes/1 aprovado/1 pendente, regular=false |
| B2 corrige B1 | exige avaliação própria | APPROVED após conferência, 2 vigentes/2 aprovados, regular=true; assert intermediário de ausência de aprovação herdada passou |
| A2 substitui A1 com parsing falho | não ressuscita aprovação A1 | PARSING_FAILED/PARSING_ERROR, avaliação REVIEW_REQUIRED; 2 vigentes/1 aprovado/1 pendente, regular=false |
| Campo obrigatório ausente | motivo específico | MISSING_REQUIRED_FIELD/receiver_name/ABSENT_IN_DOCUMENT |
| Referência extraída divergente | motivo distinto de referência não resolvida | REFERENCE_MISMATCH/declared_delivery_id/DECLARED_REFERENCE_DIFFERS |
| Envelope com entrega desconhecida | rejeitar sem documento fictício | INVALID_REFERENCE em run/tentativa; sem avaliação vinculada a entrega inexistente |
| Minuto UTC diferente | divergência temporal | VALUE_MISMATCH/delivered_at/UTC_MINUTE_DIFFERS |
| Unidade diferente | divergência de unidade | VALUE_MISMATCH/quantity_unit/VALUE_DIFFERS |
| Entrega sem conclusão | não aprovar | DELIVERY_NOT_CONFIRMED/NO_ELIGIBLE_COMPLETION; physical_state=NOT_CONFIRMED |
| Conclusão contestada | bloquear aprovação dependente de horário | DELIVERY_NOT_CONFIRMED/COMPLETION_CONTESTED, REVIEW_REQUIRED; physical_state=DELIVERED, completion_contested=true |
| Salto B2→B4 | rejeitar cadeia | INVALID_VERSION_CHAIN |
| Versões e intervalos | sem duplicação/sobreposição | **versions=10, overlaps=0**; reenvio com document_key estável e nova extração |
| Preservação | avaliações não alteram físico/P01 | **physical_and_p01_preserved=true**, escopo do snapshot descrito abaixo |
| Consulta SQL do histórico | v1 anterior preservada, v2 vigente | **history_query_exit=0**, 20 linhas, avaliações 1 e 2 de dez versões |
| git diff --check | sem erro | sem saída de erro antes do commit |

40 é o total acumulado de testes de documentos (23 de extração e 17 de regras);
não somar com os 23 anteriores como casos distintos adicionais. Após o Ruff,
somente import não usado foi removido; não foi alegada nova execução de pytest.
Não houve regressão global F3 nem novas provas CI/E2E/concorrência.

O verificador retorna a segunda extração/avaliação de cada cenário; duplicate=true
nesses reports significa reenvio interno da mesma execução, não repetição completa
do verificador. A execução completa observada foi **replay=false**. A lógica
de replay completo está preparada, mas uma segunda execução integral não foi
apresentada; não alegar essa prova adicional. Os asserts verificaram versões
estáveis nos reenvios, incremento de avaliação, pendência após nova extração
e regularidade intermediária de A/B na primeira execução.

### Consulta SQL autoral e rastreabilidade

João executou a consulta em transação **SET TRANSACTION READ ONLY** pelo
test_engine do banco ilc_f2p02b_test. Resultado:
- F4-P02-A1: versão 1, vigente=false, avaliações 1/2 APPROVED.
- F4-P02-A2: versão 2, vigente=true, avaliações 1/2 REVIEW_REQUIRED/PARSING_ERROR.
- F4-P02-B1: versão 1, vigente=false, avaliações 1/2 REVIEW_REQUIRED/VALUE_MISMATCH.
- F4-P02-B2: versão 2, vigente=true, avaliações 1/2 APPROVED.
- CONTESTED/MISSING/REFERENCE/TIME/UNCONFIRMED/UNIT: versão 1 vigente,
  avaliações 1/2 com os motivos distintos da tabela.

Exemplos da prova PostgreSQL:
- A1: documento 9a1e4951-8fff-4d85-ab5e-9d10f1cd27d0,
  avaliação 2 9d77d88a-9bab-484c-b3b6-ea3dcf0a6412,
  run evaluation-a460925f-31dd-403f-92bf-6e206aae73c2.
- B2: documento f897f4ee-1aae-4087-8443-782d518ef472,
  avaliação 2 e0418892-4541-4f76-b642-f8b87c3b67a5.
- A2: documento 2fdbcf88-de94-4236-ab35-4eb3229e6550,
  avaliação 2 0977533a-3088-4995-82c8-e808d84176c6.
- Contestada: documento 23628a56-3d0e-437c-88e3-fde9b658fd02,
  avaliação 2 e122f0f2-d92d-4b87-bbe4-76aa97ee8002.
- Referência inválida: document-13f58beb-4376-4eae-87f5-6b034a266a24.
- Cadeia inválida: document-01ff8996-65bf-401a-b576-dcb2c58c55e2.
Versão de regras: document-rules-v1; parser educational-v1.

### Prática, limites e devolução

João implementou same_utc_minute, executou testes e correção de import,
verificador PostgreSQL, consulta SQL somente leitura e commit/push.
O assistente preparou estrutura, fixtures, persistência, testes/comandos
e revisão. Prática de implementar/executar/consultar observada;
explicação independente permanece adiada conforme cartão. Não atribuir
a João explicações que não apresentou. Esforço humano não medido.

Preservação demonstrada pelo script: snapshot das tabelas globais events,
deliveries, completion_decisions, conflicts e conflict_resolutions após
semente própria e antes das avaliações, comparado ao final; versões/extrações
P01 também comparadas. Não alegar snapshot de todas as tabelas anteriores.
A semente acrescenta sete entregas e eventos/conclusões sintéticos próprios,
incluindo conflito controlado; não altera a entrega ENT-001 ou suas referências.
Avaliações não alteram eventos ou estado físico. Resolução automática não existe.

Limitações da preparação mantidas: sem migração, formatos sintéticos fechados,
quota/arquivos sem garantia concorrente nem sandbox; apenas dados locais do case.
Referência de envelope inválida é rejeição rastreável anterior à avaliação,
por integridade referencial, enquanto divergência extraída é avaliação
REFERENCE_MISMATCH. Essa distinção deve ser avaliada pelo gerente no aceite.
Não houve nova prova dedicada de identidade documental conflitante, ensaio
concorrente ou resolução manual; controles preparados não viram provas observadas.

Feito: R09 exercitado no recorte, código b88f88a e evidências/consulta acima.
Pendência única de governança: decisão central aceito/ajustes/bloqueado para P02.
Esta publicação não fecha F4 nem inicia IA. Não repetir provas já aprovadas
apenas porque a passagem foi consolidada. Próximo passo: levar documento 23
e SHA documental final ao gerente.
