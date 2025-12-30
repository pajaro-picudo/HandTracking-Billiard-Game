import pygame
import pymunk
import pymunk.pygame_util
import random
import math
import numpy as np

class TerrainGenerator:
    """
    Generador de terreno procedural infinito con laderas.
    """
    
    def __init__(self, space, screen_width, screen_height):
        self.space = space
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ground_y = screen_height - 100
        self.segments = []
        self.segment_width = 100
        self.last_x = 0
        self.last_y = self.ground_y
        
        # Generar terreno inicial
        for i in range(15):
            self.add_segment()
    
    def add_segment(self):
        """Añade un nuevo segmento de terreno."""
        # Variación aleatoria de altura
        height_change = random.randint(-80, 80)
        new_y = max(200, min(self.screen_height - 50, self.last_y + height_change))
        
        # Crear segmento de suelo
        p1 = (self.last_x, self.last_y)
        p2 = (self.last_x + self.segment_width, new_y)
        
        segment = pymunk.Segment(self.space.static_body, p1, p2, 5)
        segment.friction = 0.9
        segment.collision_type = 1
        self.space.add(segment)
        
        self.segments.append({
            'segment': segment,
            'p1': p1,
            'p2': p2
        })
        
        self.last_x += self.segment_width
        self.last_y = new_y
    
    def update(self, camera_x):
        """Actualiza el terreno basado en la posición de la cámara."""
        # Eliminar segmentos que quedaron atrás
        while self.segments and self.segments[0]['p2'][0] < camera_x - 200:
            old = self.segments.pop(0)
            self.space.remove(old['segment'])
        
        # Añadir nuevos segmentos por delante
        while self.last_x < camera_x + self.screen_width + 200:
            self.add_segment()
    
    def draw(self, screen, camera_x):
        """Dibuja el terreno."""
        for seg_data in self.segments:
            p1 = seg_data['p1']
            p2 = seg_data['p2']
            
            # Ajustar por la cámara
            screen_p1 = (int(p1[0] - camera_x), int(p1[1]))
            screen_p2 = (int(p2[0] - camera_x), int(p2[1]))
            
            # Dibujar línea del terreno
            pygame.draw.line(screen, (100, 200, 100), screen_p1, screen_p2, 10)
            
            # Rellenar debajo del terreno
            points = [
                screen_p1,
                screen_p2,
                (screen_p2[0], self.screen_height),
                (screen_p1[0], self.screen_height)
            ]
            pygame.draw.polygon(screen, (60, 120, 60), points)


class Car:
    """
    Coche controlado por gestos de manos.
    """
    
    def __init__(self, space, x, y):
        self.space = space
        
        # Crear carrocería del coche
        mass = 10
        size = (80, 40)
        moment = pymunk.moment_for_box(mass, size)
        self.body = pymunk.Body(mass, moment)
        self.body.position = x, y
        
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.friction = 0.7
        self.shape.collision_type = 2
        
        space.add(self.body, self.shape)
        
        # Crear ruedas
        self.wheels = []
        wheel_positions = [(-30, 25), (30, 25)]
        
        for wx, wy in wheel_positions:
            wheel_body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 12))
            wheel_body.position = self.body.position + (wx, wy)
            
            wheel_shape = pymunk.Circle(wheel_body, 12)
            wheel_shape.friction = 1.5
            wheel_shape.collision_type = 3
            
            space.add(wheel_body, wheel_shape)
            
            # Unir rueda al cuerpo con un joint
            joint = pymunk.PinJoint(self.body, wheel_body, (wx, wy), (0, 0))
            damped_spring = pymunk.DampedSpring(
                self.body, wheel_body,
                (wx, wy), (0, 0),
                30, 500, 10
            )
            
            space.add(joint, damped_spring)
            
            self.wheels.append({
                'body': wheel_body,
                'shape': wheel_shape,
                'joint': joint,
                'spring': damped_spring
            })
        
        self.max_speed = 800
        self.acceleration = 0
        self.rotation_speed = 0
    
    def apply_throttle(self, throttle):
        """
        Aplica aceleración al coche.
        
        Args:
            throttle: Valor entre 0 y 1
        """
        self.acceleration = throttle * self.max_speed
        
        # Aplicar fuerza a las ruedas traseras
        direction = pymunk.Vec2d(1, 0).rotated(self.body.angle)
        for wheel in self.wheels:
            wheel['body'].apply_force_at_world_point(
                direction * self.acceleration * 0.5,
                wheel['body'].position
            )
    
    def apply_rotation(self, rotation):
        """
        Aplica rotación al coche sobre sí mismo.
        
        Args:
            rotation: Ángulo en grados
        """
        # Convertir a torque
        torque = rotation * 300
        self.body.torque = torque
    
    def update(self):
        """Actualiza el estado del coche."""
        # Limitar velocidad máxima
        if self.body.velocity.length > self.max_speed:
            self.body.velocity = self.body.velocity.normalized() * self.max_speed
    
    def draw(self, screen, camera_x):
        """Dibuja el coche."""
        # Dibujar carrocería
        vertices = [self.body.local_to_world(v) for v in self.shape.get_vertices()]
        screen_vertices = [(int(v.x - camera_x), int(v.y)) for v in vertices]
        pygame.draw.polygon(screen, (200, 50, 50), screen_vertices)
        pygame.draw.polygon(screen, (100, 20, 20), screen_vertices, 3)
        
        # Dibujar ruedas
        for wheel in self.wheels:
            pos = wheel['body'].position
            screen_pos = (int(pos.x - camera_x), int(pos.y))
            pygame.draw.circle(screen, (40, 40, 40), screen_pos, 12)
            pygame.draw.circle(screen, (20, 20, 20), screen_pos, 12, 2)
    
    def get_position(self):
        """Obtiene la posición del coche."""
        return self.body.position


class CarGameEngine:
    """
    Motor del juego de coche 2D.
    """
    
    def __init__(self, screen_width=1200, screen_height=600):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Coche 2D - Control por Gestos")
        
        # Física
        self.space = pymunk.Space()
        self.space.gravity = (0, 500)
        
        # Generar terreno
        self.terrain = TerrainGenerator(self.space, screen_width, screen_height)
        
        # Crear coche
        self.car = Car(self.space, 200, 300)
        
        # Cámara
        self.camera_x = 0
        
        # Estado del juego
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 1/60
        
        # Controles
        self.throttle = 0
        self.rotation = 0
    
    def set_throttle(self, value):
        """Establece el acelerador (0-1)."""
        self.throttle = max(0, min(1, value))
    
    def set_rotation(self, angle):
        """Establece la rotación del coche (-180 a 180 grados)."""
        self.rotation = angle
    
    def update(self):
        """Actualiza la física del juego."""
        # Aplicar controles al coche
        self.car.apply_throttle(self.throttle)
        self.car.apply_rotation(self.rotation)
        
        # Actualizar física
        self.space.step(self.dt)
        self.car.update()
        
        # Actualizar cámara (seguir al coche)
        car_pos = self.car.get_position()
        self.camera_x = car_pos.x - self.screen_width // 3
        
        # Actualizar terreno
        self.terrain.update(self.camera_x)
    
    def draw(self):
        """Dibuja el juego."""
        # Fondo (cielo)
        self.screen.fill((135, 206, 235))
        
        # Dibujar terreno
        self.terrain.draw(self.screen, self.camera_x)
        
        # Dibujar coche
        self.car.draw(self.screen, self.camera_x)
        
        # Dibujar HUD
        self.draw_hud()
    
    def draw_hud(self):
        """Dibuja la interfaz de usuario."""
        font = pygame.font.Font(None, 36)
        
        # Velocidad
        speed = self.car.body.velocity.length
        speed_text = font.render(f"Velocidad: {int(speed)} px/s", True, (255, 255, 255))
        self.screen.blit(speed_text, (10, 10))
        
        # Acelerador
        throttle_text = font.render(f"Acelerador: {int(self.throttle * 100)}%", True, (255, 255, 255))
        self.screen.blit(throttle_text, (10, 50))
        
        # Rotación
        rotation_text = font.render(f"Rotación: {int(self.rotation)}°", True, (255, 255, 255))
        self.screen.blit(rotation_text, (10, 90))
        
        # Instrucciones
        small_font = pygame.font.Font(None, 24)
        instructions = [
            "Mano Derecha: Cerrar para acelerar",
            "Mano Izquierda: Girar para rotar coche",
            "Presiona Q para salir"
        ]
        for i, text in enumerate(instructions):
            inst_text = small_font.render(text, True, (255, 255, 255))
            self.screen.blit(inst_text, (10, self.screen_height - 90 + i * 25))
    
    def handle_events(self):
        """Maneja eventos de pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reiniciar coche
                    self.car.body.position = (200, 300)
                    self.car.body.velocity = (0, 0)
                    self.car.body.angle = 0
    
    def run_frame(self):
        """Ejecuta un frame del juego."""
        self.handle_events()
        self.update()
        self.draw()
        pygame.display.flip()
        self.clock.tick(60)
        return self.running
    
    def cleanup(self):
        """Limpia recursos."""
        pygame.quit()
