# TETRIS FÍSICO CON CONTROL DE GESTOS

Proyecto universitario que implementa un juego tipo Tetris con física real usando Pymunk, controlado mediante gestos de dos manos detectados con MediaPipe.

---

## OBJETIVO DEL PROYECTO

Desarrollar un sistema interactivo que integre:
- **Visión por computadora** (MediaPipe)
- **Simulación física realista** (Pymunk)
- **Control gestual avanzado** (dos manos simultáneas)
- **Renderizado en tiempo real** (Pygame)

---

## JUSTIFICACIÓN ACADÉMICA

### ¿Por qué MediaPipe?
MediaPipe Hands es una solución de Google basada en redes neuronales que detecta 21 landmarks por mano en tiempo real. Ventajas:
- Detección robusta bajo diferentes condiciones de iluminación
- Diferenciación precisa entre mano izquierda y derecha
- Procesamiento eficiente (~30-60 FPS)
- API simple y bien documentada

### ¿Por qué Pymunk?
Pymunk es un motor de física 2D basado en Chipmunk Physics. Beneficios:
- Simulación precisa de colisiones y gravedad
- Manejo de cuerpos rígidos y articulaciones
- Integración nativa con Pygame
- Ideal para prototipos académicos

### ¿Por qué dos manos?
El uso de dos manos permite:
1. **División de responsabilidades**: Una mano para posición, otra para rotación
2. **Gestos complejos**: Combinaciones que enriquecen la interacción
3. **Demostración técnica**: Tracking simultáneo de múltiples objetos
4. **Experiencia inmersiva**: Control más natural e intuitivo

---

## ARQUITECTURA DEL SISTEMA

```
┌─────────────┐
│   CÁMARA    │
│  (OpenCV)   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  HandTracker    │
│  (MediaPipe)    │
│ - Detecta manos │
│ - 21 landmarks  │
│ - Suavizado     │
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│ GestureRecognizer    │
│ - Posición X         │
│ - Rotación muñeca    │
│ - Detección apertura │
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│  TetrisGame      │
│ - Lógica juego   │
│ - Control piezas │
│ - Puntuación     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ PhysicsEngine    │
│  (Pymunk)        │
│ - Gravedad       │
│ - Colisiones     │
│ - Fricción       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   RENDERIZADO    │
│   (Pygame)       │
└──────────────────┘
```

---

## ESTRUCTURA DE MÓDULOS

### 1. `hand_tracking.py`
**Responsabilidad**: Detección y seguimiento de manos

**Funcionalidades**:
- Inicializa MediaPipe Hands con configuración optimizada
- Procesa frames de cámara en BGR → RGB
- Diferencia entre mano izquierda y derecha
- Aplica suavizado mediante media móvil (buffer de 5 frames)
- Dibuja landmarks para visualización

**Métodos clave**:
- `process_frame()`: Detecta manos en cada frame
- `get_smoothed_position()`: Obtiene posición suavizada de muñeca

### 2. `gesture_recognition.py`
**Responsabilidad**: Interpretación de gestos

**Algoritmos implementados**:

#### Detección de mano abierta
```python
# Criterio: Punta de dedo más alta que nudillo medio
for cada dedo:
    if punta.y < nudillo.y - umbral:
        dedo_extendido += 1

mano_abierta = (dedos_extendidos >= 4)
```

#### Cálculo de rotación
```python
# Vector muñeca → nudillo dedo medio
dx = nudillo.x - muñeca.x
dy = nudillo.y - muñeca.y
ángulo = atan2(dy, dx)

# Detectar cambio acumulado > umbral
if |rotación_acumulada| > 30°:
    rotar_pieza()
```

**Umbrales calibrados**:
- Apertura de mano: 4/5 dedos extendidos
- Rotación: 30 grados acumulados
- Suavizado: ventana de 5 frames

### 3. `physics_engine.py`
**Responsabilidad**: Simulación física con Pymunk

**Componentes**:
- **Space**: Contenedor del mundo físico con gravedad configurable
- **Boundaries**: Paredes estáticas (suelo y laterales)
- **Bodies**: Cuerpos rígidos con masa, momento de inercia
- **Shapes**: Geometrías de colisión (polígonos)

**Parámetros físicos**:
```python
Masa por bloque: 1 kg
Fricción: 0.7
Elasticidad: 0.1
Gravedad: 900 px/s² (cuando se activa)
```

**Creación de pieza Tetris**:
1. Crear un único cuerpo rígido principal
2. Añadir múltiples formas (polígonos) como componentes
3. Formas unidas comparten el mismo cuerpo → rotan juntas

### 4. `tetris_game.py`
**Responsabilidad**: Lógica del juego

**Estados del juego**:
- **Controlada**: Pieza bajo control manual (gravedad OFF)
- **Cayendo**: Pieza liberada con gravedad activa
- **Asentada**: Pieza en reposo (velocidad < umbral)

**Ciclo de vida de una pieza**:
```
Spawn → Control manual → Drop → Caída física → Asentamiento → Nueva pieza
```

**Detección de asentamiento**:
```python
if |velocidad_y| < 10 px/s:
    pieza_asentada = True
    spawn_nueva_pieza(delay=1s)
```

### 5. `main.py`
**Responsabilidad**: Integración y loop principal

**Flujo de ejecución**:
```python
while juego_activo:
    1. Capturar frame de cámara
    2. Detectar manos con MediaPipe
    3. Reconocer gestos
    4. Aplicar controles al juego
    5. Actualizar física (Pymunk.step)
    6. Renderizar juego (Pygame)
    7. Mostrar cámara con landmarks (OpenCV)
    8. Mantener 60 FPS
```

---

## DETECCIÓN DE GESTOS - DETALLES TÉCNICOS

### Landmarks utilizados (MediaPipe)

```
Índices relevantes:
0:  Muñeca (WRIST)
4:  Pulgar punta
8:  Índice punta
12: Medio punta
16: Anular punta
20: Meñique punta
2,6,10,14,18: Nudillos medios (PIP joints)
9:  Nudillo dedo medio (MCP)
```

### Gestos implementados

#### 1. Mover pieza horizontalmente (Mano Izquierda)
```python
# Coordenada X de muñeca (normalizada 0-1)
x = muñeca.x * ancho_pantalla

# Limitar dentro de márgenes
x = clamp(x, margen_izq, margen_der)

# Actualizar posición del cuerpo físico
pieza.position = (x, pieza.position.y)
pieza.velocity = (0, 0)  # Anular inercia
```

#### 2. Rotar pieza (Mano Derecha)
```python
# Vector muñeca → nudillo medio
vector = (nudillo_medio - muñeca)
ángulo_actual = atan2(vector.y, vector.x)

# Calcular diferencia angular
Δángulo = ángulo_actual - ángulo_previo

# Normalizar a [-180°, 180°]
if Δángulo > 180°: Δángulo -= 360°
if Δángulo < -180°: Δángulo += 360°

# Acumular rotación
rotación_acumulada += Δángulo

# Activar rotación cada 30°
if |rotación_acumulada| >= 30°:
    pieza.angle += 90° * signo(rotación)
    rotación_acumulada = 0
```

#### 3. Soltar pieza (Ambas Manos Abiertas)
```python
# Detectar dedos extendidos
for dedo in [pulgar, índice, medio, anular, meñique]:
    if punta_y < nudillo_y - 0.02:
        dedos_extendidos += 1

izq_abierta = (dedos_extendidos_izq >= 4)
der_abierta = (dedos_extendidos_der >= 4)

if izq_abierta AND der_abierta AND not gesto_previo:
    activar_gravedad()
    liberar_pieza()
```

---

## INTEGRACIÓN TETRIS + FÍSICA

### Desafíos y soluciones

**Problema 1**: Tetris clásico usa grid discreto, física usa coordenadas continuas

**Solución**: 
- Piezas son cuerpos rígidos continuos
- No hay grid → movimiento fluido
- Colisiones manejadas por Pymunk

**Problema 2**: Rotación en Tetris es discreta (90°), física es continua

**Solución**:
- Acumular rotación de muñeca
- Aplicar rotación de 90° solo cuando se supera umbral
- Resetear acumulador tras cada rotación

**Problema 3**: Control manual vs física automática

**Solución**:
- **Modo Control**: Gravedad = 0, posición forzada por gestos
- **Modo Caída**: Gravedad = 900, física toma el control
- Transición con gesto de ambas manos abiertas

**Problema 4**: Eliminar filas completas con física

**Solución** (simplificada en este prototipo):
- Detectar bloques en misma altura Y
- Contar bloques en esa fila
- Si fila completa → eliminar cuerpos del espacio
- Bloques superiores caen por gravedad

---

## REQUISITOS E INSTALACIÓN

### Dependencias

```bash
pip install mediapipe opencv-python pymunk pygame numpy
```

**Versiones recomendadas**:
- Python 3.8+
- mediapipe >= 0.10.0
- opencv-python >= 4.8.0
- pymunk >= 6.5.0
- pygame >= 2.5.0

### Ejecución

```bash
python scripts/main.py
```

---

## CONTROLES DEL JUEGO

### Mano Izquierda (Control de Posición)
- Mover la mano horizontalmente para posicionar la pieza
- La coordenada X de la muñeca controla la posición X de la pieza

### Mano Derecha (Control de Rotación)
- Girar la muñeca para rotar la pieza
- Cada 30° de rotación acumulada → pieza rota 90°

### Ambas Manos (Soltar Pieza)
- Abrir completamente ambas manos
- La pieza se libera y cae con gravedad activa

### Teclas (emergencia)
- No hay teclas de control principal
- El juego se controla exclusivamente por gestos

---

## EXPLICACIÓN PARA PRESENTACIÓN

### Introducción (2 min)
"Nuestro proyecto combina visión por computadora, física simulada y control gestual para crear una experiencia de Tetris única. Utilizamos MediaPipe de Google para detectar 21 puntos en cada mano, Pymunk para simular colisiones realistas, y Pygame para renderizar a 60 FPS."

### Demostración Técnica (3 min)
1. Mostrar ventana de cámara con landmarks
2. Demostrar mano izquierda moviendo pieza
3. Demostrar rotación con mano derecha
4. Soltar pieza con ambas manos abiertas
5. Mostrar física de colisiones

### Aspectos Académicos (3 min)
- **Visión por computadora**: Tracking robusto con redes neuronales
- **Procesamiento de señales**: Suavizado con media móvil
- **Geometría computacional**: Cálculo de ángulos y vectores
- **Simulación física**: Integración de Verlet, detección de colisiones
- **Sistemas en tiempo real**: Sincronización de múltiples módulos

### Decisiones de Diseño (2 min)
- ¿Por qué dos manos? División de responsabilidades
- ¿Por qué Pymunk? Física realista vs Tetris tradicional
- ¿Por qué gestos vs teclado? Interacción natural e innovadora

---

## MEJORAS FUTURAS

### Corto plazo
1. **Detección de filas completas**: Algoritmo robusto para eliminar bloques
2. **Sistema de puntuación**: Puntos por líneas, combos, velocidad
3. **Niveles de dificultad**: Incrementar velocidad de caída
4. **Menú de inicio**: Calibración de gestos, selección de opciones

### Mediano plazo
5. **Gestos adicionales**: Pausar con mano cerrada, acelerar caída
6. **Vista previa**: Mostrar siguiente pieza
7. **Efectos visuales**: Partículas, animaciones de eliminación
8. **Sonido**: Música de fondo, efectos de colisión

### Largo plazo (investigación)
9. **Reconocimiento de pose completa**: MediaPipe Pose para controlar con cuerpo entero
10. **Múltiples jugadores**: Dos cámaras, competencia 1v1
11. **Aprendizaje por refuerzo**: IA que aprende a jugar observando gestos
12. **Realidad aumentada**: Proyectar piezas sobre superficie real

---

## PROBLEMAS CONOCIDOS Y LIMITACIONES

### Técnicas
- **Iluminación**: MediaPipe requiere buena iluminación para detección precisa
- **Latencia**: ~33ms (30 FPS) de delay entre gesto y acción
- **Calibración**: Umbral de rotación puede necesitar ajuste por usuario
- **Filas completas**: Implementación simplificada en esta versión

### Usabilidad
- **Curva de aprendizaje**: Usuarios necesitan práctica para coordinar ambas manos
- **Fatiga**: Mantener brazos levantados puede cansar después de varios minutos
- **Precisión**: Movimiento fino es más difícil que con teclado

### Soluciones propuestas
- Calibración automática de umbrales por usuario
- Modo de práctica con gravedad reducida
- Soporte para sentado con brazos apoyados

---

## CONCLUSIONES ACADÉMICAS

Este proyecto demuestra:

1. **Integración multiplataforma**: OpenCV, MediaPipe, Pymunk y Pygame trabajando juntos
2. **Procesamiento en tiempo real**: Pipeline completo a 30-60 FPS
3. **Control intuitivo**: Gestos naturales vs input digital
4. **Simulación física**: Comportamiento realista de objetos
5. **Arquitectura modular**: Código organizado y mantenible

**Aplicaciones futuras**:
- Rehabilitación física con gamificación
- Interfaces gestuales para espacios estériles (quirófanos)
- Educación interactiva
- Accesibilidad para usuarios con movilidad reducida

---

## REFERENCIAS

- **MediaPipe Hands**: https://google.github.io/mediapipe/solutions/hands
- **Pymunk Documentation**: http://www.pymunk.org/
- **Pygame Tutorial**: https://www.pygame.org/docs/
- **OpenCV Python**: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html

---

## AUTORES Y LICENCIA

Proyecto académico desarrollado para demostración de:
- Visión por computadora
- Simulación física
- Interacción gestual
- Desarrollo de videojuegos

Licencia: MIT (Uso educativo)

---

## CONTACTO

Para preguntas sobre la implementación, consultar los comentarios en el código fuente.

**¡Disfruta jugando Tetris con tus manos!** 🎮✋🤚
