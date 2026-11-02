# F3-P01 - API de eventos: estrutura e pratica

Data: 02/11/2026. Base autorizada: 686a10597e1b708e79e75d1f63744c585fd40e57.
Estado: estrutura preparada; ligacao central e execucao Windows pendentes.
P01 e F3 NAO VALIDADOS. Ingestao bloqueada. Sem banco ou migracoes.

## Contrato desta entrega

GET /events?limit=5&cursor=...; limite 1..100, padrao 5.
Fonte exclusiva: tests/fixtures/synthetic/v1/valid/events.jsonl (13 registros).
Snapshot lido ao criar a app. Alteracoes no arquivo exigem reinicio.
Ordem: source_system, event_id e posicao original como desempate.
Nenhuma deduplicacao, filtro, correcao ou remocao de eventos.
Esta ordem de consulta nao define ordem de aceitacao de negocio.
A fixture valid inclui eventos com ambiguidades de negocio: servi-los nao e aprova-los.

Resposta: items, total, dataset_id, next_cursor e has_more.
Termino: next_cursor=null e has_more=false, inclusive conjunto vazio.
Com limite 5: 5/5/3 registros. O consumidor para ao receber null;
nao deve omitir cursor e comecar novamente apos o termino.
Cursor: base64url canonico de [versao, SHA256 dos bytes da fixture, offset].
Valida estrutura, versao, snapshot, inteiro nao booleano, faixa e codificacao.
Offset do cursor deve apontar para registro existente, depois da primeira posicao.
Cursor incorreto: 400 INVALID_CURSOR; comprimento acima de 256 ou limite invalido: 422.
Cursor nao e segredo, assinatura ou autorizacao: offsets validos podem ser construidos.
O percurso padrao deve seguir exclusivamente next_cursor.

OpenAPI vivo: /openapi.json. Swagger: /docs (assets padrao usam CDN).
Copia JSON: 16-f3-p01-openapi.json, gerada no ensaio de referencia.
Modelo Event descreve campos e tipos do contrato 06; entradas invalidas deliberadas
ficam fora deste endpoint e serao tratadas nos cenarios de falha posteriores.

## Pratica de Joao e preservacao local

Nao substituir mock_api/pagination.py, requirements.in, requirements.lock ou .vscode.
O arquivo de paginacao local foi fornecido por Joao e revisado em 02/11.
No novo mock_api/app.py, funcao page_events, substituir somente o raise
NotImplementedError por chamada a paginate com events, offset e limit,
retornando os dois valores. O assistente nao atribui essa ligacao a Joao antes da evidencia.
O import marcado noqa e intencional enquanto a ligacao nao foi preenchida.
Antes dessa edicao, GET /events falha de forma explicita; nao apresentar como API pronta.

Na venv Windows existente (sem instalar/atualizar pacotes):

    python -m ruff format mock_api tests/unit/test_events_api.py
    python -m ruff check mock_api tests/unit/test_events_api.py
    python -m ruff format --check mock_api tests/unit/test_events_api.py
    python -m pytest tests/unit/test_events_api.py -q
    python -m mock_api

O launcher fixa 127.0.0.1:8000. Em outro PowerShell:

    Get-NetTCPConnection -State Listen -LocalPort 8000 | Select-Object LocalAddress,LocalPort,OwningProcess
    Invoke-RestMethod 'http://127.0.0.1:8000/events?limit=5' | ConvertTo-Json -Depth 8
    Invoke-RestMethod 'http://127.0.0.1:8000/openapi.json' | ConvertTo-Json -Depth 20

Encerrar o servidor com Ctrl+C depois da verificacao. Joao deve executar chamada
com next_cursor recebido e explicar null/has_more=false; registrar saidas e Git diff.

## Ensaios do assistente, sem atribuir a execucao a Joao

Ambiente descartavel Linux/Python 3.12. FastAPI 0.150.0, Uvicorn 0.54.0,
HTTPX 0.28.1, Starlette 1.9.0, Pydantic 2.14.1, pytest 9.1.1, Ruff 0.17.1.
Outras transitivas podem diferir do lock Windows: nao e reproducao integral do lock.
Nenhuma dependencia ou lock do repositorio foi alterado nesta entrega.

Para verificar a estrutura, o assistente preencheu TEMPORARIAMENTE page_events
com a chamada de referencia a paginate, usando copia da funcao local informada.
Com essa ligacao: 24 testes passaram em 0.40s, Ruff check passou e format sem mudancas.
Cobertura: primeira/intermediaria/ultima parcial; conjunto vazio; percurso
reconciliado por igualdade integral de registros e ordem em limites 1,2,5,13,100;
cursor malformado, snapshot diferente, faixa/tipo invalidos; limites; OpenAPI.
Os testes leem a fixture diretamente para construir o esperado.

Houve aviso StarletteDeprecationWarning sobre HTTPX/TestClient; suite passou.
Nao instalar httpx2 nem mudar lock para suprimir aviso neste recorte.
A ligacao foi retirada do arquivo entregue, reservando a edicao central a Joao.
Portanto o pacote preparado NAO tem 24 testes aprovados como estado final:
a aprovacao refere-se exclusivamente a variante temporaria de referencia.

Servidor real de referencia iniciado em 127.0.0.1, porta efemera: HTTP retornou
5 itens, total 13, has_more=true; /openapi.json acessivel. Processo encerrado.
Isto nao verifica porta ou inicializacao no Windows de Joao.

## Passagem ao gerente

Estrutura: mock_api/__init__.py, app.py, __main__.py; testes e OpenAPI/documento 16.
Sem alteracao de requirements, lock, fixture, migracoes, main ou PR #2.
Arquivo pagination.py usado apenas como copia local para ensaio; nao incluido na entrega.

Pendentes: ligacao autoral, suite e loopback observados no Windows, explicacao
de termino, commit local incluindo paginacao/dependencias e publicacao.
Timeout, erro HTTP, JSON invalido e indisponibilidade ainda obrigatorios para P01,
fora deste recorte. Nenhum aceite de P01 ou liberacao de ingestao foi emitido.
