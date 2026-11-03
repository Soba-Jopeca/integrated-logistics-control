# 22 — F4-P01: extração determinística — preparação para prática

Data: 02/11/2026. Estado: EM EXECUÇÃO, NÃO VALIDADO.
Autorização: cartão humano F4-P01 recebido no chat 04.
Base: 0186996c067e81602f8dc1289f40351912c6509b.
Branch: feat/f4-p01-document-extraction.
F3 fechada com limitações por VAL-F3-P04-001, conforme documento 21.
F4 aberta; conferência/histórico de avaliações e IA não iniciados; F5–F6 bloqueadas.

## Escopo e artefatos preparados pelo assistente

- src/documents/parser.py: PDF textual com cinco rótulos exatos, XML educacional
  delivery_receipt; quantidade inteira, ausência/null preservados. Formato
  sintético fechado, não extrator genérico de comprovantes do mercado.
- src/documents/service.py: bytes locais por SHA256, inputs/receipts/runs/attempts,
  versão documental inicial, vigência e extrações no esquema existente.
- scripts/document_extract.py: CLI restrita pelo test_engine existente.
- scripts/check_document_extraction.py: prova SQL/arquivos preparada, NÃO executada.
- tests/fixtures/documents/v1: três PDFs reais, quatro XMLs, PDF malformado;
  expected.json separado. Fixtures e envelopes são sintéticos.
- tests/documents/test_parser.py: 23 testes offline, sem conexão ao banco.

Não há migração adicional: 0002 já contém os campos e vínculos necessários.
Nenhuma avaliação é inserida e nenhuma entrega é aprovada por este código.

## Prática autoral pendente

O cartão reserva uma transformação central a João. normalize_delivered_at está
intencionalmente incompleta: valor presente lança AUTHOR_TRANSFORMATION_PENDING.
Não utilizar o pipeline no banco antes dessa edição e dos testes verdes.

Substituir somente essa função em src/documents/parser.py por:

```python
def normalize_delivered_at(value):
    """Preserva ausência, exige fuso e normaliza para UTC."""
    from datetime import UTC, datetime

    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Timezone required")
        return parsed.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        raise DocumentError("INVALID_FIELD_TYPE") from None
```

Esperado: 2026-10-16T14:00:00-03:00 → 2026-10-16T17:00:00+00:00;
None continua None; horário sem fuso é erro. Explicação independente adiada
conforme o cartão; edição, execução e consulta de João ainda não demonstradas.

No Windows, sincronizar a branch preservando .vscode e .env:

```powershell
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch falhou.' }
git switch --track origin/feat/f4-p01-document-extraction
if ($LASTEXITCODE -ne 0) { throw 'Preservar alteracoes e investigar branch.' }
.\.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw 'Instalacao interrompida.' }
```

Se a branch já existir, usar git switch feat/f4-p01-document-extraction e
merge --ff-only origin/feat/f4-p01-document-extraction. Não executar reset/clean/stash.
Depois da edição central:

```powershell
python -m ruff check src/documents scripts/document_extract.py scripts/check_document_extraction.py tests/documents
python -m pytest -q tests/documents
Write-Output "extraction_tests_exit=$LASTEXITCODE"
```

Próxima ação única desta passagem: João edita e executa esses testes, devolvendo
saídas. Após revisão do resultado, ainda no mesmo cartão, executar o verificador:

```powershell
python -m scripts.check_document_extraction --database ilc_f2p02b_test
Write-Output "document_verification_exit=$LASTEXITCODE"
```

O verificador escreve somente no banco de testes já usado no case. Exige
revisão 0006_reliability e ENT-001 existente; não migra nem recria o banco.
Roda duas vezes cada uma das oito fixtures, preservando tentativas anteriores.
Espera oito versões documentais nessa origem exclusiva, ao menos duas extrações
por versão, mesmos document_key/input_key por reexecução, extraction_key novo,
hashes iguais aos bytes preservados, recebimento original e avaliações inalteradas.
Reexecuções posteriores acrescentam histórico; não exigir total global fixo de
extrações/tentativas. Não executar agora antes da transformação/testes.

Consulta posterior, em sessão SQL do banco de testes:

```sql
SELECT d.document_id,d.version,d.file_sha256,i.received_at,a.run_id,
       x.extractor_version,x.outcome,x.error_category,
       x.declared_delivery_id,x.delivered_at,x.received_quantity,
       x.quantity_unit,x.receiver_name
FROM ilc.document_versions d JOIN ilc.inputs i USING(input_key)
JOIN ilc.extractions x USING(document_key,input_key)
JOIN ilc.attempts a ON a.attempt_id=x.attempt_id AND a.input_key=x.input_key
WHERE d.source_system='synthetic_documents_p01'
ORDER BY d.document_id,x.extracted_at;
```

## Esperado × observado nesta preparação

| Prova | Esperado | Observado pelo assistente |
|---|---|---|
| Ruff nos arquivos novos | sem erro | All checks passed |
| Testes offline antes da prática | controles independentes passam; transformação pendente falha | 18 passed, 5 failed, 0.27s; saída 1 |
| Quatro PDFs/XML com data presente | dependem da transformação central | AUTHOR_TRANSFORMATION_PENDING |
| Data sem fuso | INVALID_FIELD_TYPE após edição | falha atual por transformação pendente |
| XML externo/DTD/entidades, XML/PDF malformados, PDF sem texto | falhas próprias | testes offline aprovados |
| Ausências, zero, tipos inválidos, tamanho, armazenamento/hash | controles do teste | testes offline aprovados |
| PDFs válido/ausente/branco | renderização correspondente | conferidos visualmente por PNG |
| PostgreSQL, histórico e idempotência | prova executada por João | NÃO EXECUTADO; script apenas preparado |

Não foram mascaradas falhas por skip/xfail. Estes resultados não constituem
aceite de R08 nem conclusão de F4-P01. Regressão F3 não foi repetida, nem
atribuídos seus 98 testes à nova implementação. Ambiente de preparação:
Python 3.12, venv isolada; dependências de apoio instaladas aqui não representam
reprodução do lock completo Windows. Windows/Python 3.13 ainda pendentes.

## Dependências e limites

Fontes oficiais consultadas antes da instalação:
https://pypi.org/project/pypdf/6.1.3/ (BSD-3-Clause, Python >=3.9),
https://pypi.org/project/defusedxml/0.7.1/ (PSF),
https://github.com/tiran/defusedxml/blob/main/defusedxml/ElementTree.py,
https://pypdf.readthedocs.io/en/latest/user/extract-text.html.
Pins 6.1.3 e 0.7.1 são versões específicas, não alegação de versões mais recentes.
Lock anterior preservado; acrescentadas rodas pure-Python com hashes calculados.
Compatibilidade nominal com Python 3.13 não substitui instalação observada.
ReportLab foi usado apenas pelo assistente na criação das fixtures; PDFs
versionados dispensam dependência de geração no projeto.

Limites: 1 MiB por arquivo, cinco páginas PDF, 1 MiB por conteúdo de página
após descompressão; quota local 32 MiB verificada antes de gravar arquivo novo.
Bytes ficam em data/documents, ignorados pelo Git; nome original não forma o
caminho de destino. DTD/entidades/externos proibidos por defusedxml.
Sem OCR, LLM, métricas, aprovação, regra de comparação com entrega ou interface.
Substituição/versionamento posterior à versão 1 aguarda cartão próprio.

Ausência/arquivo vazio/excesso de tamanho gera run FAILED, sem versão fictícia
ou hash inventado. Formato não suportado com bytes disponíveis preserva input,
receipt e tentativa rejeitada; arquivo malformado suportado gera versão e
PARSING_FAILED. Campo ausente não torna parsing falho: EXTRACTED com null.
A rejeição de referência/envelope não é conferência de negócio nem avaliação.

Limites conhecidos: quota/armazenamento não têm garantia concorrente entre
processos; proteção de symlink não é sandbox contra usuário local hostil;
checagem de stream PDF ocorre após descompressão e não limita pico de memória.
Não submeter PDFs arbitrários da internet nem alegar isolamento de parser;
case usa apenas fixtures sintéticas locais pequenas. Arquivo armazenado antes
da transação pode ficar órfão após rollback, sem remoção automática.
Falha na conexão inicial pode impedir o próprio registro do run; nenhuma prova
de persistência de falhas de infraestrutura é alegada.

Feito: estrutura, fixtures, verificações e orientação preparadas pelo assistente.
Aprendizagem de João: pendente de edição/execução/consulta observadas.
Pendências: transformação central, testes verdes, instalação Windows e prova SQL,
regressão pertinente, commit de evidências e devolução ao gerente.
Sem merge, manipulação da configuração Windows ou avanço para P02.
Esforço humano não medido. Esta é passagem intermediária; não submissão de aceite.


## Evidência Windows e correção de checkout — 02/11/2026

João criou a branch com tracking, instalou o lock com --require-hashes e
executou os 23 testes: 20 passed, 3 failed in 0.59s. As duas fixtures XML
com horário e a rejeição de data sem fuso passaram; a edição local da
transformação é compatível com esses resultados, mas seu diff ainda não
foi recebido nem publicado. Não sobrescrever src/documents/parser.py.

Falharam valid.pdf, missing.pdf e blank.pdf. Os bytes impressos na saída
Windows têm CRLF. O assistente reproduziu: os três PDFs originais abrem
com strict=True (uma página cada); converter LF para CRLF faz os três
falharem com PdfReadError: Broken xref table. .gitattributes não cobria
fixtures documentais. Correção 4b4d079: documentos textuais LF e *.pdf binary.
Parser estrito mantido; não mascarar corrupção nem regenerar comprovantes.

Próxima execução: fetch/merge --ff-only da branch, preservando alteração
local do parser; verificar git diff --name-only para os quatro PDFs e,
somente se não houver edição intencional nesses arquivos, restaurar apenas
esses quatro caminhos de HEAD para o worktree. Isso reaplica os atributos
binários e recupera os bytes versionados. Não restaurar o parser ou diretório
inteiro. Depois executar novamente os 23 testes e enviar saída/diff do parser.
Instalação Windows comprovada; teste PDF corrigido, prova SQL e aceites
continuam pendentes. Nenhuma escrita em banco feita nesta correção.
