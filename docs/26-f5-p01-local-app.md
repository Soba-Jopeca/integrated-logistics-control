# F5-P01 — Aplicação local: preparação e evidências

Data: 03/11/2026. Requisito R11; R15 transversal. Estado: **em execução,
sem aceite central e sem jornada humana comprovada**. F6 bloqueada.

## Mandato e baseline

Cartão humano F5-P01; base `97348e2922c56e7b8a6a3765af4f007456f7bd16`,
`docs/f4-p04-consolidation`. Passagem 25 lida: F4 FECHADA COM LIMITAÇÕES,
VAL-F4-P04-001. Branch `feat/f5-p01-local-app`, criada exatamente dessa base.
Fetch remoto confirmou o SHA. Worktree anterior estava limpo; criada cópia
separada, sem alterar configuração, `.env`, `.vscode/` ou branch anterior.
Estado do Windows de João ainda deve ser conferido; não presumir sincronização.

## Implementação preparada pelo assistente

`app/local_app.py`: busca por identificador, filtros independentes, consulta
explícita sem cache, horário de consulta São Paulo, detalhes e histórico.
`src/application/service.py`: lista com uma linha por entrega (sem join
multiplicador), regularidade via serviço F4, consultas parametrizadas,
upload até 1 MiB, temporário com nome controlado e armazenamento F4 por hash.
Extração e conferência existentes são chamadas separadamente; falha entre as
duas pode deixar extração persistida sem avaliação. A interface não declara
sucesso nessa situação; atualizar, inspecionar histórico e reenviar o mesmo
envelope para recuperar. Parsing malsucedido também recebe avaliação.
Sem IA ou aprovação manual. Nenhuma alteração nas regras de domínio F4.

`python -m scripts.local_app --database ilc_f2p02b_test` é o lançador suportado.
Força bind 127.0.0.1, porta 8501, limite 1 MiB e oculta detalhes internos.
O banco é explicitamente escolhido; `scripts.migration_config.test_engine`
continua exigindo o `.env` local, host 127.0.0.1, porta 55432 e usuário ilc_app.
Não cria, migra, semeia nem limpa bancos ao abrir a aplicação.
Dados sintéticos são confirmados pelo usuário a cada upload.
Configuração `.streamlit/config.toml` reforça os mesmos limites e desliga telemetria.

## Dependências e fontes oficiais

Consultadas antes da decisão:
- https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- https://docs.streamlit.io/develop/api-reference/configuration/config.toml
- https://pypi.org/project/streamlit/1.66.1/

Streamlit 1.66.1: Python >=3.11; metadados incluem 3.13 usado por João;
Apache-2.0. Selecionado após conflito resolvido de versão anterior com packaging.
`requirements.lock` e `requirements.in` da baseline permanecem intactos.
`requirements-app.in` + `requirements-app.lock` acrescentam UI com hashes;
`requirements-app-constraints.txt` extrai os pins da baseline, sem diretivas
hash, para resolução adicional. Não atualizar esses pins silenciosamente.
Instalar ambos os locks, evitando dependências flutuantes.
Ambiente do assistente é Python 3.12; não constitui teste Windows/Python 3.13.

## Testes automatizados e seus limites

`python -m pytest -q tests/application tests/documents`
`python -m ruff check app src/application scripts/local_app.py tests/application`

Os testes de aplicação usam doubles e Streamlit AppTest. Verificam filtros,
estados independentes, validação antes de escrita, fronteira de tamanho,
caminho controlado, chamadas aos serviços F4, erro de banco compreensível sem
segredo e atualização que consulta novamente. Não equivalem a PostgreSQL,
upload via navegador, capturas ou prova de histórico persistido.
Resultado final em ambiente virtual novo: Streamlit **1.66.1**, SQLAlchemy
**2.0.55**, Python **3.12.14**. Instalação conjunta dos dois locks com hashes
concluída; `pip check`: **No broken requirements found**. Pins compartilhados
entre lock base e app conferidos, sem alteração. Ruff e `git diff --check` aprovados.

Regressão offline: `python -m pytest -q tests/application tests/documents
tests/unit tests/ai`: **199 aprovados, 11 subtestes aprovados**, 5,86 s.
São 18 casos novos da aplicação dentro do total; não somar novamente suítes
anteriores. Um aviso de depreciação do TestClient FastAPI/httpx foi emitido,
sem falha; nenhuma troca de dependência de domínio foi feita para silenciá-lo.

Smoke do lançador real: `GET http://127.0.0.1:8501/_stcore/health` respondeu
**200 ok**; processo encerrado após a prova. Não constitui navegação ou acesso
bem-sucedido ao banco. Nenhum `.env` do Windows foi lido ou alterado, nenhum banco
foi carregado/modificado pelo assistente nesta preparação.

A primeira regressão na versão nova revelou caminho relativo incompatível no
AppTest; corrigido para absoluto, repetida com sucesso no ambiente limpo.
A instalação exploratória anterior foi descartada como evidência de compatibilidade.


## Prática reservada de João

João implementará o filtro de conclusão contestada: acrescentar opção
`CONTESTED` ao filtro físico da tela e ajustar a condição em
`filter_deliveries` para selecionar `completion_contested == True` nessa opção,
preservando DELIVERED, NOT_CONFIRMED e filtro documental. Assistente orienta e
prepara teste; alteração central e execução devem ser de João. Esse filtro
adicional ainda não foi implementado. Explicação independente permanece adiada.

## Jornada local e matriz esperado × observado

Preservar todas as evidências anteriores. Usar entregas sintéticas já existentes
na base de teste; não executar verificadores de semeadura automaticamente.
Identificar entrega concluída, quantidade/unidade esperadas e minuto de conclusão
na tela antes de criar comprovantes. Exemplos XML/PDF e envelope em
`tests/fixtures/documents/`; conferir delivery_id e conteúdo declarado antes de usar.
Novos IDs `F5-P01-*` evitam conflito acidental com ensaios anteriores.

| Aceite | Entrada / ação | Esperado | Observado |
|---|---|---|---|
| 1 | Buscar ENT-001; combinar filtros | Uma entrega, sem multiplicar por eventos/documentos | Teste controlado; PostgreSQL/navegador pendentes |
| 2 | Concluída sem documento vigente | DELIVERED e SEM_DOCUMENTO, separadamente | Teste controlado; caso real pendente |
| 3 | XML/PDF consistente e quantidade divergente | APPROVED ou REVIEW_REQUIRED com motivos, versões/avaliações persistidas | Pendente jornada real |
| 4 | Vazio, XML/PDF malformado, extensão inválida, >1 MiB | Mensagem visível; parsing falho rastreável quando aceito no fluxo | Validação/doubles testados; navegador pendente |
| 5 | Reenvio idêntico; v2 nova com predecessor vigente | Mesmo document_key no reenvio; novas tentativas/avaliações; substituição sem apagar anterior | Pendente PostgreSQL/navegador |
| 6 | Mudança no banco e Atualizar; banco indisponível | Mudança consultada; erro visível sem lista vazia/sucesso fictício | AppTest controlado; banco real pendente |
| 7 | Jornada de João e capturas | Tela, filtros, resultado, motivos, histórico e falha | Pendente |

Cada captura deve acompanhar IDs, entrada, esperado, observado, comando,
consulta persistida quando aplicável e commit do ensaio. Não fotografar segredos.
Consulta de conferência pode usar tabelas de detalhes da própria tela, atualizadas
após processamento, e consulta SQL independente de versões/avaliações por ID.

## Comandos Windows (após conferir Git e preservar alterações)

```powershell
git status --short --branch
git log -1 --oneline
git fetch origin
# Se ainda não existir branch local, após conferir alterações:
git switch --track origin/feat/f5-p01-local-app
python -m pip install --require-hashes -r requirements.lock -r requirements-app.lock
python -m pip check
python -m pytest -q tests/application tests/documents
python -m scripts.local_app --database ilc_f2p02b_test
```

Abrir http://127.0.0.1:8501. Não copiar credenciais ao chat. Não usar banco
operacional; `.env` permanece local. Não alterar portas/usuário para contornar
as verificações. Se configuração não corresponder, diagnosticar antes da escrita.

## Limites e próxima passagem

Lista reutiliza regularidade por entrega: custo proporcional ao volume, sem
alegar desempenho de produção. Consultas individuais usam snapshots F4; a lista
inteira não promete snapshot global sob concorrência. Paginação/otimização futura
requer medição e novo cartão. Recebimento não significa aprovação; ausência de
evento não prova ausência de entrega física. Conclusão contestada fica visível.

Sem serviço externo, métricas M1–M4, Power BI, revisão manual, IA, merge ou avanço
para camada analítica. Sem aprendizagem humana inventada ou aceites criados.
Próximo passo: João sincroniza sem descartar alterações, implementa a ligação
central orientada, inicia e executa a jornada. Depois registrar esperado ×
observado, capturas, commit e aprendizagem; devolver ao gerente. Somente gerente
aceita e libera outro cartão. Não houve envio automático a outros chats.
