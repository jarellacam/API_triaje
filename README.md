# API de Triaje B2B con LLM

API REST que clasifica automáticamente tickets de soporte con un LLM: categoría, sentimiento, urgencia, idioma, entidades clave y un resumen breve, devueltos como JSON validado por Pydantic.

## Por qué

Los equipos de soporte pierden tiempo leyendo y enrutando tickets a mano. Esta API recibe el texto del ticket y la lista de categorías de cada cliente, y devuelve una respuesta estructurada lista para integrarse en un helpdesk o CRM.

## Stack

| Área | Tecnología |
|---|---|
| API | FastAPI + Uvicorn (asíncrona) |
| Validación | Pydantic |
| LLM | Llama 3.1 8B Instant vía Groq (`temperature=0`, modo JSON) |
| Seguridad | Autenticación por cabecera `X-API-KEY` |

## Instalación

```bash
git clone https://github.com/jarellacam/API_triaje.git
cd API_triaje
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz:

```env
GROQ_API_KEY=tu_clave_de_groq
API_KEY_MAESTRA=una_clave_larga_y_aleatoria
```

Arranca el servidor:

```bash
uvicorn app.main:app --reload
```

La documentación interactiva queda en `http://localhost:8000/docs`.

## Uso

```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: una_clave_larga_y_aleatoria" \
  -d '{
    "texto_ticket": "Llevo 3 días intentando acceder a mi cuenta y el sistema no reconoce mi contraseña.",
    "categorias_disponibles": ["Facturación", "Soporte Técnico", "Ventas", "Otro"]
  }'
```

Respuesta:

```json
{
  "categoria_sugerida": "Soporte Técnico",
  "sentimiento": "Negativo",
  "urgencia": "Alta",
  "idioma": "Español",
  "datos_clave": ["cuenta", "contraseña"],
  "resumen": "Usuario no puede acceder a su cuenta desde hace días"
}
```

*(Ejemplo ilustrativo: la salida exacta depende del modelo.)*

## Decisiones de diseño

- **Categorías dinámicas:** cada cliente envía sus propias categorías, así la misma API sirve a varios negocios sin reentrenar nada.
- **Salida determinista:** `temperature=0` y `response_format` JSON reducen respuestas mal formadas.
- **Cliente asíncrono:** `AsyncGroq` permite atender varias peticiones concurrentes sin bloquear.

## Próximos pasos

- Tests con pytest y un conjunto de tickets etiquetados para medir la precisión de la clasificación.
- Dockerfile para despliegue.

---

Juan Arellano Cameo · [LinkedIn](https://linkedin.com/in/juann-arellano)
