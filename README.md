# Integrated Logistics Control

**Conferência documental e acompanhamento de entregas.**

Case educacional de dados e automação aplicado à logística, desenvolvido por João Pedro Caneca com orientação técnica. O objetivo é aprender a transformar necessidades operacionais em uma solução verificável com Python, SQL, integração REST, aplicação web e indicadores.

> **Estado: F1 FECHADA no escopo documental — VAL-F1-P04-001, 16/10/2026.** F2 pronta para receber o primeiro cartão do gerente, ainda não iniciada. Funcionalidades abaixo permanecem planejadas. Alvo de demonstração inicial: 21/10/2026, sujeito a reestimativa.

## Problema e valor esperado

O cenário fictício considera informações de pedidos, eventos de transporte e comprovantes em fontes distintas. Um analista precisa identificar entregas sem comprovante e divergências documentais para priorizar a regularização. A liderança precisa acompanhar essas pendências com métricas consistentes.

**Entrega concluída e documentação aprovada são estados independentes.** A solução deve preservar essa distinção.

## Demonstração planejada

1. Ingerir pedidos e consumir eventos de uma API local simulada.
2. Preservar a origem, tratar os dados e registrar a execução.
3. Extrair campos de PDF textual e XML de formato educacional.
4. Conciliar documentos com entregas e explicar divergências.
5. Consultar pendências em uma aplicação Python.
6. Apresentar uma página de indicadores no Power BI Desktop.
7. Avaliar um experimento de LLM local para ocorrências textuais, condicionado à viabilidade no equipamento.

## Tecnologias propostas

Python, PostgreSQL, SQL, Streamlit, FastAPI, Git e Power BI Desktop. Execução local; sem contratação de serviços ou dependência de créditos de nuvem. Agendamento inicial pelo Windows. OCR e LLM local dependem de avaliação; RAG fica para evolução.

## Documentação

- [Entendimento do negócio](docs/01-business-understanding.md)
- [Escopo e critérios de aceite](docs/02-scope-and-acceptance.md)
- [Arquitetura e decisões iniciais](docs/03-architecture.md)
- [Plano de execução e aprendizagem](docs/04-delivery-and-learning-plan.md)
- [Métricas e regras](docs/05-metrics-and-rules.md)
- [Fluxo de contribuição](CONTRIBUTING.md)

## Execução

Ainda não há aplicação executável, dependências fixadas ou instruções de instalação validadas. Essas instruções serão adicionadas conforme cada etapa for implementada e testada.

## Limites e transparência

Dados e documentos exclusivamente sintéticos. Não há integração com ERP/WMS reais nem representação oficial da Ever Express. O case foi motivado por requisitos profissionais, sem afirmar conhecimento da arquitetura interna de qualquer empresa.

Não há resultados operacionais reais ou ganhos financeiros medidos. Evidências futuras serão resultados da simulação. Revisão humana será necessária em situações ambíguas.

## Histórico — atualização documental durante F1-P04

Negócio, contratos, proteção inicial Git e modelagem foram aceitos
por passo pela gestão. A F1 permanece aberta; P04 está em consolidação.
Não há implementação executável.

- [Contratos](docs/06-event-and-document-contracts.md)
- [Modelo conceitual e lógico](docs/07-conceptual-and-logical-model.md)
- [Consolidação, proposta analítica e R01–R17](docs/08-f1-consolidation-and-analytical-model.md)

21/10/2026 é alvo de demonstração inicial sujeito a reestimativa.

## Fechamento documental autorizado

F1 FECHADA no escopo documental em 16/10/2026, por VAL-F1-P04-001.
F2 pronta para receber o primeiro cartão do gerente, ainda não iniciada.
F3–F6 bloqueadas pelas dependências anteriores.

Artefatos, validações, commits, evidências, participação e limitações:
[passagem consolidada](docs/08-f1-consolidation-and-analytical-model.md#registro-final-autorizado--val-f1-p04-001).
Nenhuma instalação ou implementação iniciada por este fechamento.
