# F2-P01 - Ambiente reproduzivel

Data: 16/10/2026.
Estado: evidencias tecnicas obtidas; aguardando aprendizagem, commit e validacao central.
Branch: chore/f2-p01-environment.
Base autorizada: d7b8a093215dafc8c4476c8995fad5b64c9d4bbb.
Requisitos: R03 parcialmente; R15 na protecao da configuracao local.

## Diagnostico e decisoes

Windows 11 Pro x64; Python 3.13.14 x64; Git 2.55.0.windows.5.
RAM total 15,7 GB; livre 1,5 GB; disco C livre 33,5 GB no diagnostico.
Launcher py ausente; usado python e depois o executavel explicito da .venv.
psql e servico PostgreSQL nao encontrados nas consultas realizadas.
Isso nao comprova ausencia de toda instalacao possivel.

origin/main em 9f6720a possui conteudo anterior ao fechamento documental.
git diff HEAD origin/main identificou diferencas em README e documentos 04/08.
A protecao interrompeu a sincronizacao antes de modificar a branch.
Branch F2 criada diretamente da passagem autorizada d7b8a09.
Integracao com main permanece pendente; nenhum historico foi descartado.

## Dependencias e configuracao

requirements.in declara dependencias diretas e ferramentas.
requirements.lock fixa dependencias diretas/transitivas e hashes.
Resolucao gerada no Windows x64 com Python 3.13.14.
Nao foi demonstrada portabilidade do lock para outro sistema ou Python.

Versoes principais:
- pip 26.1.2; pip-tools 7.6.2
- SQLAlchemy 2.0.55
- psycopg e psycopg-binary 3.3.6
- Alembic 1.20.0
- python-dotenv 1.2.4
- pytest 9.1.1; Ruff 0.17.1

.env.example fornece LOG_LEVEL com padrao INFO.
.env e configuracao local ignorada pelo Git.
Joao ajustou a configuracao local; valores locais nao integram as evidencias.
A verificacao carregou .env com dotenv_values e aplicou logging.basicConfig.
Configuracao utilizada somente no exercicio de ambiente; aplicacao futura.

## Fontes oficiais consultadas antes da instalacao

Consultadas em 16/10/2026:
- https://docs.python.org/pt-br/3.13/library/venv.html
- https://pip.pypa.io/en/stable/topics/repeatable-installs/
- https://pip-tools.pypa.io/en/latest/
- https://pypi.org/project/pip-tools/7.6.2/
- https://docs.sqlalchemy.org/en/20/intro.html
- https://www.psycopg.org/psycopg3/docs/basic/install.html
- https://alembic.sqlalchemy.org/en/latest/front.html
- https://pypi.org/project/python-dotenv/
- https://docs.pytest.org/en/stable/getting-started.html
- https://github.com/astral-sh/ruff/blob/main/docs/faq.md

Compatibilidade documental complementada pela instalacao e imports locais.
Nao equivale a validacao funcional de banco ou migracoes.

## Comandos de reproducao - PowerShell na raiz

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: -r requirements.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import sys; assert sys.prefix != sys.base_prefix; print(sys.executable)"
.\.venv\Scripts\python.exe -c "import sqlalchemy, psycopg, alembic, dotenv, pytest; from psycopg import pq; assert pq.__impl__ == 'binary'"
Copy-Item .env.example .env
```

Copiar .env.example somente se .env ainda nao existir.
Reproducao usa o lock existente; nao exige regenera-lo.

## Evidencias observadas

- Interpretador dentro da .venv; prefix diferente de base_prefix: PASS.
- include-system-site-packages = false.
- pip check nos dois ambientes: No broken requirements found.
- Configuracao local carregada e ajuste aplicado: PASS.
- .env e .venv ignorados; .env.example permitido: PASS.
- Nova venv temporaria instalada pelo lock com hashes: PASS.
- Compare-Object das versoes sem diferencas: PASS.
- Imports e driver psycopg binario: PASS.

SHA256 requirements.lock:
704A34566E7C001AC45D2FB1ED0CA625F20E0792A47FEA3E89A21C6950F2EFBF

Limites: nova venv no mesmo Windows/Python, utilizando cache de pacotes.
Nao demonstra instalacao limpa do Windows nem portabilidade para outro sistema.
pytest e Ruff instalados; nenhum teste de dominio executado.

## Participacao, tempo e passagem

Joao executou preparacao, instalacao, ajuste local e verificacoes.
Assistente forneceu comandos e orientacao.
Explicacao autoral de aprendizagem: pendente.
Inicio: 2026-10-16T22:10:55.4891698-03:00.
Fim e esforco ativo: pendentes; intervalo de mensagens nao equivale a esforco.

Pendencias: registrar aprendizagem, revisar/publicar commit e retornar ao gerente.
Integracao com main pendente; branch preserva a passagem autorizada da F1.
.vscode local fora deste commit; conteudo nao revisado.
Ambiente temporario de reproducao ainda nao removido.

Nenhum banco, tabela, migracao ou gerador criado.
R03 e F2 nao estao integralmente concluidos.
Proximo passo somente apos validacao e novo cartao do gerente.
