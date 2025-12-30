import cv2
import numpy as np
import math
import pymunk
from pymunk_config import *

class BilliardGame:
    def __init__(self, width=1200, height=800):
        self.width = width
        self.height = height
        
        # Definir mesa en perspectiva
        self.table_3d = {
            'near_left': (150, 550),
            'near_right': (1050, 550),
            'far_left': (250, 150),
            'far_right': (950, 150)
        }
        
        # PYMUNK: Crear espacio de física
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY
        self.space.damping = DAMPING
        self.space.iterations = SIMULATION_ITERATIONS
        
        # Diccionarios para bolas PyMunk
        self.ball_bodies = {}  # {number: body}
        self.ball_shapes = {}  # {number: shape}
        self.ball_colors = {}  # {number: color}
        
        self.pockets = []
        self.init_pockets()
        
        # Referencias para la bola blanca
        self.cue_ball_body = None
        
        # Estado del juego (NO TOCAR - usado por gestos)
        self.aiming = False
        self.aim_start = None
        self.aim_end = None
        self.score = 0
        
        self.show_aim_vector = False
        self.aim_vector_start = None
        self.aim_vector_end = None
        
        # Crear paredes y bolas con PyMunk
        self.create_walls()
        self.initialize_balls()
    
    def init_pockets(self):
        """Inicializa las troneras en las esquinas y centros"""
        self.pockets = [
            {'pos': self.table_3d['near_left'], 'radius': 25},
            {'pos': self.table_3d['near_right'], 'radius': 25},
            {'pos': self.table_3d['far_left'], 'radius': 20},
            {'pos': self.table_3d['far_right'], 'radius': 20},
        ]
        
        near_center = (
            (self.table_3d['near_left'][0] + self.table_3d['near_right'][0]) // 2,
            (self.table_3d['near_left'][1] + self.table_3d['near_right'][1]) // 2
        )
        far_center = (
            (self.table_3d['far_left'][0] + self.table_3d['far_right'][0]) // 2,
            (self.table_3d['far_left'][1] + self.table_3d['far_right'][1]) // 2
        )
        
        self.pockets.append({'pos': near_center, 'radius': 22})
        self.pockets.append({'pos': far_center, 'radius': 18})
    
    def create_walls(self):
        """Crea las paredes de la mesa con PyMunk"""
        wall_thickness = 10
        walls = [
            # Pared izquierda
            (self.table_3d['near_left'], self.table_3d['far_left']),
            # Pared derecha
            (self.table_3d['near_right'], self.table_3d['far_right']),
            # Pared superior
            (self.table_3d['far_left'], self.table_3d['far_right']),
            # Pared inferior
            (self.table_3d['near_left'], self.table_3d['near_right']),
        ]
        
        for start, end in walls:
            wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            wall_shape = pymunk.Segment(wall_body, start, end, wall_thickness)
            wall_shape.elasticity = WALL_ELASTICITY
            wall_shape.friction = WALL_FRICTION
            self.space.add(wall_body, wall_shape)
    
    def create_ball(self, x, y, number, color, is_cue=False):
        """Crea una bola con PyMunk"""
        # Crear cuerpo con momento de inercia para rotación
        moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        body = pymunk.Body(BALL_MASS, moment)
        body.position = x, y
        
        # Crear forma de colisión
        shape = pymunk.Circle(body, BALL_RADIUS)
        shape.elasticity = BALL_ELASTICITY
        shape.friction = BALL_FRICTION
        
        # Añadir al espacio
        self.space.add(body, shape)
        
        # Guardar referencias
        self.ball_bodies[number] = body
        self.ball_shapes[number] = shape
        self.ball_colors[number] = color
        
        if is_cue:
            self.cue_ball_body = body
        
        return body
    
    def initialize_balls(self):
        """Inicializa todas las bolas en formación de triángulo"""
        # Bola blanca
        cue_x, cue_y = self.convert_3d_to_2d(0.2, 0.5)
        self.create_ball(cue_x, cue_y, 0, (255, 255, 255), is_cue=True)
        
        # Colores para las bolas
        colors = [
            (255, 200, 0),   # 1 - Amarillo
            (0, 100, 200),   # 2 - Azul
            (255, 50, 50),   # 3 - Rojo
            (150, 50, 150),  # 4 - Púrpura
            (255, 140, 0),   # 5 - Naranja
            (0, 150, 50),    # 6 - Verde
            (139, 69, 19),   # 7 - Marrón
            (0, 0, 0),       # 8 - Negro
            (255, 200, 0),   # 9 - Amarillo rayado
            (0, 100, 200),   # 10 - Azul rayado
            (255, 50, 50),   # 11 - Rojo rayado
            (150, 50, 150),  # 12 - Púrpura rayado
            (255, 140, 0),   # 13 - Naranja rayado
            (0, 150, 50),    # 14 - Verde rayado
        ]
        
        # Formar triángulo
        start_3d_x = 0.7
        start_3d_y = 0.5
        spacing = 0.04
        
        ball_num = 1
        for row in range(5):
            for col in range(row + 1):
                x_3d = start_3d_x + row * spacing
                y_3d = start_3d_y + (col - row/2) * spacing
                
                x, y = self.convert_3d_to_2d(x_3d, y_3d)
                
                if ball_num <= len(colors):
                    self.create_ball(x, y, ball_num, colors[ball_num-1])
                    ball_num += 1
    
    def convert_3d_to_2d(self, norm_x, norm_y):
        """Convierte coordenadas normalizadas (0-1) a coordenadas de pantalla con perspectiva"""
        near_left = np.array(self.table_3d['near_left'])
        near_right = np.array(self.table_3d['near_right'])
        far_left = np.array(self.table_3d['far_left'])
        far_right = np.array(self.table_3d['far_right'])
        
        near_point = near_left + norm_y * (near_right - near_left)
        far_point = far_left + norm_y * (far_right - far_left)
        point = near_point + norm_x * (far_point - near_point)
        
        return int(point[0]), int(point[1])
    
    def start_aiming(self, x, y):
        """Inicia el proceso de apuntar (NO TOCAR - usado por gestos)"""
        if not self.any_ball_moving():
            self.aiming = True
            self.aim_start = (x, y)
            self.aim_end = (x, y)
    
    def update_aim(self, x, y):
        """Actualiza la dirección de apunte (NO TOCAR - usado por gestos)"""
        if self.aiming:
            self.aim_end = (x, y)
    
    def shoot(self):
        """Ejecuta el tiro con PyMunk"""
        if self.aiming and self.aim_start and self.aim_end and self.cue_ball_body:
            dx = self.aim_end[0] - self.aim_start[0]
            dy = self.aim_end[1] - self.aim_start[1]
            
            # Validar dirección
            if dx <= 0:
                print(f"[DISPARO DESCARTADO] Movimiento hacia la izquierda (dx={dx:.1f}).")
                self.aiming = False
                self.aim_start = None
                self.aim_end = None
                return
            
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 10:
                direction_x = dx / distance
                direction_y = dy / distance
                
                # Calcular potencia (máximo 20)
                power = min(distance / 12, 20)
                
                # PYMUNK: Aplicar velocidad con multiplicador de escala x30
                velocity_scale = 30
                self.cue_ball_body.velocity = (
                    direction_x * power * velocity_scale,
                    direction_y * power * velocity_scale
                )
                
                # Añadir spin/rotación proporcional al impacto
                self.cue_ball_body.angular_velocity = (power * velocity_scale) / BALL_RADIUS
                
                print(f"[DISPARO EXITOSO] dx={dx:.1f}, dy={dy:.1f}, potencia={power:.1f}")
            
            self.aiming = False
            self.aim_start = None
            self.aim_end = None
    
    def any_ball_moving(self):
        """Verifica si alguna bola está en movimiento"""
        for body in self.ball_bodies.values():
            velocity = body.velocity
            if velocity.length > 0.5:  # Umbral de velocidad
                return True
        return False
    
    def update(self):
        """Actualiza el estado del juego - PyMunk maneja física automáticamente"""
        # Verificar bolas que caen en troneras
        self.check_pockets()
    
    def check_pockets(self):
        """Verifica si las bolas caen en las troneras"""
        balls_to_remove = []
        
        for number, body in self.ball_bodies.items():
            x, y = body.position
            
            for pocket in self.pockets:
                dx = x - pocket['pos'][0]
                dy = y - pocket['pos'][1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < pocket['radius']:
                    if number == 0:  # Bola blanca
                        self.score = max(0, self.score - 50)
                        # Reposicionar bola blanca
                        cue_x, cue_y = self.convert_3d_to_2d(0.3, 0.5)
                        body.position = cue_x, cue_y
                        body.velocity = (0, 0)
                        body.angular_velocity = 0
                    else:  # Bola de color
                        self.score += 50
                        balls_to_remove.append(number)
                    break
        
        # Remover bolas que cayeron
        for number in balls_to_remove:
            if number in self.ball_bodies:
                body = self.ball_bodies[number]
                shape = self.ball_shapes[number]
                self.space.remove(body, shape)
                del self.ball_bodies[number]
                del self.ball_shapes[number]
                del self.ball_colors[number]
    
    def draw(self, frame):
        """Dibuja el juego en el frame"""
        frame[:] = (40, 40, 40)
        
        # Dibujar mesa
        table_points = np.array([
            self.table_3d['near_left'],
            self.table_3d['near_right'],
            self.table_3d['far_right'],
            self.table_3d['far_left']
        ], np.int32)
        
        cv2.fillPoly(frame, [table_points], (20, 100, 40))
        cv2.polylines(frame, [table_points], True, (139, 69, 19), 15)
        
        # Dibujar troneras
        for pocket in self.pockets:
            cv2.circle(frame, pocket['pos'], pocket['radius'], (0, 0, 0), -1)
            cv2.circle(frame, pocket['pos'], pocket['radius'], (100, 50, 0), 2)
        
        # VECTOR PREVIEW (mano izq abierta) - NO TOCAR
        if self.show_aim_vector and self.aim_vector_start and self.aim_vector_end:
            azul_claro = (255, 200, 100)
            self.draw_dashed_line(frame, self.aim_vector_start, self.aim_vector_end, 
                                 azul_claro, 4, 15)
            cv2.circle(frame, self.aim_vector_start, 10, azul_claro, -1)
            cv2.circle(frame, self.aim_vector_start, 10, (255, 255, 255), 2)
            self.draw_arrow(frame, self.aim_vector_start, self.aim_vector_end, azul_claro, 4)
        
        # LÍNEA DE APUNTE (mano izq cerrada) - NO TOCAR
        if self.aiming and self.aim_start and self.aim_end:
            rojo = (0, 0, 255)
            cv2.line(frame, self.aim_start, self.aim_end, rojo, 5)
            cv2.circle(frame, self.aim_start, 10, rojo, -1)
            cv2.circle(frame, self.aim_start, 10, (255, 255, 255), 2)
            cv2.circle(frame, self.aim_end, 10, (255, 150, 0), -1)
            cv2.circle(frame, self.aim_end, 10, (255, 255, 255), 2)
            
            # BARRA DE POTENCIA - NO TOCAR
            dx = self.aim_end[0] - self.aim_start[0]
            dy = self.aim_end[1] - self.aim_start[1]
            distance = math.sqrt(dx**2 + dy**2)
            power = min(int(distance / 12), 20)
            
            bar_width = 400
            bar_height = 40
            bar_x = (self.width - bar_width) // 2
            bar_y = 30
            
            cv2.rectangle(frame, (bar_x - 5, bar_y - 5), 
                         (bar_x + bar_width + 5, bar_y + bar_height + 5), 
                         (0, 0, 0), -1)
            cv2.rectangle(frame, (bar_x - 5, bar_y - 5), 
                         (bar_x + bar_width + 5, bar_y + bar_height + 5), 
                         (255, 255, 255), 3)
            
            if power <= 10:
                bar_color = (0, 255, 0)
                status = "BAJA"
            elif power <= 20:
                bar_color = (0, 165, 255)
                status = "MEDIA"
            else:
                bar_color = (0, 0, 255)
                status = "ALTA"
            
            fill_width = int((power / 20) * bar_width)
            cv2.rectangle(frame, (bar_x, bar_y), 
                         (bar_x + fill_width, bar_y + bar_height), 
                         bar_color, -1)
            
            text = f"POWER: {power}/20 [{status}]"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.2, 3)[0]
            text_x = (self.width - text_size[0]) // 2
            text_y = bar_y + bar_height + 35
            
            cv2.putText(frame, text, (text_x + 2, text_y + 2), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 0), 3)
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.2, bar_color, 3)
        
        # PYMUNK: Dibujar bolas desde bodies
        for number, body in self.ball_bodies.items():
            x, y = int(body.position.x), int(body.position.y)
            color = self.ball_colors[number]
            
            # Sombra
            cv2.circle(frame, (x + 3, y + 3), BALL_RADIUS, (0, 0, 0), -1)
            
            # Bola
            cv2.circle(frame, (x, y), BALL_RADIUS, color, -1)
            cv2.circle(frame, (x, y), BALL_RADIUS, (255, 255, 255), 2)
            
            # Línea de rotación (visual del spin)
            angle = body.angle
            end_x = int(x + BALL_RADIUS * 0.7 * math.cos(angle))
            end_y = int(y + BALL_RADIUS * 0.7 * math.sin(angle))
            cv2.line(frame, (x, y), (end_x, end_y), (255, 255, 255), 2)
            
            # Número en la bola
            if number != 0:
                cv2.putText(frame, str(number), (x - 8, y + 6), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # HUD
        cv2.putText(frame, f"Score: {self.score}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        
        instructions = [
            "MANO IZQ ABIERTA: Mostrar vector de apunte",
            "MANO IZQ CERRADA: Marca inicio del tiro",
            "MANO DER: Marca dirección y dispara",
            "R: Reiniciar | Q: Salir"
        ]
        
        y_pos = self.height - 100
        for instruction in instructions:
            cv2.putText(frame, instruction, (50, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 25
        
        return frame
    
    def draw_dashed_line(self, frame, start, end, color, thickness, dash_length):
        """Dibuja una línea discontinua"""
        x1, y1 = start
        x2, y2 = end
        
        total_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if total_length == 0:
            return
        
        dx = (x2 - x1) / total_length
        dy = (y2 - y1) / total_length
        
        current_length = 0
        draw = True
        
        while current_length < total_length:
            next_length = min(current_length + dash_length, total_length)
            
            if draw:
                start_point = (int(x1 + dx * current_length), int(y1 + dy * current_length))
                end_point = (int(x1 + dx * next_length), int(y1 + dy * next_length))
                cv2.line(frame, start_point, end_point, color, thickness)
            
            current_length = next_length
            draw = not draw
    
    def draw_arrow(self, frame, start, end, color, thickness):
        """Dibuja una flecha al final de una línea"""
        cv2.arrowedLine(frame, start, end, color, thickness, tipLength=0.1)
    
    def set_aim_vector(self, start_pos, end_pos):
        """Establece el vector de apunte (NO TOCAR - usado por gestos)"""
        if start_pos and end_pos and not self.any_ball_moving():
            self.show_aim_vector = True
            
            if self.cue_ball_body:
                cue_x, cue_y = self.cue_ball_body.position
                self.aim_vector_start = (int(cue_x), int(cue_y))
            else:
                self.aim_vector_start = start_pos
            
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            
            length = 400
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 10:
                norm_dx = dx / distance
                norm_dy = dy / distance
                
                self.aim_vector_end = (
                    int(self.aim_vector_start[0] + norm_dx * length),
                    int(self.aim_vector_start[1] + norm_dy * length)
                )
            else:
                self.aim_vector_end = (
                    self.aim_vector_start[0],
                    self.aim_vector_start[1] - length
                )
        else:
            self.show_aim_vector = False
            self.aim_vector_start = None
            self.aim_vector_end = None

    def hide_aim_vector(self):
        """Oculta el vector de apunte (NO TOCAR - usado por gestos)"""
        self.show_aim_vector = False
        self.aim_vector_start = None
        self.aim_vector_end = None
    
    def reset(self):
        """Reinicia el juego"""
        self.score = 0
        self.aiming = False
        self.aim_start = None
        self.aim_end = None
        self.show_aim_vector = False
        self.aim_vector_start = None
        self.aim_vector_end = None
        
        # PYMUNK: Limpiar espacio y recrear
        for number, body in list(self.ball_bodies.items()):
            shape = self.ball_shapes[number]
            self.space.remove(body, shape)
        
        self.ball_bodies.clear()
        self.ball_shapes.clear()
        self.ball_colors.clear()
        
        self.initialize_balls()
