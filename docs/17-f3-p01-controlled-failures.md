# F3-P01 - Falhas controladas por HTTP real

02/11/2026. Base: f177262ec78e68adedd26ffb729eddc679f5c8c3.
Branch: feat/f3-p01-events-api. Mandato humano: cenarios de falha liberados.
Estado: implementado e exercitado pelo assistente; execucao Windows de Joao
pendente. P01 continua aberto ate aceite central. Explicacao independente
adiada por Joao para revisao final. Sem retry, ingestao ou escrita no banco.

## Ativacao e esperado

Rotas separadas: GET /events continua normal e usa a mesma fixture/snapshot.
As falhas nao sao payloads de eventos invalidos. Estao identificadas em
/scenarios no OpenAPI (arquivo 16 atualizado).

| Ativacao com servidor em loopback | Esperado no cliente |
|---|---|
| /scenarios/delay?seconds=1; timeout de leitura=0.2s | httpx.ReadTimeout; sem status/corpo recebido |
| /scenarios/http-503 | HTTP 503, corpo {"scenario":"http_503","error":"SIMULATED_UNAVAILABLE"}; raise_for_status gera HTTPStatusError |
| /scenarios/invalid-json | HTTP 200, application/json, bytes de texto `{"scenario":"invalid_json",`; json() gera JSONDecodeError |
| /events na mesma porta APOS encerrar o servidor | httpx.ConnectError; sem resposta HTTP; distinto de timeout |

Delay: asyncio.sleep, parametro validado entre 0.1 e 2 segundos; padrao 1.
E atraso real do servidor; nao e resposta HTTP com rotulo "timeout".
O timeout e uma decisao do cliente. GET /scenarios/delay com timeout maior
pode concluir normalmente com a identificacao do cenario.
503 e erro HTTP recebido, nao ausencia de conectividade. JSON malformado
tem sucesso apenas na camada HTTP; parsing falha e nunca vira evento valido.

## Verificador e comandos Windows

Na venv ja existente, a partir da raiz do repositorio:

    python -m ruff check mock_api scripts/check_api_failures.py tests/unit/test_events_api.py tests/unit/test_api_failures.py
    python -m ruff format --check mock_api scripts/check_api_failures.py tests/unit/test_events_api.py tests/unit/test_api_failures.py
    python -m pytest tests/unit/test_events_api.py tests/unit/test_api_failures.py -q
    python -m scripts.check_api_failures

O ultimo comando inicia seu proprio Uvicorn em 127.0.0.1, porta efemera.
Nao depende de servidor manual na 8000. Nao termina processos preexistentes.
HTTPX com trust_env=False evita proxy de ambiente nas chamadas locais.
Sondagem de prontidao limitada a 10s; nao e retry dos cenarios.
Cada cenario e chamado uma vez. Timeout=0.2s, servidor espera 1s;
limite de observacao 3s. Conexao pos-parada tem timeout=0.5s.
Nao ha comparacao exata com duracoes nominais, sujeitas ao SO.

Processo encerrado em finally, wait limitado a 5s, kill do proprio filho
somente se necessario, seguido de wait de ate 5s. Sem processo permanente.
Em falha inesperada: codigo de saida nao zero e verification=FAIL para as
excecoes previstas; outras excecoes propagam traceback/codigo nao zero.
PASS significa que o verificador observou a falha esperada, nao que a requisicao
falhada foi processada com sucesso. Campos outcome preservam a classificacao.
Nenhuma ausencia de resposta recebe status HTTP inventado.

A selecao de porta tem janela bind-release; se houver disputa o ensaio pode
falhar e deve ser investigado. A chamada pos-parada detecta resposta inesperada
caso outro processo passe a usar a porta. Nao ha promessa de isolamento de SO.

Para experimentar manualmente as rotas: python -m mock_api (127.0.0.1:8000),
GETs nos caminhos da tabela acima. Parar com Ctrl+C. O verificador automatiza
esse ciclo em outra porta e preserva status/corpo das respostas recebidas.

## Evidencia do assistente: esperado x observado

Linux, Python 3.12.14, ambiente isolado de verificacao, nao o Windows de Joao.
FastAPI 0.150.0, Uvicorn 0.54.0, HTTPX 0.28.1, Starlette 1.9.0,
Pydantic 2.14.1, pytest 9.1.1, Ruff 0.17.1. Outras transitivas podem diferir
do lock Windows. Nenhum requirements/lock do repositorio alterado.

Ensaio real: 127.0.0.1:60075, PID filho 40; child_stopped=true.

| Esperado | Observado |
|---|---|
| Normal antes/depois preservado | HTTP 200, 5 itens, total 13, respostas iguais |
| ReadTimeout, nao ConnectError | READ_TIMEOUT; 0.201s; status/body null |
| HTTPStatusError com 503 e corpo exato | HTTP_STATUS_ERROR; 503; corpo da tabela preservado |
| HTTP 200 seguido de JSONDecodeError | JSON_DECODE_ERROR; 200; corpo invalido exato preservado |
| ConnectError apos wait do filho | CONNECT_ERROR; 0.005s; status/body null |
| Encerramento | finally concluiu, filho encerrado antes do teste de conexao |

Regressao: 32 testes aprovados em 1.85s (24 anteriores + 8 novos), sem banco.
Ruff check e format aprovados. Novo teste HTTP real executa todos os cenarios
mais verificacao do endpoint normal antes/depois e encerramento. Seis casos
validam limites/nao finitos do delay; um confere rotas no OpenAPI.
Aviso HTTPX/TestClient preservado como manutencao nao bloqueante por mandato.

## Passagem ao gerente

Diff: mock_api/app.py inclui router; mock_api/failures.py;
scripts/check_api_failures.py; tests/unit/test_api_failures.py;
OpenAPI 16 atualizado; este documento. Endpoint normal e dependencias preservados.
Registros/documentos 16 anteriores sao historicos; este documento acrescenta
os cenarios sem atribuir execucao Windows ainda nao recebida.

Joao deve executar os quatro comandos, enviar resultados, codigo de saida do
verificador e git status/HEAD. Confirmar processos encerrados com resultado
child_stopped=true e ausencia do PID filho na listagem do SO.
Apos receber evidencias, registrar observado Windows e devolver ao gerente
para aceite final de P01. Explicacao independente fica para revisao final.
Sem aceite central, nenhuma ingestao ou fase seguinte e liberada.
