# ⚡ Quick Start - 5 Minutos

## 1️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

## 2️⃣ Ejecutar API localmente

```bash
python main.py
```

Deberías ver:
```
INFO:     Started server process [12345]
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## 3️⃣ Probar endpoints

### Opción A: Swagger UI (Más fácil)

Abre en tu navegador:
```
http://localhost:8080/docs
```

Aquí puedes probar directamente los endpoints con una UI interactiva.

### Opción B: Línea de comandos

```bash
# Obtener listados
curl -X POST "http://localhost:8080/obtener-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 3
  }'

# Scrapear propiedades
curl -X POST "http://localhost:8080/scrape-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 2,
    "mode": "sequential"
  }'
```

### Opción C: Script Python

```bash
python test_api.py
```

## 4️⃣ Desplegar a Cloud Run (Opcional)

### Configuración inicial (una sola vez)

```bash
# 1. Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# 2. Autenticarse
gcloud auth login

# 3. Crear proyecto (reemplaza tu-proyecto-id)
gcloud config set project tu-proyecto-id

# 4. Habilitar APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Deploy manual

```bash
gcloud run deploy lamudi-scraper \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 600
```

### Deploy automático con GitHub

1. Ir a [DEPLOYMENT.md](DEPLOYMENT.md)
2. Seguir pasos 1-3
3. Hacer push a GitHub
4. Esperar a que GitHub Actions complete el deploy

```bash
git add .
git commit -m "Deploy to Cloud Run"
git push origin main
```

## 📊 Respuestas de ejemplo

### Obtener Listados

```json
{
  "status": "success",
  "cp": "03100",
  "tipo_propiedad": "departamento",
  "precio": 6000000,
  "total_listados": 3,
  "listados": [
    "https://www.lamudi.com.mx/departamento/for-sale/...",
    "https://www.lamudi.com.mx/departamento/for-sale/...",
    "https://www.lamudi.com.mx/departamento/for-sale/..."
  ]
}
```

### Scrapear Propiedades

```json
{
  "status": "success",
  "cp": "03100",
  "tipo_propiedad": "departamento",
  "precio": 6000000,
  "mode": "sequential",
  "total_propiedades": 2,
  "propiedades": [
    {
      "titulo": "Hermoso departamento en Roma",
      "direccion": "Calle Colima 123, Cuauhtémoc",
      "precio": "$5,200,000",
      "superficie": "150 m²",
      "habitaciones": "3",
      "banios": "2",
      "descripcion": "Descripción completa...",
      "url": "https://www.lamudi.com.mx/...",
      "lat": 19.4326,
      "lon": -99.1332,
      "fecha_consulta": "2026-07-16",
      "error": false
    },
    ...
  ]
}
```

## 🔧 Parámetros de los Endpoints

### POST /obtener-listados

| Parámetro | Tipo | Requerido | Ejemplo | Descripción |
|-----------|------|-----------|---------|-------------|
| cp | string | ✅ | "03100" | Código postal |
| tipo_propiedad | string | ✅ | "departamento" | casa, departamento, terreno, comercial |
| precio | float | ❌ | 6000000 | Precio en MXN para filtrar |
| max_listados | int | ❌ | 6 | Número máximo de listados (default: 6) |

### POST /scrape-listados

| Parámetro | Tipo | Requerido | Ejemplo | Descripción |
|-----------|------|-----------|---------|-------------|
| cp | string | ✅ | "03100" | Código postal |
| tipo_propiedad | string | ✅ | "departamento" | casa, departamento, terreno, comercial |
| precio | float | ❌ | 6000000 | Precio en MXN para filtrar |
| max_listados | int | ❌ | 6 | Número máximo de propiedades (default: 6) |
| mode | string | ❌ | "sequential" | parallel (rápido) o sequential (estable) |

## 📝 Notas Importantes

- **Scraping toma tiempo**: Cada propiedad puede tomar 10-30 segundos
- **Modo sequential es más estable** que parallel en cloud
- **Aumentar max_listados aumenta el tiempo** de respuesta
- **Los datos NO se guardan como CSV**, se devuelven en JSON

## ⚠️ Troubleshooting

| Problema | Solución |
|----------|----------|
| "Connection refused" | Asegúrate que `python main.py` está corriendo |
| Timeout | Reduce `max_listados` o usa `mode: "sequential"` |
| "Página bloqueada" | Lamudi detectó scraping, espera 24h e intenta de nuevo |
| Chrome/Chromium no instala | En local: `pip install webdriver-manager` |

## 📚 Más información

- [README.md](README.md) - Documentación completa
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guía de deploy a Cloud Run
- [API Docs Interactivo](http://localhost:8080/docs) - Swagger UI

## 💡 Tips

1. **Usar Swagger UI** (`http://localhost:8080/docs`) para explorar endpoints
2. **Empezar con `max_listados: 2`** para testing rápido
3. **Usar `mode: "sequential"`** para debug (es más lento pero más fácil de debuggear)
4. **Consultar logs** con `gcloud run logs read lamudi-scraper`

¡Listo! 🎉
