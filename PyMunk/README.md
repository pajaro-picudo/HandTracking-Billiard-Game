# PyMunk + MediaPipe Hands

Este proyecto usa MediaPipe para detectar la mano y controla un círculo en Pygame a través de Pymunk.

## Requisitos

- Python 3.10+ (recomendado)
- Windows (PowerShell)

## Instalación

```powershell
# Desde la carpeta PyMunk
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

## Configuración (.env)
Edita el archivo `.env` para ajustar parámetros:

- MODEL_PATH: ruta al modelo de MediaPipe Hands (por defecto `hand_landmarker.task`).
- CAMERA_INDEX: índice de la cámara (0 por defecto).
- SCREEN_WIDTH / SCREEN_HEIGHT: tamaño de la ventana.
- CIRCLE_RADIUS: radio del círculo.
- GRAVITY_X / GRAVITY_Y: gravedad en Pymunk.
- DEBUG: `true`/`false` para imprimir coordenadas de la punta del índice.

## Ejecución

```powershell
# Activar entorno y correr el script
.\.venv\Scripts\Activate.ps1
py pymunk_hands_basics.py
```

## Notas
- Si usas otra cámara, prueba cambiando `CAMERA_INDEX`.
- Para rendimiento, mantén la ventana en tamaño moderado.
