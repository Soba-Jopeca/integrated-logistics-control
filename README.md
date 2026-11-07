# Integrated Logistics Control

**Dados, automação e analytics aplicados à conferência documental e ao acompanhamento de entregas.**

Projeto autoral e educacional de **João Pedro Caneca**, desenvolvido com dados sintéticos para demonstrar como necessidades operacionais podem ser transformadas em ingestão rastreável, regras de negócio, aplicação local e indicadores analíticos.

> **Estado atual: projeto em desenvolvimento contínuo.** Fases anteriores possuem entregas e validações documentadas, mas o produto ainda não está concluído. A branch `main` mantém a apresentação pública e a baseline documental; as implementações posteriores permanecem em branches e no PR indicados abaixo.

## Problema de negócio

Pedidos, eventos de transporte e comprovantes podem estar distribuídos em fontes diferentes. Isso dificulta identificar rapidamente:

- entregas sem comprovante;
- divergências entre pedido, evento e documento;
- documentos substituídos ou pendentes de revisão;
- atrasos e ocorrências que exigem priorização;
- diferenças entre conclusão física e regularidade documental.

O projeto preserva uma regra central: **entrega física e aprovação documental são estados independentes**.

## Solução em desenvolvimento

O ILC está sendo construído para:

1. consumir eventos de uma API local simulada e importar dados sintéticos;
2. preservar origem, histórico, tentativas e decisões;
3. armazenar dados em PostgreSQL com migrações controladas;
4. extrair campos de documentos PDF textual e XML educacional;
5. aplicar conferência determinística e explicar divergências;
6. disponibilizar busca, filtros e histórico em aplicação Streamlit;
7. produzir métricas SQL e uma camada analítica para consumo no Power BI;
8. avaliar IA local de forma isolada, sem aprovação automática de documentos.

## Estado das fases

| Fase | Escopo | Estado |
|---|---|---|
| **F1** | Entendimento do negócio, escopo, arquitetura, contratos e modelo de dados | **Fechada documentalmente** e integrada à `main` |
| **F2** | Ambiente reproduzível, PostgreSQL, Alembic, modelo físico e dados sintéticos | **Fechada com limitações**; consolidada no [PR #2](https://github.com/Soba-Jopeca/integrated-logistics-control/pull/2), ainda sem merge |
| **F3** | FastAPI, captura, carga, idempotência, falhas controladas e recuperação | **Fechada com limitações**; preservada nas [branches F3](https://github.com/Soba-Jopeca/integrated-logistics-control/branches/all?query=feat%2Ff3) |
| **F4** | Extração PDF/XML, validação documental, histórico e experimento local de IA | **Fechada com limitações**; consolidação em [docs/f4-p04-consolidation](https://github.com/Soba-Jopeca/integrated-logistics-control/tree/docs/f4-p04-consolidation) |
| **F5** | Aplicação local, métricas SQL, camada Gold e Power BI | **Em desenvolvimento**, distribuída nas [branches F5](https://github.com/Soba-Jopeca/integrated-logistics-control/branches/all?query=feat%2Ff5) |
| **F6** | CI/E2E, backup, recuperação, empacotamento e release | **Não iniciada** |

Os estados acima representam o escopo demonstrado em cada fase. Não significam integração automática à `main`, prontidão produtiva ou conclusão integral do projeto.

## Entregas técnicas já demonstradas

- ambiente Python isolado e dependências fixadas;
- PostgreSQL local dedicado, SQLAlchemy e migrações Alembic;
- modelo com histórico, vínculos, restrições e dados sintéticos reproduzíveis;
- API FastAPI com OpenAPI, paginação e falhas controladas;
- captura e carga com rastreabilidade, idempotência e conflitos explícitos;
- retry limitado, checkpoint e retomada de execução;
- extração de PDF textual e XML educacional;
- conferência documental determinística, versionamento e histórico;
- aplicação Streamlit e referências analíticas SQL em branches F5;
- experimentação local com IA mantida fora do fluxo de aprovação.

## Tecnologias

| Área | Tecnologias |
|---|---|
| **Dados e backend** | Python, SQL, PostgreSQL, SQLAlchemy e Alembic |
| **API e ingestão** | FastAPI, HTTPX, CSV e dados sintéticos |
| **Aplicação e analytics** | Streamlit, SQL analítico e Power BI Desktop |
| **Qualidade e desenvolvimento** | Pytest, Ruff, Git e GitHub |
| **Experimento local de IA** | Ollama e Qwen2.5, de forma isolada |

## Navegação técnica

A `main` não contém todas as implementações já desenvolvidas. Para acompanhar a evolução:

- [Documentação de negócio e arquitetura na main](docs/)
- [F2 — consolidação e ambiente reproduzível](https://github.com/Soba-Jopeca/integrated-logistics-control/tree/docs/f2-p04-consolidation)
- [F3 — API, ingestão e confiabilidade](https://github.com/Soba-Jopeca/integrated-logistics-control/tree/feat/f3-p03-reliability)
- [F4 — documentos, conferência e IA experimental](https://github.com/Soba-Jopeca/integrated-logistics-control/tree/docs/f4-p04-consolidation)
- [F5 — aplicação, analytics e Power BI](https://github.com/Soba-Jopeca/integrated-logistics-control/tree/feat/f5-p03a-gold)

Cada branch mantém suas próprias instruções, evidências, limitações e comandos de reprodução. Não executar instruções de uma fase a partir da `main` desatualizada para aquele recorte.

## Limites e transparência

- Dados, documentos, empresas e operações são sintéticos ou educacionais.
- Não há integração com ERP, WMS ou TMS corporativos reais.
- O projeto não representa oficialmente a arquitetura de nenhuma empresa.
- Não há ganhos financeiros ou operacionais empresariais medidos.
- A execução é local e ainda não representa ambiente produtivo.
- O experimento de IA não aprova documentos nem altera decisões do domínio.
- Branches de desenvolvimento ainda não foram consolidadas em uma release única.
- CI/E2E, backup, recuperação e release permanecem no escopo futuro da F6.

## Próximos passos

- concluir e validar as entregas restantes da F5;
- reconciliar resultados SQL, camada Gold e Power BI;
- organizar a integração controlada das branches aprovadas;
- atualizar instruções de execução após a consolidação;
- iniciar a F6 somente após o fechamento da F5.

---

**Autor:** [João Pedro Caneca](https://github.com/Soba-Jopeca)  
**Portfólio:** [soba-jopeca.github.io](https://soba-jopeca.github.io/)  
**LinkedIn:** [joao-caneca](https://www.linkedin.com/in/joao-caneca/)
