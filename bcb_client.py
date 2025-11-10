import httpx
from datetime import datetime
from typing import Dict, Any, Optional

# URL base da API do SGS
BCB_API_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados/ultimos/1?formato=json"

async def get_ultimo_valor_serie(
    codigo_serie: int, 
    client: httpx.AsyncClient
) -> Optional[Dict[str, Any]]:
    """
    Busca o último valor de uma série temporal no SGS do Banco Central.

    Args:
        codigo_serie: O código da série no sistema SGS (ex: 433 para IPCA).
        client: Uma instância de httpx.AsyncClient.

    Returns:
        Um dicionário com 'valor' (float) e 'data' (date) ou None em caso de falha.
    """
    url = BCB_API_URL.format(codigo_serie=codigo_serie)
    
    try:
        response = await client.get(url)
        
        # Lança exceção para erros HTTP (4xx, 5xx)
        response.raise_for_status()
        
        dados = response.json()
        
        # Validação da resposta
        if not isinstance(dados, list) or len(dados) == 0:
            print(f"Resposta inesperada do BCB para série {codigo_serie}: {dados}")
            return None
            
        ultimo_registro = dados[0]
        
        # Extrai e formata os dados
        valor_str = ultimo_registro.get("valor")
        data_str = ultimo_registro.get("data")
        
        if valor_str is None or data_str is None:
            print(f"Campos 'valor' ou 'data' ausentes na resposta do BCB: {ultimo_registro}")
            return None

        # Converte valor para float
        try:
            valor_float = float(valor_str)
        except (ValueError, TypeError):
            print(f"Não foi possível converter valor '{valor_str}' para float.")
            return None
            
        # Converte data de 'dd/mm/YYYY' para um objeto date
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except (ValueError, TypeError):
            print(f"Não foi possível converter data '{data_str}' para objeto date.")
            return None
            
        return {
            "valor": valor_float,
            "data": data_obj
        }

    except httpx.HTTPStatusError as exc:
        print(f"Erro HTTP ao buscar série {codigo_serie}: {exc.response.status_code} - {exc.request.url}")
        return None
    except httpx.RequestError as exc:
        print(f"Erro de rede ao buscar série {codigo_serie}: {exc}")
        return None
    except Exception as exc:
        print(f"Erro inesperado ao processar série {codigo_serie}: {exc}")
        return None