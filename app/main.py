import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List
from groq import AsyncGroq

load_dotenv()

app = FastAPI(
    title="API de Triaje B2B",
    description="Clasificación automática de tickets con detección de idioma y entidades",
    version="1.1.0"
)

# MODELOS DE DATOS
class TicketRequest(BaseModel):
    texto_ticket: str = Field(..., example="Llevo 3 días intentando acceder a mi cuenta y el sistema no reconoce mi contraseña.")
    categorias_disponibles: List[str] = Field(..., example=["Facturación", "Soporte Técnico", "Ventas", "Otro"])

class TicketResponse(BaseModel):
    categoria_sugerida: str
    sentimiento: str
    urgencia: str
    idioma: str
    datos_clave: List[str]
    resumen: str

# CONFIGURACIÓN IA
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("Falta GROQ_API_KEY")

client = AsyncGroq(api_key=api_key)

# SEGURIDAD
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)
API_KEY_MAESTRA = os.environ.get("API_KEY_MAESTRA", "mi_clave_secreta_local_123")

def verificar_api_key(api_key_recibida: str = Security(api_key_header)):
    if api_key_recibida != API_KEY_MAESTRA:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return api_key_recibida

# ENDPOINT PRINCIPAL
@app.post("/api/v1/triage", response_model=TicketResponse)
async def analizar_ticket(request: TicketRequest, api_key: str = Security(verificar_api_key)):
    system_prompt = f"""
    Eres un analista experto. Analiza el ticket y devuelve ÚNICAMENTE un JSON válido.
    
    Reglas:
    - categoria_sugerida: Una de estas: {request.categorias_disponibles}
    - sentimiento: "Positivo", "Neutral" o "Negativo".
    - urgencia: "Baja", "Media" o "Alta".
    - idioma: Nombre del idioma detectado.
    - datos_clave: Lista de strings con IDs, nombres, correos o productos mencionados.
    - resumen: Máximo 10 palabras.

    Formato JSON:
    {{
        "categoria_sugerida": "...",
        "sentimiento": "...",
        "urgencia": "...",
        "idioma": "...",
        "datos_clave": ["...", "..."],
        "resumen": "..."
    }}
    """

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.texto_ticket}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        respuesta_json = json.loads(chat_completion.choices[0].message.content)
        return TicketResponse(**respuesta_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error IA: {str(e)}")

@app.get("/")
async def health_check():
    return {"status": "Operativa", "version": "1.1.0"}