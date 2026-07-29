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

Os detalhes funcionais de cada módulo serão documentados em seções próprias.

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
