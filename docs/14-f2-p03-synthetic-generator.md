# F2-P03 - Gerador sintetico e fixtures reproduziveis

Data: 19/10/2026. Branch: feat/f2-p03-synthetic-generator.
Entrada autorizada: 35dd157dcb44932eebf948cc85cd4c2ba98b064a.
Contratos 06 e fixtures A/B/C de 06/07 nessa entrada.
Estado: pratica orientada e reproducao local no Windows comprovadas;
codigo final a publicar, validacao central pendente. Evidencias na secao 10.
F2 aberta, R03 parcial, R04 nao validado e F3-F6 bloqueadas.
Nao representa consolidacao da F2 nem integracao com main.

## 1. Base observada no Windows de Joao

HEAD 35dd157, branch feat/f2-p03-synthetic-generator criada.
Python 3.13.14 na .venv: PASS. Apenas .vscode nao rastreada.
Nenhum comando de banco foi solicitado ou executado neste cartao.
Dependencias existentes mantidas; nenhuma instalacao nova necessaria.
O gerador e o verificador usam apenas biblioteca padrao do Python.

## 2. Escopo e formatos

scripts/synthetic_generator.py produz arquivos, sem imports ou conexao de banco.
Config(seed, volume): seed inteiro de 0 a 2**63-1; volume significa numero
de entregas consistentes adicionais, entre 0 e 10000. Sempre ha oito
entregas das fixtures basicas. Default: seed=20261019, volume=0.
O teto e uma protecao de escopo/memoria; desempenho no volume maximo nao
foi demonstrado. O gerador monta bytes em memoria antes da escrita.

Saida CLI restrita a um novo subdiretorio de data/generated/ no repositorio.
Destino existente causa falha, sem mesclar, apagar ou sobrescrever arquivos.
Falha de escrita pode deixar diretorio parcial: revisar e escolher outro
destino, sem instruir limpeza automatica ou sobrescrita.
Pastas volumosas geradas ficam ignoradas no Git por /data/generated/.
Nao altera .env, migracoes, banco ou instalacoes de outros projetos.

| Caminho | Conteudo |
|---|---|
| reference/orders.jsonl | Pedidos sinteticos de referencia |
| reference/deliveries.jsonl | Entregas, quantidade/unidade esperadas e prazo de referencia |
| valid/events.jsonl | Eventos com estrutura e vinculos coerentes |
| valid/document_envelopes.jsonl | Envelopes de familias/versoes documentais |
| replays/ | Payloads identicos para futuras verificacoes de idempotencia |
| anomalies/ | Alternativas bem formadas com identidade repetida e conteudo diferente |
| invalid/ | Negativos estruturais, separados dos casos validos |
| synthetic_documents/ | Referencias JSON sinteticas, nunca PDF/XML real |
| document_references.jsonl | Mapeamento envelope/arquivo sintetico, tamanho e SHA256 dos bytes JSON |
| arrival_plan.jsonl | Ordem planejada de chegadas, horarios e ponteiros para payloads |
| manifest.json | Configuracao, contagens, inventario e resultados esperados por cenario |
| SHA256SUMS | Hash de todos os arquivos, incluindo manifesto, exceto o proprio SHA256SUMS |

Os layouts de pedidos/entregas sao adaptadores educacionais derivados do
modelo 07; nao se afirma contrato externo de API aprovado para esses arquivos.
Um pedido referencia sua origem; cada entrega aponta para o pedido e tem
delivery_id globalmente unico no conjunto.

Payloads de evento/envelope usam os campos de recebimento do contrato,
sem acrescentar metadados de execucao ou resultados ficticios. Horarios de
chegada ficam no plano externo, separados de occurred_at.
O plano nao comprova ingestao ou ordem efetiva de aceitacao no banco.

### Referencias documentais

Cada .synthetic.json declara is_real_pdf_or_xml=false e contem campos
declarados para a fixture futura, nao resultados extraidos de um parser.
O media_type do envelope descreve o formato documental pretendido para F4;
os bytes atuais sao JSON, nao application/pdf. Nao enviar esses arquivos
como se fossem PDFs reais nem considera-los documentos aceitos.
file_sha256 nao e inventado no envelope: esse metadado de arquivo real
somente sera calculado na etapa autorizada com bytes reais de PDF/XML.
O hash em document_references.jsonl verifica apenas o JSON sintetico atual.
Reenvio documental reutiliza exatamente o mesmo envelope e a mesma referencia.
Conflito documental reutiliza a identidade/envelope, com referencia alternativa
de bytes diferentes, sem sobrescrever a original.

## 3. Cobertura e expectativas futuras

Todas as expectativas do manifesto usam EXPECTED_NOT_EXECUTED.
Nao se executam aprovacao, deduplicacao, substituicao no banco ou resolucao.

| Caso | Entrada sintetica | Resultado futuro esperado, nao executado |
|---|---|---|
| A | ENT-001; EVT-001/002/003; DOC-A1 e DOC-B1 em familias distintas | Tres eventos/dois comprovantes continuam uma entrega; quantidade 10 consistente e 9 divergente |
| B | ENT-002; DOC-C1 v1=9; DOC-C2 v2=10; reenvio identico | Cadeia preservada; nova versao exige avaliacao propria; recebimentos 17:10/17:30/17:40Z distintos |
| C_AB | ENT-003; conclusoes A 17:00Z e B 17:10Z, chegada A antes de B | Preservar primeira aceita provisoria e conflito aberto |
| C_BA | ENT-004; mesmas alternativas, chegada B antes de A | Preservar B provisoriamente; nao escolher minimo/ultimo ocorrido automaticamente |
| CONSISTENT | ENT-005; evento, campos declarados coerentes e reenvio do evento | Consistencia futura; reenvio nao deve duplicar evento |
| NO_DOCUMENT | ENT-006; evento DELIVERED sem envelope | Ausencia documental explicita, sem documento ficticio |
| IDENTITY_CONFLICT | ENT-007; mesmo event_id com horario diferente e mesmo document_id com bytes sinteticos diferentes | Original e alternativa preservados; conflito sem sobrescrita |
| LATE_EVENT | ENT-008; IN_TRANSIT anterior chega depois de DELIVERED | Historico sem regressao fisica automatica |
| INVALID_* | Tipo FINISHED, horario sem fuso, referencia obrigatoria ausente, envelope sem media_type, v2 sem antecessora | Rejeicao estrutural; nao muda versao valida |
| BULK_CONSISTENT | Volume adicional configurado | Cada referencia possui evento e envelope coerentes |

Casos A/B conservam IDs, quantidades e horarios centrais de 06.
C usa duas entregas independentes para representar as duas ordens possiveis.
"Valido" designa estrutura/vinculo: divergencia de quantidade ou conclusoes
ambiguas continuam sendo anomalias de negocio deliberadas e identificadas.
"Invalid" designa violacao estrutural introduzida para teste negativo.

## 4. Reprodutibilidade e manifesto

Data-base fixa 2026-10-16T00:00:00Z. Nenhum datetime.now, uuid4, os.urandom,
random global, variavel de banco ou caminho absoluto participa dos bytes.
A semente influencia notas/identificacao sintetica e quantidades adicionais
por SHA256(seed/indice), sem depender do algoritmo random de outra versao.
IDs das fixtures permanecem legiveis; nao sao UUIDs aleatorios.
UTF-8, chaves JSON ordenadas, separadores fixos e LF escritos em binario.
.gitattributes fixa LF para as fixtures pequenas tambem no checkout Windows.
Arquivos vazios de fluxos sem registros continuam no inventario.

Manifesto exclui seu proprio hash para evitar autorreferencia; SHA256SUMS
inclui o manifesto e exclui apenas a si mesmo. Comparacao entre diretorios
exige os mesmos caminhos, bytes e hashes, inclusive manifesto e SHA256SUMS.
Contagens sao de entradas geradas, nao de registros aceitos em banco.
Reenvios e alternativas nao sao contabilizados como novas identidades validas.

scripts/check_synthetic_dataset.py verifica inventario exato, tamanhos,
hashes e contagens, e --compare exige igualdade de todos os bytes.
Recusa links simbolicos e arquivos extras/ausentes/alterados.
Nao implementa parser documental ou conferencia funcional.

### Fixture pequena versionada (seed 20261019, volume adicional zero)

| Conteudo | Quantidade |
|---|---|
| Pedidos / entregas de referencia | 8 / 8 |
| Eventos validos / envelopes validos | 13 / 6 |
| Reenvios de evento / envelope | 1 / 1 |
| Alternativas de identidade de evento / envelope | 1 / 1 |
| Eventos / envelopes estruturalmente invalidos | 3 / 2 |
| Chegadas planejadas | 28 |
| Referencias documentais, incluindo reenvio | 8 |
| Arquivos JSON documentais sinteticos distintos | 7 |
| Arquivos totais do dataset | 21 |

Fixture em tests/fixtures/synthetic/v1/. README explicativo fica fora de v1.
SHA256 de SHA256SUMS da referencia:

    5e2d363aabb33506cbae02252037b32f742c08ebc3d43718f31b4ce8e27d7e50

## 5. Pratica central de Joao

No arquivo scripts/synthetic_generator.py, funcao divergent_quantity,
o scaffold publicado contem NotImplementedError. Joao deve substituir o
corpo por uma regra que:

1. Exija inteiro positivo, recusando bool, zero, negativo, decimal e texto.
2. Produza expected - 1; 10 gera 9 e 1 gera 0, sem quantidade negativa.

Essa regra cria a divergencia deliberada das fixtures A/B e da alternativa
documental de identidade. Deve manter os valores aprovados nos contratos.
Nao mudar a chamada nem relaxar os testes para contornar o bloqueio.
O gerador e os testes ficam bloqueados ate essa edicao orientada.
Depois, Joao executara Ruff, pytest e duas geracoes, interpretando contagens
e hashes. Nao atribuir ao usuario explicacoes elaboradas pelo assistente.

## 6. Testes e verificacoes da preparacao

24 testes unitarios preparados em tests/unit/test_synthetic_generator.py,
executaveis por pytest existente ou unittest da biblioteca padrao.
Verificam determinismo, seeds diferentes, volume adicional, contratos de
payload, vinculos de pedido/entrega/versao, fixtures A/B/C, anomalias e
negativos, horarios de chegada, inventario/hashes, LF, ausencia de importacao
de banco, invariancia ao PYTHONHASHSEED e recusa de sobrescrita/destino externo.
O verificador e exercitado com alteracao, arquivo extra e arquivo ausente.
Teste compara a geracao com todos os bytes da fixture pequena versionada.

Para preparar e verificar as fixtures, o assistente executou uma versao de
referencia com divergent_quantity ja completa, antes de substituir somente
essa funcao pelo bloqueio de pratica no scaffold publicado.
Na referencia, ambiente Linux/Python 3.12.14 do assistente:

- unittest final: Ran 24 tests in 0.131s, OK.
- Duas geracoes CLI com seed=20261019, volume=25: PASS.
- Ambas: 33 entregas, 46 arquivos, 38 eventos validos, 31 envelopes validos,
  78 chegadas planejadas, 33 referencias documentais.
- Verificador --compare: Same files, bytes and hashes: PASS.
- SHA256 de SHA256SUMS das duas geracoes de referencia:

      0bfc266949ab9488a357ef67a03a3f12a4b6dc46cdd6caa1969bca27d67f9a2c

As evidencias acima nao provam execucao de Joao nem do scaffold bloqueado.
Ruff/pytest nao disponiveis no ambiente do assistente: nao foram executados
aqui. A verificacao posterior no Windows/Python 3.13.14 esta na secao 10.
Nao executada regressao de banco neste cartao: codigo de migracao nao mudou.

## 7. Comandos previstos, ainda nao observados no Windows

Depois da pratica central e Ruff aprovado:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_synthetic_generator.py
.\.venv\Scripts\python.exe -m scripts.synthetic_generator --seed 20261019 --volume 25 --output data/generated/f2p03-a
.\.venv\Scripts\python.exe -m scripts.synthetic_generator --seed 20261019 --volume 25 --output data/generated/f2p03-b
.\.venv\Scripts\python.exe -m scripts.check_synthetic_dataset data/generated/f2p03-a --compare data/generated/f2p03-b
.\.venv\Scripts\python.exe -m scripts.check_synthetic_dataset tests/fixtures/synthetic/v1
git check-ignore data/generated/f2p03-a/manifest.json
```

Parar em falha. Nao sobrescrever diretorios de geracoes anteriores.
Resultados esperados sao insumos para fases seguintes, nao comportamento
de ingestao ou aprovacao comprovado por estes comandos.

## 8. Fontes oficiais consultadas antes da preparacao

Consultadas em 19/10/2026 para biblioteca padrao Python 3.13:
- https://docs.python.org/3.13/library/hashlib.html
- https://docs.python.org/3.13/library/json.html
- https://docs.python.org/3.13/library/datetime.html

APIs utilizadas tambem foram exercitadas na referencia Python 3.12.14.
Isso complementa, sem substituir, a verificacao no ambiente aceito de Joao.
Nenhum pacote ou versao do lock foi alterado por causa deste cartao.

## 9. Pendencias e passagem

Publicar o codigo final editado/formatado e retornar ao gerente. Pratica
orientada e execucao comprovadas; interpretacao independente nao verificada.
F2-P03 e R04 dependem da validacao central.
Sem ingestao, API, parser, conferencia funcional ou metricas implementadas.
Integracao com main e consolidacao final da F2 permanecem pendentes.


## 10. Execucao observada no Windows de Joao - 19/10/2026

### Configuracao, qualidade e reproducao

- Base 35dd157 e branch feat/f2-p03-synthetic-generator confirmadas.
- Python 3.13.14 dentro da .venv: PASS.
- Joao editou divergent_quantity conforme a regra orientada pelo assistente.
- Ruff: All checks passed! apos organizacao/formatacao.
- pytest: 24 passed, 11 subtests passed in 0.73s.
  Sao 24 testes principais; subtestes nao sao contados como outros 11 testes principais.
- Duas geracoes com seed=20261019 e volume adicional=25:
  data/generated/f2p03-a e data/generated/f2p03-b, ambas PASS.
- Comparacao independente de inventario, contagens, hashes e todos os bytes:
  Same files, bytes and hashes: PASS.
- Verificacao da fixture pequena tests/fixtures/synthetic/v1: PASS.
- git check-ignore confirmou os manifestos dos dois conjuntos gerados:
  ambos fora do rastreamento. .vscode permanece nao rastreada.

| Item por conjunto | Esperado | Observado |
|---|---|---|
| Pedidos / entregas | 33 / 33 | 33 / 33 |
| Eventos validos / envelopes validos | 38 / 31 | 38 / 31 |
| Reenvios de evento / envelope | 1 / 1 | 1 / 1 |
| Alternativas de evento / envelope | 1 / 1 | 1 / 1 |
| Eventos / envelopes invalidos | 3 / 2 | 3 / 2 |
| Chegadas planejadas | 78 | 78 |
| Referencias documentais | 33 | 33 |
| Arquivos totais | 46 | 46 |

SHA256 de SHA256SUMS identico nas duas geracoes Windows:

    0bfc266949ab9488a357ef67a03a3f12a4b6dc46cdd6caa1969bca27d67f9a2c

SHA256 de SHA256SUMS da fixture pequena, verificado no Windows:

    5e2d363aabb33506cbae02252037b32f742c08ebc3d43718f31b4ce8e27d7e50

Os dois valores tambem coincidem com a referencia preparada pelo assistente
no Linux/Python 3.12.14 para essas mesmas configuracoes. Isso e evidencia
pontual entre os dois ambientes; nao garante todos os sistemas/versoes.

### Explicacoes de referencia do assistente

33 entregas significam oito referencias das fixtures e 25 adicionais.
Contagens de entradas nao sao contagens de registros aceitos: reenvios,
alternativas e invalidos permanecem separados e identificados.
A igualdade verificada abrange caminhos e todos os bytes, alem dos hashes;
indica reproducao para a configuracao e versao de codigo verificadas.
Os resultados EXPECTED_NOT_EXECUTED no manifesto continuam expectativas
para o pipeline futuro. Nao foram executadas aprovacao, deduplicacao,
ingestao, resolucao de conflitos ou metricas.

Joao executou edicao orientada, qualidade, duas geracoes e verificacoes.
Assistente preparou codigo, fixtures, testes, comandos e explicacoes.
Interpretacao independente de Joao nao foi recebida/verificada; nao atribuir
as explicacoes acima ao usuario como resposta autoral.

### Estado da publicacao e limites

Alteracoes locais observadas: scripts/synthetic_generator.py e
tests/unit/test_synthetic_generator.py; commit final sera identificado na passagem.
O scaffold inicial dd257dd possuia bloqueio de pratica; a execucao Windows
foi feita depois da edicao orientada, nao com o scaffold bloqueado.

Sem conexao/escrita no banco, API, parser, conferencia funcional ou metricas.
Documentos continuam referencias JSON sinteticas, sem PDF/XML real.
Volume maximo de 10000 nao ensaiado; geracoes nao sobrescrevem diretorios.
F2 aberta, R03 parcial, R04 aguardando validacao; F3-F6 bloqueadas.
Integracao com main e consolidacao da F2 permanecem pendentes.
