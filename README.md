# 🎱 Juego de Billar con Control por Gestos

Juego de billar interactivo controlado mediante gestos de manos usando MediaPipe y simulación física con PyMunk.

## 📋 Requisitos Previos

- **Python 3.11** (Requerido - versión específica)
- Cámara web funcional
- Sistema operativo: Windows, macOS o Linux

## 🚀 Instalación

### Instalación en Windows (Python 3.11)

```powershell
# 1. Navegar a la carpeta del proyecto
cd billar

# 2. Si ya existe un entorno virtual, eliminarlo
Remove-Item -Recurse -Force .venv

# 3. Crear entorno virtual con Python 3.11 (REQUERIDO)
py -3.11 -m venv .venv

# 4. Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# 5. Actualizar pip e instalar dependencias (EN ESTE ORDEN)
py -m pip install --upgrade pip
py -m pip install mediapipe==0.10.9
py -m pip install numpy==1.26.4
py -m pip install opencv-python==4.10.0.84
py -m pip install pygame==2.6.1
py -m pip install pymunk
py -m pip install python-dotenv
```

### Instalación en macOS/Linux

```bash
cd billar
python3.11 -m venv .venv
source .venv/bin/activate
python3.11 -m pip install --upgrade pip
python3.11 -m pip install mediapipe==0.10.9
python3.11 -m pip install numpy==1.26.4
python3.11 -m pip install opencv-python==4.10.0.84
python3.11 -m pip install pygame==2.6.1
python3.11 -m pip install pymunk
python3.11 -m pip install python-dotenv
```

> **⚠️ CRÍTICO**: 
> - Debes usar **Python 3.11** (no 3.12, 3.13 o superior)
> - Instala los paquetes **en el orden indicado** para evitar conflictos de dependencias
> - Usa siempre `py -m pip` en lugar de solo `pip` para asegurar que usas Python 3.11

Las dependencias incluyen:
- `mediapipe==0.10.9` - Detección de manos
- `opencv-python==4.10.0.84` - Procesamiento de video
- `pygame==2.6.1` - Ventana del juego
- `pymunk==6.6.0` - Motor de física
- `numpy==1.26.4` - Cálculos numéricos
- `python-dotenv==1.0.0` - Variables de entorno

## 🎮 Cómo Ejecutar

**Asegúrate de que el entorno virtual esté activado** (deberías ver `(.venv)` en tu terminal).

**Windows:**
```powershell
py main_billar.py
```

**macOS/Linux:**
```bash
python3.11 main_billar.py
```

## 🎯 Controles por Gestos

El juego se controla mediante **dos manos** detectadas por la cámara web:

### 🖐️ Mano Izquierda - Control de Fases

1. **FASE IDLE (Mano abierta):**
   - Mueve la bola blanca con la mano derecha
   - Visualiza un preview del vector de dirección

2. **FASE 1 - Apuntar (Mano cerrada - puño):**
   - La bola blanca se fija en su posición
   - Mueve la mano derecha para seleccionar la dirección del tiro
   - El vector azul muestra hacia dónde apuntas

3. **FASE 2 - Potencia (Mano abierta de nuevo):**
   - La dirección queda fijada
   - Mueve la mano derecha para ajustar la potencia
   - **Movimiento rápido hacia arriba/abajo = DISPARAR**

### ✋ Mano Derecha - Control de Posición/Dirección/Potencia

- **En IDLE:** Controla la posición de la bola blanca
- **En FASE 1:** Controla la dirección del tiro
- **En FASE 2:** Controla la potencia y ejecuta el disparo con movimiento rápido

### ⌨️ Controles de Teclado

- **R** - Reiniciar el juego
- **Q** o **ESC** - Salir del juego

## 📁 Estructura del Proyecto

```
billar/
├── main_billar.py       # Archivo principal - ejecutar este
├── billiard_game.py     # Lógica del juego y física
├── hand_tracking.py     # Detección de gestos con MediaPipe
├── pymunk_config.py     # Configuración del motor de física
├── requirements.txt     # Dependencias del proyecto
└── .venv/              # Entorno virtual (crear con Python 3.11)
```

## 🔧 Solución de Problemas

### ❌ Error: "Could not find a version that satisfies the requirement mediapipe==0.10.9"

**Causa**: Estás usando una versión de Python incorrecta (probablemente Python 3.12, 3.13 o 3.14).

**Solución**:
```powershell
# 1. Verifica tu versión de Python
py -3.11 --version  # Debe mostrar Python 3.11.x

# 2. Si no tienes Python 3.11, descárgalo de python.org

# 3. Elimina el entorno virtual existente
deactivate  # Si está activo
Remove-Item -Recurse -Force .venv

# 4. Crea nuevo entorno con Python 3.11 específicamente
py -3.11 -m venv .venv

# 5. Activa y reinstala
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install mediapipe==0.10.9
# ... resto de dependencias
```

### No tengo Python 3.11 instalado
- Descarga Python 3.11 desde [python.org](https://www.python.org/downloads/)
- Durante la instalación, marca "Add Python to PATH"
- Verifica la instalación: `py -3.11 --version`

### La cámara no se detecta
- Verifica que tu cámara web esté conectada y funcionando
- Cierra otras aplicaciones que puedan estar usando la cámara
- En Windows, verifica los permisos de la cámara en Configuración

### Error al importar módulos
```bash
# Asegúrate de que el entorno virtual esté activado y uses Python 3.11
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### El juego va lento
- Cierra otras aplicaciones para liberar recursos
- Asegúrate de tener buena iluminación para mejor detección de manos
- Reduce la resolución de la cámara si es necesario

### Las manos no se detectan bien
- Mejora la iluminación del ambiente
- Asegúrate de que tus manos estén completamente visibles en la cámara
- Mantén las manos a una distancia apropiada (30-60 cm de la cámara)
- Evita fondos con colores similares al tono de piel

## 💡 Consejos de Juego

1. **Posiciónate correctamente:** Mantén ambas manos visibles en el cuadro de la cámara
2. **Gestos claros:** Haz puño cerrado bien definido para cambiar de fase
3. **Movimientos suaves:** Mueve las manos de forma controlada para mejor precisión
4. **Disparo rápido:** Para ejecutar el tiro, haz un movimiento rápido vertical con la mano derecha
5. **Espera entre turnos:** Permite que todas las bolas se detengan antes del siguiente tiro

## 🎓 Tecnologías Utilizadas

- **MediaPipe:** Framework de Google para detección de manos en tiempo real
- **OpenCV:** Procesamiento de video y visualización
- **PyMunk:** Motor de física 2D basado en Chipmunk
- **Pygame:** Renderizado de la ventana del juego
- **NumPy:** Cálculos matemáticos y vectoriales

## 📝 Notas

- El juego requiere una cámara web conectada para funcionar
- Se recomienda buena iluminación para mejor detección de gestos
- El motor de física está calibrado para simular comportamiento realista de bolas de billar

## 👨‍💻 Autor

Proyecto desarrollado como parte del curso SIPC

---

¡Disfruta del juego! 🎱✨
