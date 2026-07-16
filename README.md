# Lamudi Scraper API

API para obtener y scrapear propiedades de Lamudi.com.mx, optimizada para deployar en Google Cloud Run.

## 🚀 Características

- **Dos Endpoints principales:**
  - `POST /obtener-listados` - Obtiene lista de URLs de propiedades
  - `POST /scrape-listados` - Scrapea datos detallados de propiedades

- **Optimizado para Cloud Run:**
  - Contenedor Docker listo
  - Soporte para headless Chrome/Chromium
  - Anti-detección de bots (User-Agent dinámico, etc.)
  - Scraping paralelo para mejor rendimiento

## 📋 Requisitos

- Python 3.11+
- Docker (para deployar en Cloud Run)
- Cuenta de Google Cloud Platform

## 💻 Desarrollo Local

### Instalación

```bash
# Clonar o descargar el repositorio
cd lamudi-cloudrun

# Crear entorno virtual (opcional)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar localmente

```bash
python main.py
```

La API estará disponible en `http://localhost:8080`

Acceder a la documentación interactiva: `http://localhost:8080/docs`

## 🐳 Docker

### Build local

```bash
docker build -t lamudi-scraper:latest .
docker run -p 8080:8080 lamudi-scraper:latest
```

## ☁️ Deploy a Cloud Run

### Prerequisitos

```bash
# Instalar gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Autenticarse
gcloud auth login

# Configurar proyecto (reemplazar PROJECT_ID)
gcloud config set project PROJECT_ID
```

### Deploy automático desde GitHub

#### 1. Conectar repositorio a Cloud Run

```bash
# Crear repositorio en GitHub (si no lo tienes)
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/lamudi-cloudrun.git
git push -u origin main
```

#### 2. Deploy desde GitHub

```bash
gcloud run deploy lamudi-scraper \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 600s
```

O configurar CI/CD automático:

```bash
# Cloud Build + Cloud Run
gcloud beta run deploy lamudi-scraper \
  --source https://github.com/tu-usuario/lamudi-cloudrun \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --timeout 600s
```

### Crear archivo `cloudbuild.yaml` para automatización

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/lamudi-scraper:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/lamudi-scraper:latest'
      - '.'
  
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/lamudi-scraper:$SHORT_SHA'
  
  - name: 'gcr.io/cloud-builders/run'
    args:
      - 'deploy'
      - 'lamudi-scraper'
      - '--image'
      - 'gcr.io/$PROJECT_ID/lamudi-scraper:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--memory'
      - '2Gi'
      - '--timeout'
      - '600s'

images:
  - 'gcr.io/$PROJECT_ID/lamudi-scraper:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/lamudi-scraper:latest'
```

## 📡 Uso de la API

### 1. Obtener Listados

```bash
curl -X POST "http://localhost:8080/obtener-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 6
  }'
```

**Parámetros:**
- `cp` (string, requerido): Código postal (ej: "03100")
- `tipo_propiedad` (string, requerido): "casa", "departamento", "terreno", "comercial"
- `precio` (float, opcional): Precio en MXN para filtrar
- `max_listados` (int, default: 6): Número máximo de listados

**Respuesta:**
```json
{
  "status": "success",
  "cp": "03100",
  "tipo_propiedad": "departamento",
  "precio": 6000000,
  "total_listados": 6,
  "listados": [
    "https://www.lamudi.com.mx/departamento/for-sale/...",
    ...
  ]
}
```

### 2. Scrapear Propiedades

```bash
curl -X POST "http://localhost:8080/scrape-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 6,
    "mode": "parallel"
  }'
```

**Parámetros:**
- `cp` (string, requerido): Código postal
- `tipo_propiedad` (string, requerido): Tipo de propiedad
- `precio` (float, opcional): Precio para filtrar
- `max_listados` (int, default: 6): Número máximo
- `mode` (string, default: "parallel"): "parallel" o "sequential"

**Respuesta:**
```json
{
  "status": "success",
  "cp": "03100",
  "tipo_propiedad": "departamento",
  "precio": 6000000,
  "mode": "parallel",
  "total_propiedades": 6,
  "propiedades": [
    {
      "titulo": "Hermoso departamento...",
      "direccion": "Calle X, Apartado Y",
      "precio": "$5,500,000",
      "superficie": "150 m²",
      "habitaciones": "3",
      "banios": "2",
      "descripcion": "...",
      "url": "https://...",
      "lat": 19.4326,
      "lon": -99.1332,
      "fecha_consulta": "2026-07-16",
      "error": false
    },
    ...
  ]
}
```

## 🔧 Configuración

### Variables de Entorno

- `PORT` (default: 8080): Puerto de la API
- `K_SERVICE`: Detecta automáticamente si está en Cloud Run

### Límites de Cloud Run

- **Memoria**: 2Gi recomendado
- **Timeout**: 600 segundos (máximo permitido)
- **Workers**: 3 (paralelo recomendado)

## 📊 Ejemplo de Uso Completo

```python
import requests
import json

BASE_URL = "http://localhost:8080"  # O tu URL de Cloud Run

# Paso 1: Obtener listados
response1 = requests.post(
    f"{BASE_URL}/obtener-listados",
    json={
        "cp": "03100",
        "tipo_propiedad": "departamento",
        "precio": 6000000,
        "max_listados": 6
    }
)

listados = response1.json()
print(f"Se encontraron {listados['total_listados']} listados")

# Paso 2: Scrapear propiedades
response2 = requests.post(
    f"{BASE_URL}/scrape-listados",
    json={
        "cp": "03100",
        "tipo_propiedad": "departamento",
        "precio": 6000000,
        "max_listados": 6,
        "mode": "parallel"
    }
)

propiedades = response2.json()
print(json.dumps(propiedades, indent=2, ensure_ascii=False))

# Guardar datos (opcional)
import pandas as pd
df = pd.DataFrame(propiedades['propiedades'])
df.to_csv('propiedades.csv', index=False, encoding='utf-8')
```

## ⚠️ Notas Importantes

1. **Scraping responsable**: Respetar los términos de servicio de Lamudi.com.mx
2. **Rate limiting**: La API está optimizada pero puede necesitar ajustes si Lamudi es más restrictivo
3. **Timeouts**: Cada propiedad tiene timeout de 15-30 segundos máximo
4. **Recursos**: 
   - Cloud Run asigna 1 CPU compartida
   - 2Gi memoria recomendada para rendimiento óptimo

## 🐛 Troubleshooting

### Error: "Página bloqueada (403/404)"
- Lamudi detectó scraping. Esperar 24-48 horas o ajustar User-Agent

### Error: Timeout
- Aumentar timeout en `scrape_property_fast()` (línea con `set_page_load_timeout`)
- Cambiar mode a "sequential" en lugar de "parallel"

### Chrome no carga en Cloud Run
- Verificar que el Dockerfile instala Chromium correctamente
- El path `/usr/bin/chromedriver` debe existir

## 📝 Logs

Ver logs en Cloud Run:
```bash
gcloud run logs read lamudi-scraper --limit=50
```

## 📄 Licencia

Este proyecto es de uso privado. Respetar términos de servicio de Lamudi.

## 🤝 Soporte

Para problemas específicos del scraping de Lamudi, revisar el HTML de la página y actualizar los selectores en `main.py`.
