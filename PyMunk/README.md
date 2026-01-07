# Juego de Billar con Detección de Manos

## Requisitos

- **Python 3.11** (recomendado - NO usar Python 3.14)
- Windows (PowerShell)

## Instalación

```powershell
# Desde la carpeta bolos
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

## Ejecución

```powershell
.\.venv\Scripts\Activate.ps1
py main_billar.py
```

## Solución de problemas

**Error: "module 'mediapipe' has no attribute 'solutions'"**
- Estás usando Python 3.14. Reinstala con Python 3.11:
  ```powershell
  Remove-Item -Recurse -Force .venv
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  py -m pip install -r requirements.txt
  ```

**Error: No se encuentra Python 3.11**
- Descarga e instala desde: https://www.python.org/downloads/release/python-3118/

<!-- filepath: c:\Users\alore\Desktop\CodigosPrueba\CodigosPrueba\bolos\setup.ps1 -->
# Script de configuración automática
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Write-Host "Instalación completada. Ejecuta: py main_billar.py" -ForegroundColor Green

.\setup.ps1
py main_billar.py