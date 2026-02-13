import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from groq import AsyncGroq

load_dotenv()
# Inicializamos la app FastAPI
app = FastAPI(
    title="API de Triaje B2B",
    description="Clasificación automática de tickets de soporte con IA",
    version="1.0.0"
)

# MODELOS DE DATOS (PYDANTIC)
class TicketRequest(BaseModel):
    texto_ticket: str = Field(..., example="Llevo 3 días intentando acceder a mi cuenta y el sistema no reconoce mi contraseña. ¡Es urgente, pierdo dinero!")
    categorias_disponibles: List[str] = Field(..., example=["Facturación", "Soporte Técnico", "Ventas", "Otro"])

class TicketResponse(BaseModel):
    categoria_sugerida: str
    sentimiento: str
    urgencia: str
    resumen: str

# CONFIGURACIÓN DEL CLIENTE IA
# Verificamos que la clave existe antes de arrancar para evitar errores silenciosos
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("¡ALTO! Falta la variable GROQ_API_KEY. Asegúrate de tener tu archivo .env configurado en la raíz del proyecto.")

client = AsyncGroq(api_key=api_key)

# ENDPOINT PRINCIPAL 
@app.post("/api/v1/triage", response_model=TicketResponse)
async def analizar_ticket(request: TicketRequest):
    # Construimos el Prompt inyectando las categorías dinámicas que envíe el cliente
    system_prompt = f"""
    Eres un asistente experto en atención al cliente B2B. Tu tarea es analizar el ticket de soporte y devolver ÚNICAMENTE un objeto JSON válido.
    
    Reglas de clasificación:
    - categoria_sugerida: Debe ser estrictamente una de estas opciones: {request.categorias_disponibles}
    - sentimiento: "Positivo", "Neutral" o "Negativo".
    - urgencia: "Baja", "Media" o "Alta".
    - resumen: Un resumen del problema en un máximo de 10 palabras.
    
    Formato de salida esperado (JSON puro, sin Markdown):
    {{
        "categoria_sugerida": "...",
        "sentimiento": "...",
        "urgencia": "...",
        "resumen": "..."
    }}
    """

    try:
        # Llamada asíncrona al LLM 
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.texto_ticket}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0, # Temperatura 0 para respuestas lógicas y deterministas
            response_format={"type": "json_object"} # Forzamos que la IA escupa un JSON nativo
        )

        # Extraemos el texto de la respuesta y lo convertimos a un diccionario Python
        respuesta_json = json.loads(chat_completion.choices[0].message.content)
        
        # Pydantic empaqueta la respuesta y valida que tenga los campos exactos
        return TicketResponse(**respuesta_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento de IA: {str(e)}")

# ENDPOINT DE SALUD
# Útil para que plataformas de hosting (como Vercel/Render) sepan que tu API está viva
@app.get("/")
async def health_check():
    return {"status": "API de Triaje Operativa", "version": "1.0.0"}