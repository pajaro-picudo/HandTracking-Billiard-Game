"""
Configuración de PyMunk para el juego de billar
"""

# Física del espacio
GRAVITY = (0, 0)  # Sin gravedad (billar es horizontal)
DAMPING = 0.95  # Amortiguamiento del espacio

# Propiedades de las bolas
BALL_RADIUS = 15  # Radio visual de las bolas
BALL_MASS = 1  # Masa de cada bola
BALL_ELASTICITY = 0.95  # Rebote (0=sin rebote, 1=rebote perfecto)
BALL_FRICTION = 0.5  # Fricción entre bolas

# Propiedades de las paredes
WALL_ELASTICITY = 0.95  # Rebote en paredes
WALL_FRICTION = 0.7  # Fricción con paredes

# Simulación
SIMULATION_DT = 1/60  # Delta time por frame (60 FPS)
SIMULATION_ITERATIONS = 5  # Iteraciones de precisión de PyMunk
