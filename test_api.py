"""
Script de prueba rápida para la API de Lamudi Scraper
Ejecutar con: python test_api.py
"""

import requests
import json
from time import sleep

# URL base (cambiar si está en producción)
BASE_URL = "http://localhost:8080"

def test_health():
    """Prueba health check"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

def test_root():
    """Prueba endpoint raíz"""
    print("\n" + "="*60)
    print("TEST 2: Root Endpoint")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Error: {e}")

def test_obtener_listados():
    """Prueba obtener listados"""
    print("\n" + "="*60)
    print("TEST 3: Obtener Listados")
    print("="*60)
    try:
        payload = {
            "cp": "03100",
            "tipo_propiedad": "departamento",
            "precio": 6000000,
            "max_listados": 3
        }
        print(f"Parámetros: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/obtener-listados",
            json=payload,
            timeout=60
        )
        
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"Se encontraron {data['total_listados']} listados")
        
        if data['listados']:
            print("\nPrimeros 2 URLs:")
            for i, url in enumerate(data['listados'][:2], 1):
                print(f"  {i}. {url}")
        
        return data['listados']
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_scrape_listados(listados):
    """Prueba scraping de propiedades"""
    print("\n" + "="*60)
    print("TEST 4: Scrape Listados (Sequential)")
    print("="*60)
    
    if not listados:
        print("⚠️ No hay listados para scrapear. Ejecuta test_obtener_listados primero.")
        return
    
    try:
        payload = {
            "cp": "03100",
            "tipo_propiedad": "departamento",
            "precio": 6000000,
            "max_listados": 2,
            "mode": "sequential"  # Usar sequential para pruebas (más lento pero más estable)
        }
        
        print(f"Parámetros: {json.dumps(payload, indent=2)}")
        print("⏳ Scrapeando propiedades (esto puede tomar varios minutos)...")
        
        response = requests.post(
            f"{BASE_URL}/scrape-listados",
            json=payload,
            timeout=300  # 5 minutos de timeout
        )
        
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        
        print(f"\nSe scrapearon {data['total_propiedades']} propiedades")
        
        if data['propiedades']:
            print("\n📋 Primera propiedad:")
            prop = data['propiedades'][0]
            print(json.dumps({
                "titulo": prop.get('titulo'),
                "precio": prop.get('precio'),
                "superficie": prop.get('superficie'),
                "habitaciones": prop.get('habitaciones'),
                "banios": prop.get('banios'),
                "direccion": prop.get('direccion'),
                "error": prop.get('error'),
                "url": prop.get('url')
            }, indent=2, ensure_ascii=False))
            
            print("\n💾 Guardando resultados en propiedades_test.json...")
            with open('propiedades_test.json', 'w', encoding='utf-8') as f:
                json.dump(data['propiedades'], f, indent=2, ensure_ascii=False)
            print("✅ Guardado")
    
    except requests.exceptions.Timeout:
        print("❌ Timeout: La solicitud tardó demasiado")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Ejecutar todos los tests"""
    print("\n" + "🚀"*30)
    print("PRUEBAS DE API - Lamudi Scraper")
    print("🚀"*30)
    
    print(f"\nURL Base: {BASE_URL}")
    print("Asegúrate de que la API esté corriendo (python main.py)")
    
    # Pruebas básicas
    test_health()
    sleep(1)
    test_root()
    sleep(1)
    
    # Obtener listados
    listados = test_obtener_listados()
    sleep(2)
    
    # Scrapear (opcional, comentar si no quieres esperar)
    # test_scrape_listados(listados)
    
    print("\n" + "="*60)
    print("✅ Tests completados")
    print("="*60)
    print("\nPróximos pasos:")
    print("1. Ver documentación en: http://localhost:8080/docs")
    print("2. Descomentar test_scrape_listados() si quieres probar scraping")
    print("3. Revisar propiedades_test.json para resultados")

if __name__ == "__main__":
    main()
