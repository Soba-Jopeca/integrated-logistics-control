# F5-P03A — Publicação analítica Gold da fixture

Base 36e6b15; referência SQL d6f7e6d e documento 27. O cartão autoriza
a publicação no banco de teste. P03B aguarda aceite central; F5 aberta e F6
bloqueada. O exportador CSV anterior permanece disponível para evidência.

Raw é a entrada original preservada; Bronze é a rastreabilidade de captura
e ingestão; Silver é o domínio operacional no schema ilc; Gold é analytics.
Esta prova carrega somente a fixture sintética com os fatos do P02. Não prova
carga Gold de ilc e não muda Raw, Bronze, Silver ou o aplicativo.

## Objetos e rastreabilidade

- consume_publication: uma linha por publication_id, com referência, corte,
  período, fuso, hash dos SQLs e horário da publicação.
- consume_scenarios: dimensão, uma linha por publicação e cenário.
- consume_deliveries: uma linha por publicação, cenário e delivery_key;
  vem de fact_delivery_reference e completion_cohort. Preserva delivery_id,
  conclusão, prazo, contestação, recebimento e intervalo original.
- consume_documents: uma linha por publicação, cenário e document_key
  vigente, com família e número de versão de dim_document, avaliação e
  delivery_key. Origem: fact_document_reference.
- consume_reasons: uma linha por publicação, cenário, avaliação, código e
  campo. Origem: bridge_evaluation_reason. O fato documental mantém seu grão
  antes do detalhamento. Chaves compostas impedem cruzar publicações.
- runs: trilha privada de tentativas. run_id é novo a cada execução;
  publication_id identifica conteúdo, regras e corte; corte limita o
  conjunto temporal. O erro controlado guarda o ID tentado separadamente.

A publicação é atômica e só fica visível após o commit. O hash inclui o
conteúdo ordenado, referência e SQL; exclui o horário da consulta. Repetir a
entrada reutiliza a publicação. A variante alternate muda identificadores de
entregas sintéticas na entrada dos fatos e mantém o corte e as métricas.
A variante failure insere antes de provocar falha de qualidade. A transação
é revertida e o diagnóstico é gravado em outra transação. Logs de tentativa
são privados. O snapshot fica imutável pelo fluxo de publicação; a identidade
proprietária do schema continua responsável pela administração.

## Provas no Windows

Na raiz, com venv e PostgreSQL dedicado ativos, confirmar a revisão atual
0006_reliability. Se houver configuração local modificada, preservá-la.

```powershell
python -m alembic -x database=ilc_f2p02b_test current
python -m alembic -x database=ilc_f2p02b_test upgrade 0007_gold_fixture
```

Para provar reversão **antes de inserir qualquer publicação**, executar
downgrade 0006_reliability e upgrade 0007_gold_fixture com os mesmos
argumentos. O downgrade remove exclusivamente objetos Gold e seus dados;
não aplicar sobre publicações a preservar. Depois:

```powershell
python -m scripts.publish_gold_fixture --database ilc_f2p02b_test --prove
```

O comando executa base, reuso, entrada alternativa e falha, valida métricas
no estado persistido e verifica ausência das linhas revertidas. Esperado:
18 entregas, 15 documentos e 6 motivos por publicação (três cenários);
a versão B1 tem dois motivos em cada cenário e conta uma vez em M3.
Se a publicação base ou alternativa já existir, REUSED é esperado.

| Cenário | M1 | M2 | M3 | M4 |
|---|---:|---:|---:|---:|
| BASE | 75% | 2 | 1 | 5 min |
| EMPTY | NULL | 2 | 1 | NULL |
| LATE | 0% | 2 | 1 | NULL |

## Identidade leitora

No psql do cluster dedicado, conectado ao banco de teste como DBA, criar
uma única vez o login `ilc_gold_reader`, sem memberships nem privilégios
administrativos. Usar `CREATE ROLE ilc_gold_reader LOGIN;` e
`\password ilc_gold_reader` para definir a senha sem colocá-la no comando
ou no Git. Se o login já existir, verificar seus privilégios antes de usar.
Aplicar grant_gold_reader.sql como ilc_app (dono de analytics); em seguida
executar check_gold_reader.sql **conectado como o próprio leitor**:

```powershell
$psql = 'C:\ILC-PostgreSQL\18.6\bin\psql.exe'
& $psql -h 127.0.0.1 -p 55432 -d ilc_f2p02b_test -U ilc_app -W -v ON_ERROR_STOP=1 -f analytics/sql/grant_gold_reader.sql
& $psql -h 127.0.0.1 -p 55432 -d ilc_f2p02b_test -U ilc_gold_reader -W -v ON_ERROR_STOP=1 -f analytics/sql/check_gold_reader.sql
```

O teste de privilégios cobre os schemas do case no banco de teste; catálogos
PostgreSQL não fazem parte dessa restrição. O login é administrado pelo DBA
e não é removido pelo downgrade. Sem abrir o Desktop neste cartão.

## Estado das evidências

Preparação versionada. Execução PostgreSQL, reversão e leitura com o login
real ainda aguardam João. Devolver resultados, identificadores das duas
fotografias, amostras e diagnóstico persistido. Registrar a explicação
de João sobre run_id, publication_id e corte antes do aceite central.
