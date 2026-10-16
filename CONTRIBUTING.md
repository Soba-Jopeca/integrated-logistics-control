# Como desenvolver e aprender neste projeto

## Responsabilidades

João Pedro Caneca implementa, executa e explica a solução. A orientação técnica apoia documentação, conceitos e revisão. Sugestões geradas por IA devem ser compreendidas e verificadas antes da integração.

## Fluxo Git

1. Definir uma tarefa com problema, escopo e critérios de aceite em uma issue.
2. Atualizar a main local e criar branch curta, por exemplo: docs/data-contracts ou feat/orders-ingestion.
3. Fazer uma mudança pequena, com evidência proporcional ao risco.
4. Revisar o diff; não incluir credenciais, documentos reais ou arquivos locais gerados.
5. Commit com intenção clara: docs:, feat:, fix: ou test:.
6. Abrir pull request com problema, mudança, validação e limitações.
7. Integrar após revisão e atualizar o estado da documentação.

A carga documental inicial pode ser registrada diretamente na main para inicializar o repositório vazio. Mudanças posteriores seguem o fluxo por branch/PR. Não há proteção de branch ou CI configurados nesta etapa.

## Revisão de uma entrega

- Qual necessidade atende?
- Por que essa abordagem?
- Qual é a granularidade e a identidade dos dados?
- O que acontece quando há duplicidade, atraso ou falha?
- Como foi validado?
- O que ficou pendente?

## Evidências e documentação

Informar commit, comando/consulta, entrada, esperado e observado. Não usar credenciais em capturas. Atualizar README apenas com capacidades implementadas ou claramente identificadas como planejadas. Os testes devem validar comportamento e falhas relevantes, sem perseguir quantidade arbitrária.

Não adicionar frameworks, dependências ou infraestrutura sem justificar a necessidade. Requisitos de qualidade devem ser proporcionais à demonstração local.
