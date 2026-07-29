# BestCell System — v2.0.0

Sistema interno para loja e assistência técnica de celulares, desenvolvido em Python com Streamlit e SQLite.

## Módulos

- **Vendas:** cadastro, parcelas e acompanhamento financeiro.
- **Ordens de serviço:** gestão do atendimento técnico e emissão de documentos.
- **Estoque:** peças, capas, películas e compatibilidades.
- **Catálogo:** consulta de produtos e simulação de vendas.

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
