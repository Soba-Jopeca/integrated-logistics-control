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
