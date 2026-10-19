# F2-P02B - Primeira revisao fisica e migracao reversivel

Data: 19/10/2026. Branch: feat/f2-p02b-migrations.
Base: 2c0ab8bf9cca9e6221cabf60c1ff1b8735db2742.
Entrada: contratos 06 e modelo 07 nessa base; F2-P02A encerrado com limitacoes
conforme cartao central recebido neste chat.

Estado: estrutura PREPARADA pelo assistente, nao validada no PostgreSQL.
F2-P02B EM EXECUCAO; F2 aberta; R03 parcial. Sem gerador, API ou ETL.

## 1. Escopo desta divisao

Revisao Alembic 0001_core: oito tabelas no schema ilc:
sources, inputs, receipts, runs, attempts, orders, deliveries e events.
O schema ilc e o banco de dados ilc sao conceitos distintos.
Neste cartao a revisao so pode atingir o banco descartavel ilc_f2p02b_test.
O banco ilc permanece como referencia de conexao da etapa anterior.

PENDENTES de revisoes posteriores: familias e versoes documentais,
extracoes, avaliacoes, motivos, vigencias, decisoes de conclusao,
conflitos, evidencias e resolucoes. Modelo 07 inteiro NAO implementado.
Sem metricas, selecao de estado fisico ou regularidade documental.

## 2. Evidencia ja observada de operacao

Inicio informado de F2-P02B: 2026-10-19T17:06:07.7438190-03:00.
Git local confirmado na base; .vscode nao rastreada preservada.
Branch local criada: feat/f2-p02b-migrations.
Verificador Python antes da parada: PASS.
pg_ctl status confirmou a instancia em C:\ILC-PostgreSQL\ilc-data-18,
PID anterior 30384. Parada fast concluida; porta 55432 liberada.
Reinicio concluido, listener 127.0.0.1:55432, PID 14584.
Verificador Python apos reinicio: PASS, ilc_app/ilc, servidor 18.6,
UTC, cinco privilegios administrativos false, limite de cinco conexoes.
Nenhuma outra instancia foi alvo dos comandos fornecidos.
Esforco ativo ainda nao consolidado; nao inferir pelo intervalo de mensagens.

## 3. Decisoes fisicas e fronteira banco/aplicacao

| Regra | Garantia nesta revisao | Complemento pendente |
|---|---|---|
| Identidade de evento por origem | UNIQUE(source_system,event_id), a implementar por Joao | Classificar reenvio identico versus conflito, sem sobrescrita |
| Identidade de pedido | PK UUID e UNIQUE(source_system,order_id) | Aceitacao de entradas de pedido |
| Uma entrega por pedido | FK obrigatoria e UNIQUE(order_key); delivery_id global unico | Orquestracao de criacao |
| Origem, entrada e tentativa do evento coerentes | FKs compostas incluindo input_key, source_system e input_type | Validar payload declarado e resultado da tentativa de aceitacao |
| Tentativa e recebimento da mesma entrada | FK composta; receipt_key nulo para repeticao interna | Cada entrada deve ter chegada inicial e received_at=min(recebimentos) |
| Ordem de aceitacao por entrega | Sequencia positiva e unica | Alocar sequencia sob concorrencia; nao escolher por occurred_at |
| Conteudo preservado | Referencia original/checksum; hash minusculo de 64 caracteres; fingerprint/versao ou motivo de falha | Calcular e comparar bytes; validar normalizacao e arquivos |
| Historico imutavel | Triggers impedem UPDATE/DELETE em inputs, receipts e events | Proprietario do banco pode alterar DDL; separacao de roles de producao nao entregue |
| Vinculos historicos | FKs ON DELETE RESTRICT; sem cascata de exclusao | Politicas completas das entidades ainda nao criadas |
| Campos e tipos | UUID, NOT NULL, CHECK de enum, versao, texto, quantidade nao negativa, datas timestamptz | Rejeitar data de origem sem fuso e campos desconhecidos antes de inserir |
| Datas de processo | Fim nao anterior ao inicio; estados finais com fim/resultado; falha com categoria | Transicoes de estado, controle de concorrencia e logs sem segredos |
| Estado fisico e documental | Nao materializados nem confundidos | Derivar no codigo das fases seguintes; atraso e conflitos ainda nao processados |

Conversoes logicas: ORIGEM=sources; ENTRADA=inputs; RECEBIMENTO=receipts;
EXECUCAO=runs; TENTATIVA=attempts; PEDIDO=orders; ENTREGA=deliveries;
EVENTO=events. Chaves UUID sao fornecidas pelo chamador; nenhuma extensao
ou gerador e instalado. request_data JSONB preserva os dados do pedido.
inputs.input_type usa EVENT/DOCUMENT para rastreabilidade inicial,
sem implementar o dominio documental nesta divisao.

Vocabulario fisico local de execucao: RUNNING, SUCCEEDED, FAILED, PARTIAL.
Tentativa em andamento: outcome/ended_at nulos; final: ACCEPTED, REJECTED,
DUPLICATE, CONFLICT ou FAILED com ended_at. Esses nomes operacionalizam
os estados logicos; nao comprovam uma rotina de ingestao.

## 4. Pratica central de Joao

Editar migrations/versions/0001_core.py, funcao add_event_identity_constraint.
Substituir NotImplementedError por op.create_unique_constraint:
nome uq_events_source_event; tabela events; colunas source_system e event_id;
schema ilc. Preservar os demais trechos.
O scaffold e intencionalmente incompleto ate essa alteracao.
O teste de catalogo e os casos duplicado/mesmo ID em outra origem verificam
a restricao. A chamada acontece dentro da transacao da migracao.
Se nao implementada, upgrade falha e o DDL deve ser revertido pela transacao.
Nao afirmar essa reversao como observada antes de executar.

Perguntas para interpretacao apos execucao:
- Por que repetir um ID na mesma origem falha e em outra origem passa?
- Qual vinculo protege contra associar uma tentativa de outra entrada?
- O que foi removido pelo downgrade e qual banco ficou preservado?

## 5. Configuracao e comandos previstos (ainda nao executados)

Dependencias mantidas no lock de F2-P01; nenhum pacote novo.
Segredos somente em .env, lido com interpolate=False.
URL.create; echo=False; hide_parameters=True; NullPool; timeout limitado.
alembic.ini nao contem URL nem senha.
DDL exige -x database=ilc_f2p02b_test; sem alvo explicito falha.
Nao ha fallback de DDL para DB_NAME=ilc. Modo offline nao habilitado.
public.alembic_version fica fora do schema de dominio; em base pode existir
vazia. DROP SCHEMA sem CASCADE recusa objetos inesperados.

Criar o banco descartavel UMA vez, com senha administrativa no prompt:

    & 'C:\ILC-PostgreSQL\18.6\bin\createdb.exe' -h 127.0.0.1 -p 55432 -U ilc_admin -W --owner=ilc_app --template=template0 --encoding=UTF8 ilc_f2p02b_test

Nao repetir se o banco ja existir. Nao reutilizar outro banco com dados.
Inspecionar base vazia antes de qualquer upgrade:

    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect base

Depois da alteracao central de Joao e revisao:

    .\.venv\Scripts\python.exe -m ruff format migrations scripts/migration_config.py scripts/inspect_migration.py tests/integration/test_core_migration.py
    .\.venv\Scripts\python.exe -m ruff check migrations scripts/migration_config.py scripts/inspect_migration.py tests/integration/test_core_migration.py
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade head
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
    $env:ILC_TEST_DATABASE = 'ilc_f2p02b_test'
    .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test downgrade base
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect base
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade head
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
    .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py
    Remove-Item Env:ILC_TEST_DATABASE
    .\.venv\Scripts\python.exe scripts/check_db_connection.py

Executar comandos em blocos controlados e interromper em qualquer falha.
Downgrade elimina as oito tabelas desta revisao e seus dados de teste.
Nao e restauracao de dados; nao apaga banco nem cluster. A subida seguinte
recria estrutura vazia. Os testes usam transacoes revertidas e savepoints;
fixtures nao sao persistidas entre os comandos.

## 6. Verificacoes preparadas e esperado

- Catalogo com oito tabelas e UNIQUE do autor na ordem correta.
- Evento valido e evento com ocorrencia anterior aceitos; isso nao testa
  selecao de estado fisico, ainda nao implementada.
- Mesmo ID em outra origem aceito; mesma origem/ID rejeitado com 23505.
- Referencia desconhecida, tentativa de outra entrada, origem divergente
  e entrada de tipo DOCUMENT rejeitadas por FK (23503).
- PKs, sequencia unica, NOT NULL, enums e checks de quantidade/texto/hash.
- Segundo delivery para o mesmo pedido rejeitado; exclusao do pedido
  referenciado rejeitada. UPDATE/DELETE do historico rejeitados.
- Processo com fim anterior ao inicio e tentativa final sem resultado
  rejeitados. Reprocessamento interno sem novo receipt aceito.
- Perfil sem privilegios administrativos confirmado na conexao de teste.
- Estados head/base/head inspecionados independentemente pelo catalogo.

Resultado nesta preparacao: sintaxe Python compilada no ambiente do assistente.
Sem PostgreSQL, Alembic ou Ruff disponiveis nesse ambiente: testes de banco
e lint ainda NAO executados. DDL ainda nao comprovado. Resultados reais,
hash do commit final, aprendizagem e esforco deverao constar na devolucao.

## 7. Fontes oficiais consultadas

- https://alembic.sqlalchemy.org/en/latest/tutorial.html (documentacao 1.20.0)
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://www.postgresql.org/docs/18/app-pg-ctl.html
- https://www.postgresql.org/docs/18/app-createdb.html
- https://docs.sqlalchemy.org/en/20/core/engines.html

Nenhuma fase ou cartao seguinte liberado por este documento.
