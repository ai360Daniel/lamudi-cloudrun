"""
API para Scraping de Propiedades en Lamudi
Endpoints:
- POST /obtener-listados - Obtiene lista de URLs
- POST /scrape-listados - Scrapea datos de propiedades
"""

import re
import time
import logging
import os
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode, urljoin

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# === IMPORTS DEFERRED (lazy) - se cargan solo cuando se necesitan ===
# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from fake_useragent import UserAgent


# ==================== CONFIGURACIÓN ====================
app = FastAPI(
    title="Lamudi Scraper API",
    description="API para obtener y scrapear propiedades de Lamudi.com.mx",
    version="1.0.0"
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== FUNCIONES AUXILIARES ====================

def construir_url_cp(
    cp: str,
    tipo_propiedad: str,
    precio: Optional[float] = None,
    porcentaje: float = 0.20,
    accion: str = "for-sale"
) -> str:
    """
    Construye una URL de búsqueda por CP y opcionalmente por precio.
    """
    cp = str(cp).zfill(5)
    base = f"https://www.lamudi.com.mx/{tipo_propiedad}/{accion}/"
    params = {"search": cp}

    if precio is not None:
        minimo = int(precio * (1 - porcentaje))
        maximo = int(precio * (1 + porcentaje))
        params["min-price"] = minimo
        params["max-price"] = maximo
        params["priceCurrency"] = "MXN"

    return base + "?" + urlencode(params)


def get_stealth_driver():
    """
    Configura el driver con técnicas anti-detección optimizado para velocidad
    """
    # ===== DEFERRED IMPORTS =====
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from fake_useragent import UserAgent
    
    chrome_options = Options()

    # Detectar si estamos en Cloud Run
    is_cloud_run = os.environ.get('K_SERVICE') is not None

    # === ARGUMENTOS PARA VELOCIDAD ===
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # OPTIMIZACIONES DE VELOCIDAD
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    
    # Deshabilitar características que ralentizan
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--media-cache-size=0")

    # Anti-detección
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # User-Agent
    try:
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')
    except:
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Configuración por entorno
    if is_cloud_run:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--remote-debugging-port=9222")
        # webdriver-manager descargará chromedriver automáticamente
        service = Service(ChromeDriverManager().install())
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Scripts de evasión
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
            Object.defineProperty(navigator, 'headless', { get: () => false });
            window.chrome = { runtime: {} };
            delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
        '''
    })

    # Timeouts
    driver.set_page_load_timeout(15)
    driver.set_script_timeout(10)

    logger.info("✅ Driver optimizado iniciado")
    return driver


def scrape_property_fast(url: str) -> dict:
    """
    Versión RÁPIDA de scraping para una sola propiedad
    """
    # ===== DEFERRED IMPORTS =====
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    driver = None
    data = {
        'titulo': None,
        'direccion': None,
        'tipo': None,
        'precio': None,
        'superficie': None,
        'habitaciones': None,
        'banios': None,
        'caracteristica_propiedad': None,
        'amenidades': None,
        'caracteristicas': None,
        'planta': None,
        'descripcion': None,
        'fecha_publicacion': None,
        'url': url,
        'lat': None,
        'lon': None,
        'script_content': None,
        'fecha_consulta': time.strftime("%Y-%m-%d"),
        'error': False
    }

    try:
        start_time = time.time()
        logger.info(f"⬇️ Scrapeando: {url}")

        driver = get_stealth_driver()

        # NAVEGACIÓN
        driver.get(url)

        # ESPERA MÍNIMA
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            logger.warning(f"⚠️ H1 no encontrado en {url}")
            pass

        # SCROLL para cargar contenido
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(0.8)

        # VERIFICAR BLOQUEO RÁPIDO
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "403" in body_text or "404" in body_text or "ERROR" in body_text:
            logger.error(f"❌ Página bloqueada (403/404/ERROR): {url}")
            data['error'] = True
            return data

        # ===== SELECTORES MEJORADOS Y MÚLTIPLES =====
        
        # TÍTULO - múltiples variantes
        try:
            # Intenta varios selectores en orden de preferencia
            titulo_elem = None
            for selector in [
                (By.XPATH, "//h1"),
                (By.CSS_SELECTOR, "h1"),
                (By.CSS_SELECTOR, "[class*='title']"),
                (By.CSS_SELECTOR, "[class*='Title']"),
            ]:
                try:
                    titulo_elem = driver.find_element(*selector)
                    if titulo_elem and titulo_elem.text.strip():
                        data['titulo'] = titulo_elem.text.strip()
                        break
                except:
                    continue
            if data['titulo']:
                logger.info(f"✅ Título: {data['titulo'][:50]}")
        except Exception as e:
            logger.debug(f"Error extrayendo título: {e}")

        # PRECIO
        try:
            precio_elem = None
            for selector in [
                (By.XPATH, "//span[contains(text(), '$') or contains(text(), 'MXN')]"),
                (By.CSS_SELECTOR, "[class*='price']"),
                (By.CSS_SELECTOR, "[class*='Price']"),
            ]:
                try:
                    precio_elem = driver.find_element(*selector)
                    if precio_elem and precio_elem.text.strip():
                        data['precio'] = precio_elem.text.strip()
                        break
                except:
                    continue
            if data['precio']:
                logger.info(f"✅ Precio: {data['precio']}")
        except Exception as e:
            logger.debug(f"Error extrayendo precio: {e}")

        # DIRECCIÓN
        try:
            for selector in [
                (By.XPATH, "//span[@class and contains(@class, 'address')]"),
                (By.CSS_SELECTOR, "[class*='address']"),
                (By.CSS_SELECTOR, "[class*='Address']"),
            ]:
                try:
                    dir_elem = driver.find_element(*selector)
                    if dir_elem and dir_elem.text.strip():
                        data['direccion'] = dir_elem.text.strip()
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Error extrayendo dirección: {e}")

        # CARACTERÍSTICAS (Habitaciones, Baños, Superficie)
        try:
            for item in driver.find_elements(By.XPATH, "//div[contains(@class, 'detail') or contains(@class, 'feature')]"):
                text = item.text.strip().lower()
                
                if 'habitación' in text or 'bedroom' in text or 'recamara' in text:
                    data['habitaciones'] = item.text.strip()
                elif 'baño' in text or 'bathroom' in text:
                    data['banios'] = item.text.strip()
                elif 'm²' in text or 'superficie' in text or 'area' in text:
                    data['superficie'] = item.text.strip()
                elif 'tipo' in text or 'property' in text:
                    data['tipo'] = item.text.strip()
        except Exception as e:
            logger.debug(f"Error extrayendo características: {e}")

        # DESCRIPCIÓN
        try:
            for selector in [
                (By.XPATH, "//div[contains(@class, 'description')]"),
                (By.CSS_SELECTOR, "[class*='description']"),
                (By.CSS_SELECTOR, "[class*='Description']"),
                (By.XPATH, "//div[@id='description']"),
            ]:
                try:
                    desc_elem = driver.find_element(*selector)
                    if desc_elem and desc_elem.text.strip():
                        data['descripcion'] = desc_elem.text.strip()[:500]  # Limitar a 500 chars
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Error extrayendo descripción: {e}")

        # COORDENADAS - Buscar en scripts JSON
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            logger.debug(f"Buscando coordenadas en {len(scripts)} scripts")
            
            for script in scripts[:20]:  # Aumentar búsqueda a 20 scripts
                txt = script.get_attribute("innerHTML") or ""
                
                # Buscar patterns de lat/lon
                if "latitude" in txt or "longitude" in txt or "latlng" in txt.lower():
                    data['script_content'] = txt[:500]  # Guardar solo primeros 500 chars
                    
                    # Múltiples patterns
                    patterns = [
                        (r'latitude["\']?\s*:\s*["\']?([-\d.]+)["\']?', 'lat'),
                        (r'longitude["\']?\s*:\s*["\']?([-\d.]+)["\']?', 'lon'),
                        (r'"lat["\']?\s*:\s*["\']?([-\d.]+)["\']?', 'lat'),
                        (r'"lon["\']?\s*:\s*["\']?([-\d.]+)["\']?', 'lon'),
                    ]
                    
                    for pattern, key in patterns:
                        match = re.search(pattern, txt)
                        if match:
                            try:
                                value = float(match.group(1))
                                if key == 'lat':
                                    data['lat'] = value
                                else:
                                    data['lon'] = value
                                logger.info(f"✅ Encontrado {key}: {value}")
                            except:
                                pass
                    
                    if data['lat'] or data['lon']:
                        break
        except Exception as e:
            logger.debug(f"Error extrayendo coordenadas: {e}")

        elapsed = time.time() - start_time
        
        # Log resumen
        titulo_preview = (data['titulo'][:30] if data['titulo'] else 'Sin título')
        precio_preview = (data['precio'][:20] if data['precio'] else 'Sin precio')
        logger.info(f"✅ Completado en {elapsed:.1f}s | {titulo_preview} | {precio_preview}")

    except Exception as e:
        logger.error(f"❌ Error crítico en {url}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        data['error'] = True

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return data


def scrape_listados_parallel(property_links: List[str], max_workers: int = 3) -> List[dict]:
    """
    Versión PARALELIZADA para múltiples URLs
    """
    if not property_links:
        return []

    logger.info(f"🚀 Iniciando scraping paralelo de {len(property_links)} URLs con {max_workers} workers")

    all_data = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_property_fast, url): url for url in property_links}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result(timeout=30)
                all_data.append(data)
                logger.info(f"📊 Progreso: {len(all_data)}/{len(property_links)} completadas")
            except Exception as e:
                logger.error(f"❌ Error en {url}: {e}")
                all_data.append({
                    'url': url,
                    'error': True,
                    'fecha_consulta': time.strftime("%Y-%m-%d")
                })

    total = len(all_data)
    errores = sum(1 for item in all_data if item.get('error', False))
    exitos = total - errores
    logger.info(f"📊 Resumen: {exitos} éxitos, {errores} errores de {total} total")

    return all_data


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check y documentación básica"""
    return {
        "status": "ok",
        "service": "Lamudi Scraper API",
        "endpoints": [
            "/docs - Documentación interactiva",
            "/obtener-listados - GET lista de URLs",
            "/scrape-listados - POST para scrapear propiedades"
        ]
    }


@app.post("/obtener-listados")
async def endpoint_obtener_listados(
    cp: str,
    tipo_propiedad: str,
    precio: Optional[float] = None,
    max_listados: int = 6
):
    """
    Obtiene lista de URLs de propiedades en Lamudi
    
    **Parámetros:**
    - `cp`: Código postal (ej: "03100")
    - `tipo_propiedad`: Tipo de propiedad (ej: "departamento", "casa", "terreno")
    - `precio`: Precio opcional para filtrar (ej: 6000000)
    - `max_listados`: Número máximo de listados (default: 6)
    
    **Retorna:** Lista de URLs encontradas
    """
    # ===== DEFERRED IMPORTS =====
    import requests
    from bs4 import BeautifulSoup
    
    try:
        start_url = construir_url_cp(cp, tipo_propiedad, precio)
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        }

        enlaces = []
        visitados = set()
        url = start_url
        pagina = 1

        while url:
            logger.info(f"Página {pagina}: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            enlaces_pagina = []

            for a in soup.select(".snippet__content a[href]"):
                href = a.get("href")
                if href:
                    href = urljoin(url, href)
                    if href not in visitados:
                        visitados.add(href)
                        enlaces.append(href)
                        enlaces_pagina.append(href)

            logger.info(f"Links nuevos encontrados: {len(enlaces_pagina)}, Total acumulado: {len(enlaces)}")

            if len(enlaces) >= max_listados:
                logger.info(f"Se alcanzó el máximo solicitado ({max_listados})")
                return {
                    "status": "success",
                    "cp": cp,
                    "tipo_propiedad": tipo_propiedad,
                    "precio": precio,
                    "total_listados": len(enlaces[:max_listados]),
                    "listados": enlaces[:max_listados]
                }

            next_button = soup.select_one("#pagination-next")
            if next_button is None:
                logger.info("No hay más páginas")
                break

            href = next_button.get("href")
            if not href:
                logger.info("El botón siguiente no tiene href")
                break

            nueva_url = urljoin(url, href)
            if nueva_url == url:
                logger.info("La URL siguiente es la misma. Terminando")
                break

            url = nueva_url
            pagina += 1

        logger.info(f"Solo se encontraron {len(enlaces)} anuncios")
        return {
            "status": "success",
            "cp": cp,
            "tipo_propiedad": tipo_propiedad,
            "precio": precio,
            "total_listados": len(enlaces),
            "listados": enlaces
        }

    except Exception as e:
        logger.error(f"Error en obtener_listados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo listados: {str(e)}")


@app.post("/scrape-listados")
async def endpoint_scrape_listados(urls: List[str]):
    """
    Scrapea propiedades desde Lamudi en paralelo
    
    **Parámetros:**
    - `urls`: Lista de URLs de propiedades (ej: ["https://www.lamudi.com.mx/detalle/...", "https://www.lamudi.com.mx/detalle/..."])
    
    **Retorna:** Lista de diccionarios con datos de propiedades
    """
    try:
        if not urls or len(urls) == 0:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos una URL en 'urls'")
        
        logger.info(f"Iniciando scraping paralelo de {len(urls)} URLs")
        
        data = scrape_listados_parallel(urls, max_workers=3)

        total_exitosas = sum(1 for item in data if not item.get('error', False))
        logger.info(f"Scraping completado: {total_exitosas}/{len(data)} exitosas")
        
        return {
            "status": "success",
            "total_propiedades": len(data),
            "exitosas": total_exitosas,
            "propiedades": data
        }

    except Exception as e:
        logger.error(f"Error en scrape_listados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scrapeando: {str(e)}")


@app.get("/health")
async def health():
    """Health check para Cloud Run"""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
