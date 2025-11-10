API Interna de Índices e Câmbio da GuessEste projeto é um microsserviço em FastAPI que atua como um middleware (abstrator e cache) entre os sistemas internos da Guess e a API pública de Séries Temporais (SGS) do Banco Central do Brasil.O objetivo é centralizar a lógica de busca, traduzir nomes amigáveis (ex: ipca_mensal) para códigos de série (ex: 433) e implementar um cache robusto para evitar chamadas desnecessárias à API do BCB, garantindo alta performance e resiliência.Tech Stack:FastAPIUvicorn (Servidor ASGI)Httpx (Cliente HTTP assíncrono)Cachetools (Cache em memória com TTL)Como Rodar o ProjetoCrie um ambiente virtual (Recomendado):python -m venv venv
Ative o ambiente:No Windows: .\venv\Scripts\activateNo macOS/Linux: source venv/bin/activateInstale as dependências:pip install -r requirements.txt
Execute o servidor:uvicorn main:app --reload
O servidor estará rodando em http://127.0.0.1:8000.Endpoints DisponíveisAcesse a documentação interativa (Swagger UI) para testar os endpoints:https://www.google.com/search?q=http://127.0.0.1:8000/docsÍndices EconômicosGET /api/v1/indice/{nome_indice}Busca o último valor de um índice econômico.Nomes de índice disponíveis:ipca_mensal (Cache de 24h)igpm_mensal (Cache de 24h)incc_mensal (Cache de 24h)selic_diaria (Cache de 4h)Exemplo de Resposta (200 OK):{
  "nome": "ipca_mensal",
  "valor": 0.38,
  "data_referencia": "2025-10-01",
  "fonte": "BCB-SGS"
}
Moedas (PTAX)GET /api/v1/moeda/ptax/{codigo_moeda}Busca a última cotação PTAX de fechamento para uma moeda. A busca não diferencia maiúsculas de minúsculas (usd, USD, eur, JPY, etc.).Códigos de moeda disponíveis:USD (Dólar)EUR (Euro)JPY (Iene Japonês)(Todos com cache de 4h)Exemplo de Resposta (200 OK):{
  "moeda": "USD",
  "valor_brl": 5.4321,
  "data_referencia": "2025-11-09",
  "fonte": "BCB-SGS-PTAX"
}
