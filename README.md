# BestCell System — v2.0.0

Sistema interno para loja e assistência técnica de celulares, desenvolvido em Python com Streamlit e SQLite.

## O que mudou na v2.0

A v1.0 era dedicada à gestão de vendas de aparelhos: cadastro de vendas, controle de parcelamento e relatórios financeiros.

Na v2.0, o BestCell System foi reorganizado como uma aplicação modular. A funcionalidade existente foi preservada e passou a compor o módulo de **Vendas**. A antiga página de vendas evoluiu para o shell da aplicação, responsável pelo cabeçalho, pela barra lateral e pela navegação entre os módulos.

Também foi criada a camada `core`, que centraliza o gerenciamento de estado da interface e evita conflitos entre os módulos durante o uso do sistema.

## Arquitetura modular

Cada módulo possui uma estrutura própria em camadas:

- **Orquestrador:** coordena o fluxo e a interface do módulo.
- **Database:** acessa e mantém as tabelas do módulo.
- **Utils:** concentra regras de negócio e funções de apoio.
- **View:** apresenta dados e componentes da interface.

Os módulos compartilham o mesmo banco SQLite, mas cada um manipula exclusivamente suas próprias tabelas. Assim, as funcionalidades permanecem separadas e não interferem entre si.

## Módulos da v2.0

- **Vendas:** evolução do conteúdo da v1.0, responsável pelas vendas de aparelhos, parcelamentos e relatórios.
- **Ordens de serviço:** novo módulo para o atendimento e acompanhamento de serviços técnicos.
- **Estoque:** novo módulo para o controle de itens utilizados na operação da loja.
- **Catálogo:** novo módulo para consulta de produtos e apoio à comercialização.

## Funcionalidades dos módulos

### Vendas

O módulo de **Vendas** preserva as funcionalidades que compunham integralmente a v1.0: cadastro de vendas de aparelhos, controle de parcelamentos e relatórios financeiros. Com a arquitetura modular, ele passou a operar como uma área independente dentro do sistema.

#### Frequência de pagamentos

Nas vendas parceladas da v1.0, as datas das parcelas eram sempre geradas com intervalo de 30 dias a partir da data da venda, caracterizando pagamentos mensais.

Na v2.0, foi incluído o campo **Frequência de Pagamentos**, que permite escolher o intervalo de vencimento das parcelas:

- **Mensal:** parcelas a cada 30 dias.
- **Quinzenal:** parcelas a cada 15 dias.
- **Semanal:** parcelas a cada 7 dias.

Essa escolha é aplicada ao criar a venda e define as datas de vencimento de todas as parcelas geradas.

#### Relatórios e saúde do sistema

Os relatórios e as informações de saúde do sistema, antes exibidos na navegação da v1.0, foram realocados para dentro do módulo de Vendas. A mudança preserva o acesso às informações financeiras e libera a barra lateral principal para o menu de navegação entre os módulos da v2.0.

### Ordens de Serviço

O módulo de **Ordens de Serviço** controla os aparelhos recebidos na loja para reparo, desde o cadastro até a conclusão ou o cancelamento do atendimento.

#### Fluxo de atendimento

Cada cadastro gera um card de OS em um quadro Kanban. O acompanhamento segue o fluxo **Recebido → Em análise → Em reparo → Pronto**, registrando as datas de cada avanço para manter o histórico do atendimento.

#### Informações e senha do aparelho

A OS permite editar as informações do aparelho e do cliente, o serviço executado, observações e a senha de desbloqueio. Para aparelhos Android com padrão de tela, o módulo inclui um **pattern lock** que simula a grade 3×3 do sistema Android e permite registrar o padrão de forma visual.

#### Atendimento, comunicação e consulta

- Geração de PDF da ordem de serviço.
- Geração de mensagem para comunicação via WhatsApp.
- Busca de ordens de serviço ativas e arquivadas.
- Edição das informações ao longo do atendimento.

#### Métricas e arquivamento

O módulo apresenta métricas e relatórios financeiros e operacionais. Ao concluir ou cancelar um atendimento, a OS é arquivada em uma tabela própria, preservando o histórico sem misturá-lo às ordens em andamento.

### Estoque

O módulo de **Estoque** acompanha o estoque físico da loja com uma lógica voltada à reposição e ao reaproveitamento de componentes. Ele não reproduz um sistema de estoque convencional: não controla preço, fornecedor ou custos, pois capas e películas possuem preço de venda unificado. O foco é identificar quantidades disponíveis, necessidades de reposição e peças que podem ser usadas em reparos.

#### Peças

Registra peças e componentes de celulares disponíveis para reaproveitamento em reparos. Esses itens não são repostos por compra: são retirados de aparelhos ou carcaças sem conserto, ou cujo reparo não compensa o custo. O módulo permite consultar a disponibilidade antes de iniciar um novo serviço técnico.

#### Capas

Controla a disponibilidade de capas por modelo e cor. Além de identificar os modelos zerados que precisam ser repostos, o módulo mostra quais cores permanecem em estoque, ajudando a evitar a compra repetida de cores e a manter opções variadas para os clientes.

#### Películas

Controla a quantidade disponível por modelo e considera a compatibilidade entre aparelhos. Para indicar a reposição, o estoque mínimo leva em conta tanto as películas cadastradas para o modelo quanto as quantidades dos modelos compatíveis. Dessa forma, a necessidade de reposição reflete a disponibilidade real de películas que podem atender ao aparelho.

#### Dashboard

O dashboard consolida essas informações para apoiar a operação diária: disponibilidade de peças para reparo, modelos de capas sem estoque e níveis de películas que exigem atenção na reposição.

### Catálogo

O módulo de **Catálogo** é uma ferramenta de apoio ao atendimento no balcão. Ele reúne os preços e as características dos produtos vendidos pela loja, funcionando como tabela comercial e como conjunto de calculadoras para a negociação.

#### Cadastro de produtos

Cada categoria possui um CRUD independente, com os campos relevantes para sua venda:

- **iPhones:** modelo, armazenamento, cor, condição da bateria, disponibilidade e preço.
- **Androids:** marca, modelo, memória RAM, armazenamento, estado e preço.
- **Perfumes e PODs:** cadastro com os atributos específicos de cada categoria.

#### Simuladores e calculadoras

- **Simulador de venda:** calcula entrada, juros e parcelamento para apoiar a negociação com o cliente.
- **Calculadora de atraso:** calcula o valor de atraso com multa fixa de **R$ 3,90 por dia**.

## Foco no negócio

O BestCell System não foi pensado como um ERP genérico. Cada módulo foi desenvolvido para a rotina real de uma loja e assistência técnica de celulares, priorizando fluxos simples, objetivos e coerentes com a operação do negócio.

## Requisitos

- Python 3.10 ou posterior

## Como executar

```bash
pip install -r requirements.txt
streamlit run bestsystem.py
```

O aplicativo ficará disponível em `http://localhost:8501`.

## Dados locais

O banco SQLite (`bestsystem.db`), cópias de segurança, laudos e caches são mantidos fora do repositório para não publicar dados operacionais.
