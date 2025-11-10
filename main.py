import asyncio
from contextlib import asynccontextmanager
from datetime import date
from typing import Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from cachetools import TTLCache

# Importar o cliente BCB
from bcb_client import get_ultimo_valor_serie

# --- Configuração do Cache ---
# Cache para índices mensais (IPCA, IGP-M, INCC) - 24 horas
cache_indices_mensais = TTLCache(maxsize=100, ttl=86400)
# Cache para dados diários (SELIC, PTAX) - 4 horas
cache_dados_diarios = TTLCache(maxsize=100, ttl=14400)

# --- Mapeamento de Séries (A "Tradução") ---
MAPA_SERIES_INDICES = {
    "ipca_mensal": 433,
    "igpm_mensal": 189,
    "incc_mensal": 192,
    "selic_diaria": 11,
}

MAPA_SERIES_MOEDAS = {
    "USD": 10813,  # PTAX USD Fechamento
    "EUR": 21619,  # PTAX EUR Fechamento
    "JPY": 21623,  # PTAX JPY Fechamento
}

# --- Gerenciamento do Cliente HTTP (Lifespan) ---
# Um único cliente httpx para toda a aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar o cliente
    print("Iniciando cliente HTTP...")
    client = httpx.AsyncClient(timeout=10.0)
    app.state.http_client = client  # Adiciona ao state
    try:
        yield  # A aplicação roda aqui
    finally:
        # Fechar o cliente
        print("Fechando cliente HTTP...")
        await client.aclose()

# --- Inicialização do App FastAPI ---
app = FastAPI(
    title="API Interna de Índices e Câmbio da Guess",
    description="Microsserviço que atua como middleware e cache para a API do Banco Central (BCB-SGS).",
    version="1.0.0",
    lifespan=lifespan
)

# --- Modelos Pydantic (Respostas) ---
class IndiceResponse(BaseModel):
    nome: str = Field(..., description="Nome amigável do índice.")
    valor: float = Field(..., description="Valor percentual ou numérico do índice.")
    data_referencia: date = Field(..., description="Data de referência do dado.")
    fonte: str = Field("BCB-SGS", description="Fonte do dado.")

class MoedaResponse(BaseModel):
    moeda: str = Field(..., description="Código da moeda (ex: USD).")
    valor_brl: float = Field(..., description="Valor da moeda em Reais (BRL).")
    data_referencia: date = Field(..., description="Data de referência da cotação.")
    fonte: str = Field("BCB-SGS-PTAX", description="Fonte do dado.")

# --- Lógica de Cache e Busca ---
async def get_cliente_http(request: Request) -> httpx.AsyncClient:
    """Dependência para injetar o cliente HTTP gerenciado pelo lifespan."""
    return request.app.state.http_client

async def buscar_serie_com_cache(
    codigo_serie: int,
    cache: TTLCache,
    client: httpx.AsyncClient
) -> Dict[str, Any] | None:
    """
    Função helper para verificar o cache antes de buscar no BCB.
    """
    # 1. Tenta buscar do cache
    dados_cacheados = cache.get(codigo_serie)
    if dados_cacheados:
        # print(f"HIT cache para série {codigo_serie}")
        return dados_cacheados

    # 2. Se não está no cache, busca no BCB
    # print(f"MISS cache para série {codigo_serie}. Buscando no BCB...")
    try:
        dados_bcb = await get_ultimo_valor_serie(codigo_serie, client)
        if dados_bcb:
            # 3. Armazena no cache
            cache[codigo_serie] = dados_bcb
            return dados_bcb
    except Exception as e:
        # Se falhar a busca no BCB, não podemos fazer nada
        print(f"Erro ao buscar série {codigo_serie} no BCB: {e}")
        return None
    
    return None

# --- Endpoints da API ---
@app.get(
    "/api/v1/indice/{nome_indice}",
    response_model=IndiceResponse,
    tags=["Índices"]
)
async def get_indice(
    nome_indice: str,
    client: httpx.AsyncClient = Depends(get_cliente_http)
):
    """
    Busca o último valor de um índice econômico (ex: ipca_mensal, selic_diaria).
    """
    if nome_indice not in MAPA_SERIES_INDICES:
        raise HTTPException(
            status_code=404,
            detail=f"Índice '{nome_indice}' não encontrado. Disponíveis: {list(MAPA_SERIES_INDICES.keys())}"
        )
    
    codigo_serie = MAPA_SERIES_INDICES[nome_indice]
    
    # Determina qual cache usar
    if nome_indice == "selic_diaria":
        cache_selecionado = cache_dados_diarios
    else:
        cache_selecionado = cache_indices_mensais
        
    dados_serie = await buscar_serie_com_cache(codigo_serie, cache_selecionado, client)
    
    if dados_serie is None:
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail=f"Não foi possível obter os dados do BCB para o índice '{nome_indice}'."
        )

    return IndiceResponse(
        nome=nome_indice,
        valor=dados_serie["valor"],
        data_referencia=dados_serie["data"]
    )

@app.get(
    "/api/v1/moeda/ptax/{codigo_moeda}",
    response_model=MoedaResponse,
    tags=["Moedas"]
)
async def get_moeda_ptax(
    codigo_moeda: str,
    client: httpx.AsyncClient = Depends(get_cliente_http)
):
    """
    Busca a última cotação PTAX de fechamento para uma moeda (ex: USD, EUR, JPY).
    A busca é case-insensitive (usd, USD, UsD funcionam).
    """
    codigo_moeda_upper  = codigo_moeda.upper()

    if codigo_moeda_upper not in MAPA_SERIES_MOEDAS:
        raise HTTPException(
            status_code=404,
            detail=f"Moeda '{codigo_moeda}' não encontrada. Disponíveis: {list(MAPA_SERIES_MOEDAS.keys())}"
        )

    codigo_serie = MAPA_SERIES_MOEDAS[codigo_moeda_upper]
    
    # Cotações PTAX são diárias
    dados_serie = await buscar_serie_com_cache(codigo_serie, cache_dados_diarios, client)

    if dados_serie is None:
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail=f"Não foi possível obter os dados do BCB para a moeda '{codigo_moeda}'."
        )

    return MoedaResponse(
        moeda=codigo_moeda,
        valor_brl=dados_serie["valor"],
        data_referencia=dados_serie["data"]
    )

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Índices e Câmbio da Guess. Acesse /docs para a documentação."}