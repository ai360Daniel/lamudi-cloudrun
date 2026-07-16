# Guía Completa: Deploy a Cloud Run con GitHub

## Paso 1: Preparar Repositorio GitHub

### 1.1 Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `lamudi-cloudrun` (o el que prefieras)
3. Descripción: "API para scraping de propiedades en Lamudi"
4. Elige `Public` o `Private`
5. Clic en "Create repository"

### 1.2 Inicializar repositorio local

```bash
# En el directorio del proyecto
git init
git add .
git commit -m "Initial commit: Lamudi Scraper API for Cloud Run"
git branch -M main
git remote add origin https://github.com/tu-usuario/lamudi-cloudrun.git
git push -u origin main
```

## Paso 2: Configurar Google Cloud Platform

### 2.1 Crear proyecto en GCP

```bash
# Instalar gcloud CLI si no lo tienes
# https://cloud.google.com/sdk/docs/install

# Autenticarse
gcloud auth login

# Crear nuevo proyecto (reemplaza PROJECT_NAME)
gcloud projects create lamudi-scraper --name="Lamudi Scraper API"

# Obtener ID del proyecto
gcloud projects list

# Configurar proyecto activo (reemplaza PROJECT_ID)
gcloud config set project PROJECT_ID

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### 2.2 Crear Artifact Registry

```bash
# Crear repositorio para imágenes Docker
gcloud artifacts repositories create lamudi \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Lamudi Scraper"
```

### 2.3 Crear Workload Identity (para GitHub Actions)

```bash
# Crear service account
gcloud iam service-accounts create github-runner \
  --display-name="GitHub Runner for Cloud Run"

# Obtener email del service account
gcloud iam service-accounts list --filter="displayName:GitHub Runner"

# Reemplaza SERVICE_ACCOUNT_EMAIL con el email obtenido arriba
export SERVICE_ACCOUNT_EMAIL="github-runner@PROJECT_ID.iam.gserviceaccount.com"

# Crear Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Pool"

# Crear Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-condition="assertion.repository_owner == 'tu-usuario'"

# Obtener el WIF Provider
gcloud iam workload-identity-pools providers describe "github-provider" \
  --workload-identity-pool="github-pool" \
  --location="global" \
  --format="value(name)"

# Dar permisos al service account (reemplaza los valores)
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
  --project="PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/tu-usuario/lamudi-cloudrun"

# Dar permisos para Cloud Run, Artifact Registry
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

## Paso 3: Configurar Secrets en GitHub

### 3.1 Agregar secrets al repositorio

1. Ve a tu repositorio en GitHub
2. Clic en "Settings" → "Secrets and variables" → "Actions"
3. Agrega estos secrets:

**GCP_PROJECT_ID**
```
PROJECT_ID (el ID de tu proyecto GCP)
```

**WIF_PROVIDER**
```
projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

**WIF_SERVICE_ACCOUNT**
```
github-runner@PROJECT_ID.iam.gserviceaccount.com
```

Para obtener PROJECT_NUMBER:
```bash
gcloud projects describe PROJECT_ID --format='value(projectNumber)'
```

## Paso 4: Deploy Manual (Opcional - para probar)

```bash
# Deploy directo a Cloud Run
gcloud run deploy lamudi-scraper \
  --source . \
  --region us-central1 \
  --platform managed \
  --memory 2Gi \
  --timeout 600 \
  --allow-unauthenticated \
  --max-instances 10

# Obtener URL del servicio
gcloud run services describe lamudi-scraper --region us-central1 --format='value(status.url)'
```

## Paso 5: Deploy Automático con GitHub Actions

### 5.1 El workflow está listo

El archivo `.github/workflows/deploy.yml` ya está configurado. Solo necesitas:

1. Hacer push a `main`:
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. GitHub Actions automáticamente:
   - Construirá la imagen Docker
   - La subirá a Artifact Registry
   - La deployará a Cloud Run

3. Ver progreso en: `tu-repositorio/actions`

## Paso 6: Prueba la API

### 6.1 Obtener URL del servicio

```bash
gcloud run services describe lamudi-scraper \
  --region us-central1 \
  --format='value(status.url)'
```

### 6.2 Probar endpoints

```bash
# Health check
curl https://lamudi-scraper-XXXXX.a.run.app/health

# Ver documentación
# https://lamudi-scraper-XXXXX.a.run.app/docs

# Obtener listados
curl -X POST "https://lamudi-scraper-XXXXX.a.run.app/obtener-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 6
  }'

# Scrapear propiedades
curl -X POST "https://lamudi-scraper-XXXXX.a.run.app/scrape-listados" \
  -H "Content-Type: application/json" \
  -d '{
    "cp": "03100",
    "tipo_propiedad": "departamento",
    "precio": 6000000,
    "max_listados": 3,
    "mode": "sequential"
  }'
```

## Paso 7: Monitoreo

### 7.1 Ver logs en tiempo real

```bash
# Logs de Cloud Run
gcloud run logs read lamudi-scraper --limit=100 --follow

# O en Cloud Console
# https://console.cloud.google.com/run/detail/us-central1/lamudi-scraper/logs
```

### 7.2 Ver métricas

```bash
# Ver invocaciones
gcloud monitoring time-series list \
  --filter="metric.type=run.googleapis.com/request_count AND resource.service_name=lamudi-scraper"
```

## Paso 8: Hacer Cambios y Actualizar

Simplemente haz cambios locales y push a main:

```bash
# Editar código
# ...

# Commit y push
git add .
git commit -m "Improve scraping logic"
git push origin main

# GitHub Actions se ejecutará automáticamente
# Ver progreso en: Actions tab
```

## Troubleshooting

### Error: "Permission denied"
```bash
# Revisar permisos del service account
gcloud iam service-accounts get-iam-policy $SERVICE_ACCOUNT_EMAIL
```

### Cloud Run falla con Chrome
```bash
# Revisar logs
gcloud run logs read lamudi-scraper --limit=50

# Posible solución: aumentar memoria
gcloud run services update lamudi-scraper \
  --region us-central1 \
  --memory 2Gi
```

### GitHub Actions falla con auth
```bash
# Revisar que los secrets estén correctos
# Settings → Secrets and variables → Actions
# Verificar que los valores sean exactos (sin espacios)
```

## Costos

- **Cloud Run**: ~$0.40 USD por millón de requests (primera capa gratuita incluida)
- **Artifact Registry**: ~$0.40 USD por GB de almacenamiento (primeros 0.5GB gratis)
- **Compute**: $0.00002400 USD por vCPU-segundo

Estimado mensual para uso moderado: $1-5 USD

## ¡Listo!

Tu API está desplegada en Cloud Run y lista para usar:

```
https://lamudi-scraper-XXXXX.a.run.app
```

Para más ayuda:
- Google Cloud Run Docs: https://cloud.google.com/run/docs
- GitHub Actions: https://docs.github.com/en/actions
