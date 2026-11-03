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


## Execução Windows observada — evidências para submissão central

Estado: F4-P01 executado no recorte demonstrado, aguardando commit da
transformação de João e validação central. Não fecha F4 nem libera P02.

João apresentou o diff de normalize_delivered_at: ausência preservada;
datetime.fromisoformat, fuso obrigatório, conversão astimezone(UTC),
INVALID_FIELD_TYPE para erro. A transformação foi editada e executada por João;
explicação independente continua adiada, conforme cartão.

Após fetch/fast-forward até 6bbb4f5, git restore não regravou os PDFs CRLF.
A recuperação efetiva foi feita por João via subprocess.check_output de
`git show HEAD:caminho` e Path.write_bytes, sem passagem binária pelo shell.
Não foi relaxado strict=True nem regenerada fixture para contornar a falha.

Hashes SHA256 observados dos bytes recuperados:
- valid.pdf: fe49e47b0af8c7bb3b6f01fe921dba1599922b8ccd1cea8a7e54b1040e83a451
- missing.pdf: fb58389b45c2193a388c914de4b36683e02b016dd9558c171f127d4caa488069
- blank.pdf: 226bdbe274d3222c3ed276db4f6736d457282e01abf7982629360f7b4f1ad77b
- malformed.pdf: b9e295f0c86730ee956a72a38716ba58f3ab765ee596bbd92d70ad7b7218ed97

| Comando/prova | Esperado | Observado por João |
|---|---|---|
| pytest -q tests/documents | 23 aprovados | 23 passed in 0.29s; extraction_tests_exit=0 |
| check_document_extraction --database ilc_f2p02b_test | PASS, versões estáveis e histórico novo | verification=PASS; document_versions=8; document_verification_exit=0 |
| PDF/XML completos | cinco campos corretos; 14h -03 → 17h UTC | EXTRACTED; ENT-001, 17:00 UTC, 12, BOX, Pessoa Sintetica |
| PDF/XML sem receiver_name | EXTRACTED com ausência preservada | receiver_name=null, missing_fields=[receiver_name] |
| PDF branco | falha explícita | NO_EXTRACTABLE_TEXT / PARSING_FAILED |
| XML/PDF malformados | falha explícita | PARSING_ERROR / PARSING_FAILED |
| XML com entidade externa | bloqueio | XML_SECURITY_BLOCKED / PARSING_FAILED |
| Arquivo ausente | sem versão fictícia | FILE_MISSING; run FAILED |
| Formato não suportado | categoria própria | UNSUPPORTED_FORMAT; run FAILED |
| Reexecução das oito fixtures | mesma versão/input; extração nova | oito pares, 16 extrações distintas reportadas; duplicate=true na segunda de cada par |
| SHA256, bytes preservados e vínculos | iguais e coerentes no banco | asserts do verificador aprovados |
| Avaliações | nenhuma nova avaliação | evaluations_unchanged=true |
| Ruff nos módulos/CLIs/testes novos | aprovado | All checks passed; ruff_exit=0 |
| git diff --check | sem erro | nenhuma saída de erro |

Rastreabilidade de exemplo válido: document_key d8f497e6-8ca2-420a-81a1-2a9436467189;
input_key 3494053b-9154-43b9-9e87-d8f51de7b554;
runs document-1e6f4529-b0ed-4fac-9e21-2e7f2bbcd067 e
document-ed8128e8-2dc4-4616-82b7-e438c374c7fd;
extrações 0322cfb4-7cb2-463a-a729-a8d894f44fa9 e
5d116252-fee3-4b2c-8a74-3d10610d3adc. Parser educational-v1.
Run ausente: document-e2d3b3c8-31d0-4a6c-9878-8d1fb94b5486;
formato: document-9d4be2a8-755a-4c2e-9369-9a146f8f6184.
Os runs FAILED são casos negativos esperados; PASS do verificador não altera
seu estado. As 16 extrações são as retornadas nesta execução, não contagem
global certificada de toda a tabela. Recebimento original não nulo foi conferido
pelo script, mas seu valor não foi impresso no JSON. A consulta SQL autoral
separada do runbook ainda não foi apresentada; não alegar sua execução.

Último status informado: parser.py e quatro PDFs modificados; .vscode/ não
rastreado. O conteúdo dos PDFs será comparado com HEAD antes de atualizar o
índice; nenhuma alteração binária deve ser aceita por suposição. Configuração
local e .vscode/ preservadas. Commit da transformação e prova final Git ainda
pendentes; não atribuir o código autoral a um SHA ainda não publicado.

Feito/evidências: extração, falhas e idempotência exercitadas conforme tabela.
Aprendizagem prática: João editou transformação UTC, recuperou bytes originais,
executou instalação/testes/verificador/Ruff. Explicação independente adiada.
Limitações anteriores mantidas; não houve migração, avaliação/aprovação,
OCR, LLM, conferência de negócio, interface ou métricas. Regressão global
anterior não repetida. Próximo passo: verificar PDFs, publicar transformação,
consultar resultados existentes e devolver passagem com SHA ao gerente.


## Passagem consolidada ao gerente — F4-P01 entregue para validação

Autoridade: cartão F4-P01 encaminhado por João neste chat. Estado:
**ENTREGUE PARA VALIDAÇÃO CENTRAL**, sem aceite inferido e sem fechamento F4.
As seções de preparação acima são histórico; resultados executados constam
na seção Windows e nesta consolidação. Conferência documental/P02 e IA
não liberadas; F5–F6 bloqueadas.

- Repositório: Soba-Jopeca/integrated-logistics-control.
- Branch: feat/f4-p01-document-extraction, base 0186996c067e81602f8dc1289f40351912c6509b.
- Código final observado/publicado: **787f327**, transformação central de João.
- Evidências anteriores: c5dbc67; correção binária 4b4d079 e registro 6bbb4f5.
- Git demonstrado por João após push: HEAD=origin em 787f327, comparação 0 0;
  nenhuma alteração rastreada pendente, apenas .vscode/ não rastreado, preservado.
- Esta consolidação posterior é exclusivamente documental; código testado
  e fixtures permanecem os de 787f327. Sincronização deste novo documento
  no Windows não é presumida nem exigida como nova prova do código.

R08 demonstrado no recorte autorizado: PDF textual e XML educacional reais,
cinco campos, UTC, ausência preservada, falhas distintas e rastreáveis,
bytes/SHA256/origem/recebimento/run/parser e vínculos no modelo existente.
R15 contribuições limitadas ao recorte: tamanho/caminho controlados, DTD e
entidades bloqueados. Não declarar atendimento transversal completo.
Sem migração adicional, mudança de esquema, merge ou serviço pago.

| Critério F4-P01 | Evidência observada |
|---|---|
| PDF/XML válidos | campos esperados nos testes e nos reports do verificador |
| Ausência permanece null | receiver_name=null em PDF/XML e missing_fields correspondente |
| Malformado/PDF sem texto | PARSING_ERROR e NO_EXTRACTABLE_TEXT distintos |
| XML externo bloqueado | XML_SECURITY_BLOCKED, mantido em histórico |
| Hash/vínculo/histórico/idempotência | PASS SQL/arquivos; oito versões, oito pares de tentativas com 16 extrações reportadas; versão/input estáveis e nova extração |
| Sem aprovação | evaluations_unchanged=true; nenhum fluxo de avaliação inserido |

Comandos executados por João: instalação --require-hashes do lock;
pytest -q tests/documents (**23 passed in 0.29s, exit=0**);
check_document_extraction --database ilc_f2p02b_test (**PASS, exit=0**);
Ruff (**All checks passed, exit=0**); diff --check sem erro;
conferência byte a byte dos quatro PDFs contra HEAD; commit/push e rev-list 0 0.
Não foi necessário repetir essas provas após a publicação da mesma transformação.

Prática/autoria: João implementou normalize_delivered_at, executou instalação,
recuperação binária, testes/verificador/Ruff e publicou o commit. Assistente
preparou estrutura, formatos, fixtures, testes, persistência, comandos e revisão.
Aprendizagem prática observada nessas ações; explicação independente continua
adiada por autorização do cartão. Não atribuir a João explicação não apresentada.
Consulta SQL avulsa do runbook não foi apresentada; consulta de resultados foi
exercitada pelo verificador SQL executado por João, com reports retornados.
Cabe ao gerente avaliar essa limitação no critério de prática, sem inventar prova.

Limitações mantidas: formato sintético fechado; apenas versões iniciais;
quota local sem garantia concorrente; parser sem sandbox de memória/tempo;
verificação de stream após descompressão; arquivo órfão possível após rollback;
infraestrutura indisponível pode impedir log inicial. Testes pertinentes do
recorte executados, sem regressão global F3, CI/E2E ou ensaio concorrente novo.
Sem OCR/LLM/conferência/aprovação/interface/métricas; nenhuma integração
empresarial ou economia alegada. Esforço humano não medido.

**Solicitação ao gerente:** avaliar F4-P01 como aceito/ajustes/bloqueado com base
nas evidências, commit e limites acima. Não iniciar passo seguinte antes da
decisão central. Nenhuma mensagem automática enviada a outro chat.


## Aceite central recebido com F4-P02

**VAL-F4-P01-001**, por cartão humano de João no chat 04. P01 aceito no
recorte e com as limitações documentadas; código 787f327, passagem 80dec06.
F4-P02 autorizado; F4 permanece aberta e experimento IA não liberado.
