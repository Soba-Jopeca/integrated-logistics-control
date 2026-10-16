# 06 — Contratos de evento e documento

Versão: 0.1 — proposta para validação central.
Data: 16/10/2026.
Passo: F1-P02.
Base técnica informada: branch docs/data-contracts,
commit 161a874678159055b3a6e347c84664ca958667f4.

Documento conceitual. Não comprova implementação ou testes de software.
Case educacional com dados sintéticos.

## 1. Convenções comuns

- schema_version: texto obrigatório, valor "1.0".
- Identificadores: texto não vazio, sem espaços nas extremidades;
  comparação sensível a maiúsculas.
- Datas: ISO 8601 com fuso obrigatório; normalização para UTC;
  exibição em America/Sao_Paulo.
- Campos desconhecidos são rejeitados nesta versão.
- Campos obrigatórios não aceitam ausência, null ou texto vazio.
- Campos opcionais aceitam ausência ou null.
- Identidade de origem: source_system + identificador.
- Recebimento e ingestão são distintos do acontecimento de negócio.
- received_at, ingested_at e run_id são registrados pelo sistema.
- A entrada original é preservada com referência e checksum.
- Metadados de execução não alteram a identidade de negócio.

### Reenvio e conflito

Mesma identidade e conteúdo de negócio normalizado:
reenvio sem duplicação, com tentativa rastreável.

Mesma identidade e conteúdo diferente:
conflito explícito; preservar original e entrada conflitante,
sem sobrescrita silenciosa.

A comparação ignora a ordem das propriedades JSON, normaliza datas
para UTC e trata ausência e null como equivalentes nos opcionais.
Não ignora diferenças de valores ou de conteúdo de arquivos.

## 2. Evento

### Grão e vínculos

Um evento representa um acontecimento informado por uma origem
sobre uma entrega.

Cada evento referencia uma entrega.
Uma entrega admite zero ou vários eventos.
Na v1, um pedido corresponde a uma entrega.

### Campos recebidos

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| schema_version | texto | Sim | "1.0" |
| source_system | texto | Sim | Origem identificada |
| event_id | texto | Sim | Identidade estável na origem |
| delivery_id | texto | Sim | Referência da entrega |
| event_type | enum | Sim | DISPATCHED, IN_TRANSIT, DELIVERED |
| occurred_at | data/hora com fuso | Sim | Horário do acontecimento |
| notes | texto | Não | Conteúdo informativo não confiável |

Identidade: (source_system, event_id).

Metadados do sistema: received_at, ingested_at, run_id,
referência à entrada original e checksum.

Uma referência ainda não encontrada produz rejeição recuperável.
Não se cria uma entrega fictícia para satisfazer o vínculo.

### Situação física e transições

- Sem evento elegível: NOT_CONFIRMED.
- Sequência normal: DISPATCHED → IN_TRANSIT → DELIVERED.
- Etapas intermediárias podem estar ausentes.
- DELIVERED pode confirmar a conclusão mesmo sem eventos anteriores.
- A ordem de recebimento não determina a ordem de ocorrência.
- Evento anterior recebido com atraso entra no histórico sem regressão.
- Eventos de tipos diferentes no mesmo occurred_at exigem revisão;
  preservar a última situação inequívoca ou NOT_CONFIRMED se inexistente.
- Evento incompatível ocorrido após DELIVERED exige revisão e não
  desfaz automaticamente a conclusão.
- Correção/cancelamento de conclusão não possui fluxo automático na v0.1.
  O caso permanece sinalizado até decisão explícita e auditável.

NOT_CONFIRMED significa falta de confirmação nos dados disponíveis;
não significa que a entrega não ocorreu.

### Exemplo válido

    {
      "schema_version": "1.0",
      "source_system": "mock_transport",
      "event_id": "EVT-003",
      "delivery_id": "ENT-001",
      "event_type": "DELIVERED",
      "occurred_at": "2026-10-16T14:00:00-03:00",
      "notes": null
    }

### Exemplos e resultados esperados

| Entrada | Resultado esperado |
|---|---|
| EVT-003 idêntico novamente | Reenvio; um evento de negócio |
| EVT-003 com outro horário | Conflito; original preservado |
| Data sem fuso | Entrada inválida |
| event_type FINISHED | Entrada inválida |
| delivery_id desconhecido | Rejeição recuperável |
| IN_TRANSIT anterior recebido após DELIVERED | Histórico atualizado; sem regressão |

## 3. Documento

### Grão e vínculos

Um registro representa uma versão imutável de um comprovante.

Uma entrega admite zero ou vários comprovantes.
Uma família identifica um comprovante ao longo de suas versões.
Cada versão declara uma entrega.
A vinculação confirmada só existe após resolver a referência.

### Campos do envelope de recebimento

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| schema_version | texto | Sim | "1.0" |
| source_system | texto | Sim | Origem identificada |
| document_id | texto | Sim | Identidade da versão |
| document_family_id | texto | Sim | Identidade do comprovante |
| version | inteiro | Sim | Começa em 1; incrementa sem saltos |
| supersedes_document_id | texto | Condicional | Null na v1; obrigatório nas seguintes |
| delivery_id | texto | Sim | Entrega declarada no recebimento |
| media_type | enum | Sim | application/pdf ou application/xml |
| file_sha256 | texto | Gerado pelo sistema | Obrigatório no registro aceito; 64 caracteres hexadecimais minúsculos |

O checksum é calculado pelo sistema sobre os bytes recebidos.
Se informado pela origem, deve coincidir com o calculado.

Identidade: (source_system, document_id).
Unicidade adicional:
(source_system, document_family_id, version).

Metadados do sistema: received_at, ingested_at, run_id,
tamanho e referência ao arquivo preservado.

O nome original não determina o caminho de armazenamento.
Conteúdo de documento é dado não confiável, nunca instrução executável.
XML é educacional, sem alegação de conformidade fiscal.
XML com entidades externas não é aceito.

Mesmo hash com outro identificador sinaliza possível duplicação;
não implica fusão automática de comprovantes.

### Campos extraídos para conferência

| Campo | Tipo | Exigência para aprovação |
|---|---|---|
| declared_delivery_id | texto ou null | Igual à entrega vinculada |
| delivered_at | data/hora com fuso ou null | Mesmo minuto UTC da conclusão efetiva |
| received_quantity | inteiro ou null | Não negativo e igual à quantidade esperada |
| quantity_unit | texto ou null | Igual à unidade esperada |
| receiver_name | texto ou null | Nome sintético não vazio |

Campos ausentes permanecem null.
Não preencher por suposição ou por inferência da IA.

A comparação temporal descarta segundos e frações após normalização
para UTC. Não há tolerância adicional entre minutos.
Essa é uma premissa educacional, não uma regra empresarial validada.

A quantidade refere-se ao total entregue na mesma unidade do esperado.
Entregas parciais e conversões entre unidades ficam fora da v0.1.

Os valores esperados pertencem à referência da entrega.
Sua estrutura será definida no passo de modelagem, após liberação.

### Processamento e avaliação

Processamento:
RECEIVED → EXTRACTED ou PARSING_FAILED.

Reprocessamento pode recuperar PARSING_FAILED.
Cada tentativa permanece rastreável.

Avaliação:
NOT_EVALUATED → APPROVED ou REVIEW_REQUIRED.

Uma nova avaliação não sobrescreve a anterior.
Registrar identidade da avaliação, documento, versão das regras,
horário, resultado e motivos.

Se houver revisão manual, preservar também autor, motivo e
referência à avaliação anterior.

### Motivos distintos

| Motivo | Significado |
|---|---|
| MISSING_REQUIRED_FIELD | Campo exigido ausente |
| INVALID_REFERENCE | Referência ainda não resolvida |
| REFERENCE_MISMATCH | Referência extraída difere da vinculada |
| VALUE_MISMATCH | Valor extraído difere do esperado |
| PARSING_ERROR | Falha na extração |
| DELIVERY_NOT_CONFIRMED | Falta conclusão elegível para comparação |
| IDENTITY_CONFLICT | Mesma identidade com conteúdo diferente |

INVALID_REFERENCE pode ser recuperado quando os dados de referência
chegarem. Não significa inexistência definitiva da entrega.

APPROVED exige todos os campos obrigatórios presentes e consistentes,
referência resolvida e ausência de bloqueadores.

Recebimento ou extração não implica aprovação.
A IA não autoriza aprovação.

### Substituição e histórico

- A versão inicial tem version = 1 e supersedes_document_id = null.
- A seguinte aponta para a versão vigente anterior da mesma origem,
  família e entrega, com version incrementada em 1.
- Não são permitidos saltos, ciclos ou ramificações.
- Substituição fora de ordem fica pendente de recuperação.
- A vigência muda somente após aceitação estrutural do envelope,
  arquivo, identidade e cadeia de substituição.
- Uma substituição estruturalmente inválida não retira a vigência anterior.
- Aceitação estrutural não significa aprovação documental.
- A nova versão começa sem aprovação e exige conferência própria.
- Falha de parsing ou divergência na nova versão vigente gera pendência;
  não restaura silenciosamente a aprovação da versão antiga.
- Versões anteriores e suas avaliações permanecem no histórico.

Correção da entrega declarada não ocorre por substituição entre famílias
ou entregas diferentes. O vínculo incorreto exige tratamento explícito,
preservando o histórico.

### Regularidade da entrega

Regularidade documental exige:

1. Pelo menos um comprovante vigente aprovado.
2. Nenhum comprovante vigente vinculado com pendência de processamento,
   avaliação ou conflito não resolvido.

Comprovantes substituídos não bloqueiam a situação atual.
Documento sem vínculo resolvido fica em pendência própria e não é
atribuído por suposição a uma entrega.

Ausência documental é condição da entrega; não cria documento fictício.
Conclusão física e regularidade documental são independentes.

### Exemplo válido de envelope inicial

    {
      "schema_version": "1.0",
      "source_system": "mock_documents",
      "document_id": "DOC-001",
      "document_family_id": "POD-001",
      "version": 1,
      "supersedes_document_id": null,
      "delivery_id": "ENT-001",
      "media_type": "application/pdf",
      "file_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }

O hash acima é ilustrativo; deve corresponder ao arquivo na execução.

### Exemplos e resultados esperados

| Entrada | Resultado esperado |
|---|---|
| Mesmo envelope e arquivo | Reenvio; sem nova versão |
| Mesmo document_id com outro arquivo | Conflito; sem sobrescrita |
| DOC-002, v2, substitui DOC-001 na mesma família/entrega | Substituição estrutural válida; nova conferência |
| v2 sem supersedes_document_id | Entrada inválida |
| v3 antes da v2 | Pendente de recuperação; não muda vigência |
| received_quantity ausente | Null; revisão por campo ausente |
| Unidade diferente da esperada | Revisão por divergência |
| Referência extraída diferente da vinculada | REFERENCE_MISMATCH |
| Arquivo não extraível | PARSING_ERROR; sem valores inventados |
| Comprovante antes do evento de conclusão | Preservar; DELIVERY_NOT_CONFIRMED até reavaliação |

## 4. Coerência com as métricas

- M1 conta entregas distintas pela conclusão efetiva.
- M2 identifica entrega concluída sem documento recebido vinculado.
  Documento divergente não equivale a documento ausente.
- M3 conta versões de documentos vigentes com avaliação atual
  REVIEW_REQUIRED; vários motivos contam o documento uma vez.
  Documentos ainda não avaliados são apresentados separadamente.
- Para M4, recebimento válido é arquivo aceito estruturalmente,
  vinculado a entrega existente e sem conflito de identidade.
  Não exige aprovação documental.
- Após resolver um vínculo tardio, usar o received_at original preservado,
  não o horário de resolução.
- M4 usa o primeiro recebimento válido, inclusive de versão posteriormente
  substituída, pois mede chegada do comprovante.
- Intervalos negativos são excluídos da mediana e contados para revisão.
- Declarar período, instante de referência, fuso, atualização e versão.
- Sem SLA documental validado, exibir tempo decorrido sem alegar violação.

## 5. Fixture conceitual ENT-001

Premissas sintéticas:
entrega ENT-001; quantidade esperada 10; unidade VOLUME.

Eventos:
- EVT-001: DISPATCHED, 16/10/2026 às 12:00Z.
- EVT-002: IN_TRANSIT, 16/10/2026 às 14:00Z.
- EVT-003: DELIVERED, 16/10/2026 às 17:00Z.

Documentos da família POD-001:
- DOC-001, v1: quantidade extraída 9; REVIEW_REQUIRED.
- DOC-002, v2, substitui DOC-001: quantidade 10, unidade VOLUME,
  referência ENT-001, conclusão 17:00Z e recebedor sintético preenchido;
  APPROVED se todos os demais critérios forem satisfeitos.

Resultado esperado:
uma entrega, três eventos e duas versões documentais históricas.
DOC-002 é vigente após substituição estrutural válida.
DOC-001 e sua divergência permanecem no histórico.
Situação física concluída; documental regular após aprovação de DOC-002.

Um cruzamento 3 × 2 pode gerar seis linhas, mas continua uma entrega.
Se houver outra família vigente divergente, a regularidade fica pendente.

Esta fixture descreve resultados esperados; não foi executada.

## 6. Decisões e participação

O assistente preparou o rascunho e a revisão.
João solicitou a adoção da alternativa recomendada e a continuidade.

Decisão adotada:
um comprovante aprovado não encobre pendência em outro vigente.

Consequência:
a entrega pode estar fisicamente concluída e documentalmente pendente;
versões substituídas preservam histórico sem bloquear a situação atual.

A justificativa foi elaborada pelo assistente.
Não há explicação autoral independente de João registrada neste passo.
A edição, revisão e execução Git por João serão registradas por evidência.

## 7. Limites e validação

- Não há modelos, tabelas, banco, ETL ou testes implementados neste passo.
- Contratos e fixture exigem validação central.
- Correção/cancelamento automático de eventos não está incluído.
- Entregas parciais, conversão de unidades e conformidade fiscal não incluídas.
- Frequência de atualização será definida no passo operacional pertinente.
- Nenhuma fase é fechada por este documento.