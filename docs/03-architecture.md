# 03 — Arquitetura proposta

Estado: proposta, ainda sem implementação ou dimensionamento validado.

## Fluxo

- CSV sintético de pedidos e API REST local de eventos → ingestão Python.
- PDF textual/XML sintético → recebimento, extração e validação.
- Persistência PostgreSQL → consultas operacionais e modelos analíticos.
- Streamlit → consulta e conferência.
- Power BI Desktop → indicadores.
- Agendador do Windows → execução periódica com histórico.

O caminho síncrono de upload na aplicação e o pipeline agendado devem reutilizar regras de negócio. A interface não deve duplicar regras SQL/Python.

## Responsabilidades dos dados

| Área lógica proposta | Responsabilidade |
|---|---|
| Origem preservada | Conteúdo recebido, checksum, fonte e horário de ingestão |
| Staging | Tipagem, validação e identificação de rejeições |
| Operacional | Pedidos, eventos, documentos e resultados de conferência |
| Analytics | Granularidade e métricas publicadas com regras únicas |
| Auditoria | Execuções, contagens, falhas e rastreabilidade |

A estrutura física de schemas, tabelas e arquivos será definida no exercício de modelagem. Não pressupor que todas as camadas precisem de cópias integrais.

## Decisões iniciais

| Decisão | Justificativa | Limite / revisão |
|---|---|---|
| Python + PostgreSQL | Aderência à vaga e integridade relacional | Não demonstra processamento distribuído |
| Streamlit | Priorizar o fluxo operacional no prazo | Não equivale a aplicação pronta para produção |
| FastAPI local | Controlar cenários de parceiro e falhas | API simulada, não integração externa real |
| Windows Scheduler | Agendamento simples no equipamento do autor | Sem a infraestrutura de um orquestrador distribuído |
| Execução local | Evitar serviços cobrados | Computador precisa estar disponível |
| LLM opcional local | Investigar IA sem API paga | Sujeito a licença, recursos e avaliação |
| Databricks fora do núcleo | Concentrar a entrega nos requisitos Python/SQL | Reavaliar apenas após concluir o fluxo |

## Confiabilidade a projetar

- Identificadores estáveis de negócio e restrições de unicidade.
- Timestamp do evento separado do timestamp de ingestão.
- Deduplicação de eventos pela identidade, não apenas por data.
- Eventos atrasados sem regressão indevida do estado.
- Transações para impedir publicação parcial.
- Referências inválidas em quarentena com motivo recuperável.
- Retries limitados apenas para falhas transitórias; respeitar idempotência.
- Arquivos repetidos identificados; checksum não substitui regra de identidade do negócio.
- Horários UTC na persistência e fuso explícito na exibição.
- Metadados de atualização visíveis, evitando confundir dado antigo com situação atual.

## Limites de segurança

Somente dados sintéticos. Credenciais via configuração externa ao Git; exemplo sem valores reais. Arquivos recebidos com tamanho/tipo permitidos e XML sem resolução de entidades externas. Textos de documentos são dados não confiáveis para o LLM: instruções embutidas não devem alterar o contrato de extração. Detalhar controles conforme a implementação.

## Fontes para consultar durante a construção

- https://docs.python.org/3/
- https://www.postgresql.org/docs/
- https://docs.streamlit.io/
- https://fastapi.tiangolo.com/
- https://docs.ollama.com/
- https://learn.microsoft.com/power-bi/

Versões e compatibilidade serão verificadas antes da instalação. Nenhum serviço em nuvem ou API paga é obrigatório.

## Consolidação F1-P04

O modelo conceitual/lógico foi definido no documento 07.
A estrutura física, migrações e mecanismos de restrição pertencem à F2;
não foram implementados.

Origem preservada inclui ocorrência, recebimento original,
chegadas posteriores, tentativas e ingestão como horários distintos.
Reenvio idêntico não duplica; conflito não sobrescreve.

A proposta de fatos, dimensões e relações está no documento 08.
Sua implementação pertence à F5.
A avaliação formal de IA pertence à F4.
