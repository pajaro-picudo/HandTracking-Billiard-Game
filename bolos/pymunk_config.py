"""
Configuración de PyMunk para el juego de billar
"""

# Física del espacio
GRAVITY = (0, 0)  # Sin gravedad (billar es horizontal)
DAMPING = 0.88  # ANTES 0.70 → AHORA 0.88 (fricción brutal)

# Propiedades de las bolas
BALL_RADIUS = 15  # Radio visual de las bolas
BALL_MASS = 0.12  # ANTES 0.17 → AHORA 0.12 (120g más ágil)
BALL_ELASTICITY = 0.75  # Rebote reducido
BALL_FRICTION = 1.1  # ANTES 0.8 → AHORA 1.1 (máximo agarre)

# Propiedades de las paredes
WALL_ELASTICITY = 0.75  # ANTES 0.65 → AHORA 0.75 (rebote mínimo)
WALL_FRICTION = 1.2  # ANTES 0.9 → AHORA 1.2 (paredes agarran más)

# Simulación
SIMULATION_DT = 1/60  # Delta time por frame (60 FPS)
SIMULATION_ITERATIONS = 20  # ANTES 5 → AHORA 20 (mayor precisión)
