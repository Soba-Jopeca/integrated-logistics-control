# F2-P02A - PostgreSQL local e conexao Python

Data: 19/10/2026.
Estado tecnico: conexao comprovada; validacao do gerente pendente.
Branch: chore/f2-p02a-postgresql.
Base: acbff3da02cc06753c755b8ce549ead698e151c8.
Requisitos: R03 parcialmente; R15 na configuracao e privilegios locais.

## Escopo e diagnostico

Windows 11 Pro x64; RAM total 15,69 GB; livre 1,36 GB.
Disco C livre: 34,24 GB.
Consultas nao encontraram servico PostgreSQL, comandos no PATH
ou diretorio padrao. Isso nao comprova ausencia de toda instalacao.
Portas 5432, 5433 e 55432 sem listener no diagnostico.
.vscode nao rastreada preservada; nenhum descarte de alteracoes.

## Preparacao observada

Instalador: postgresql-18.6-5-windows-x64.exe.
Assinatura Authenticode: Valid; EnterpriseDB Corporation.
SHA256:
227E2BC08091B4C2B8338C7D61B11D057F895711480B006F90BFCFCD2410A58A

Metadado FileVersion do instalador: 1.0.0.0.
Versao efetiva comprovada por postgres, psql e servidor: 18.6.
Extracao com --extract-only, sem instalacao de servico solicitada.
Binarios ativos: C:\ILC-PostgreSQL\18.6\bin.
Cluster: C:\ILC-PostgreSQL\ilc-data-18.
Diretorio dedicado com ACL para usuario executor, SYSTEM e Administradores.
Original extraido em LOCALAPPDATA permanece; limpeza nao executada.

initdb: UTF8, locale C, autenticacao scram-sha-256.
Administrador de preparacao: ilc_admin.
Banco do case: ilc; proprietario e usuario de conexao: ilc_app.
Nenhuma tabela de dominio, migracao ou gerador criado.

## Configuracao e verificacoes observadas

Servidor: listen_addresses=127.0.0.1; port=55432; timezone=UTC.
shared_buffers=64MB; max_connections=20.
Windows confirmou listener 127.0.0.1:55432.
password_encryption=scram-sha-256.
ilc_app: LOGIN; limite de 5 conexoes.
Sem SUPERUSER, CREATEDB, CREATEROLE, REPLICATION ou BYPASSRLS.
Como proprietario do banco, ilc_app pode criar objetos no proprio banco.
Nao equivale a um usuario de producao limitado apenas a DML.

Python 3.13.14; SQLAlchemy 2.0.55; psycopg 3.3.6.
Verificador: scripts/check_db_connection.py.
Executado pela .venv; transacao somente leitura; conexao: PASS.
Retornou ilc_app, ilc, servidor 18.6, 127.0.0.1:55432, UTC
e todos os cinco indicadores administrativos como false.
URL.create monta a conexao sem concatenar senha na URL textual.
dotenv_values usa interpolate=False; senha e URL nao sao impressas.
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD e DB_CONNECT_TIMEOUT
sao utilizados pelo verificador; senha real somente no .env local.

## Ocorrencias e limites

Primeiro initdb falhou com invalid byte sequence for encoding UTF8.
Diretorio incompleto removido pelo proprio initdb.
Caminho anterior continha Joao com acento.
Transferencia para caminho ASCII seguida de initdb teve sucesso.
Causa de codificacao do caminho e provavel, nao isolada formalmente.

Primeiro verificador terminou com RuntimeError sem motivo detalhado.
SQL ajustado de inet_server_addr()::text para host(inet_server_addr()).
Adicionada lista permitida de mensagens diagnosticas sem segredos.
Reexecucao passou; motivo original nao foi capturado individualmente.

Execucao local observada; sem teste em outro computador.
Sem instalacao ou alteracao solicitada de servicos de outros projetos.
Sem Docker, nuvem, OCR ou LLM neste cartao.

## Operacao - PowerShell

Iniciar, se parado:
    & 'C:\ILC-PostgreSQL\18.6\bin\pg_ctl.exe' start -D 'C:\ILC-PostgreSQL\ilc-data-18' -l 'C:\ILC-PostgreSQL\ilc-data-18\server.log' -w

Verificar:
    .\.venv\Scripts\python.exe scripts/check_db_connection.py

Parar somente esta instancia:
    & 'C:\ILC-PostgreSQL\18.6\bin\pg_ctl.exe' stop -D 'C:\ILC-PostgreSQL\ilc-data-18' -m fast -w

Nao executar initdb novamente sobre o cluster.
Nao copiar .env.example sobre um .env existente.
Nao excluir diretorios de dados como procedimento de rollback.
Parada e nova partida acima documentadas; ciclo completo ainda nao testado.

## Fontes oficiais consultadas antes da preparacao

- https://www.postgresql.org/download/windows/
- https://www.postgresql.org/support/versioning/
- https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- https://www.enterprisedb.com/docs/supported-open-source/postgresql/installing/command_line_parameters/
- https://www.enterprisedb.com/docs/supported-open-source/postgresql/installing/windows
- https://www.postgresql.org/docs/18/app-initdb.html
- https://www.postgresql.org/docs/18/app-pg-ctl.html
- https://www.postgresql.org/docs/18/runtime-config-connection.html
- https://www.postgresql.org/docs/18/app-createuser.html
- https://www.postgresql.org/docs/18/app-createdb.html
- https://www.postgresql.org/docs/18/sql-createrole.html
- https://docs.sqlalchemy.org/en/20/core/engines.html
- https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- https://www.psycopg.org/psycopg3/docs/basic/install.html

Pagina Psycopg consultada apresenta documentacao de desenvolvimento.
Compatibilidade efetiva das versoes instaladas comprovada pela conexao.

## Participacao, esforco e passagem

Joao executou preparacao, definiu senhas e ajustou configuracao local.
Assistente preparou comandos, verificador e documentacao.
Explicacao autoral ainda nao coletada; nao inferida da execucao.
Inicio registrado: 2026-10-19T15:20:42.3946239-03:00.
Esforco ativo nao consolidado; intervalo entre mensagens nao e medicao.
Commit e publicacao devem ser identificados na passagem e no historico Git.
F2 permanece aberta; R03 parcial.
Proximo passo depende de validacao e novo cartao central.

## Revisao final observada

Ruff format aplicado ao verificador.
Ruff check inicialmente apontou BLE001 por captura generica de Exception.
Corrigido para SQLAlchemyError, OSError, ValueError, RuntimeError e KeyError.
Nova execucao Ruff: All checks passed!
Conexao Python apos correcao e formatacao: PASS.
DB_PASSWORD vazio no .env.example: PASS.
git check-ignore confirmou protecao de .env e .venv.
Nao foram executados testes de dominio neste cartao.
