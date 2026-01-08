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
        self.space.damping = 0.90  # ANTES 0.88 → AHORA 0.90 (equilibrio velocidad/fricción)
        self.space.iterations = 20  # ANTES SIMULATION_ITERATIONS → AHORA 20 (precisión física)
        
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
        
        # SISTEMA DE DOS FASES
        self.game_phase = 'idle'          # 'idle', 'aiming_direction', 'aiming_power'
        self.frozen_direction = None      # (dx, dy) unitario
        self.current_power = 0.0          # potencia en fase 2
        self.power_origin = None          # (x, y) en pantalla, SIEMPRE centro de la bola blanca
        
        # Crear paredes y bolas con PyMunk
        self.create_walls()
        self.initialize_balls()
    
    def init_pockets(self):
        """Inicializa las troneras en las esquinas y centros"""
        self.pockets = [
            {'pos': self.table_3d['near_left'], 'radius': 40},   # ANTES 35 → 40
            {'pos': self.table_3d['near_right'], 'radius': 40},  # ANTES 35 → 40
            {'pos': self.table_3d['far_left'], 'radius': 35},    # ANTES 30 → 35
            {'pos': self.table_3d['far_right'], 'radius': 35},   # ANTES 30 → 35
        ]
        
        near_center = (
            (self.table_3d['near_left'][0] + self.table_3d['near_right'][0]) // 2,
            (self.table_3d['near_left'][1] + self.table_3d['near_right'][1]) // 2
        )
        far_center = (
            (self.table_3d['far_left'][0] + self.table_3d['far_right'][0]) // 2,
            (self.table_3d['far_left'][1] + self.table_3d['far_right'][1]) // 2
        )
        
        self.pockets.append({'pos': near_center, 'radius': 38})  # ANTES 32 → 38
        self.pockets.append({'pos': far_center, 'radius': 33})   # ANTES 28 → 33
    

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
            wall_shape.elasticity = 0.75  # ANTES WALL_ELASTICITY → Menos rebote
            wall_shape.friction = 1.2  # ANTES WALL_FRICTION → Más agarre en paredes
            self.space.add(wall_body, wall_shape)
    
    def create_ball(self, x, y, number, color, is_cue=False):
        """Crea una bola con PyMunk"""
        # Crear cuerpo con momento de inercia para rotación
        moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        body = pymunk.Body(BALL_MASS, moment)
        body.position = x, y
        
        # Crear forma de colisión
        shape = pymunk.Circle(body, BALL_RADIUS)
        shape.elasticity = 1  # ANTES 0.75 → Mayor rebote/transferencia de energía
        shape.friction = 0.9  # ANTES 1.1 → Menos agarre = más velocidad
        
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
        if not self.any_ball_moving() and self.cue_ball_body:
            self.aiming = True
            self.game_phase = 'aiming_direction'
            
            # ✅ FRENO EMERGENCIA al iniciar apuntado
            for body in self.ball_bodies.values():
                body.velocity *= 0.1   # Reducir 90% velocidad instantáneo
                body.angular_velocity *= 0.1
            
            cue_x, cue_y = self.cue_ball_body.position
            # origen visual y geométrico = centro bola blanca
            self.aim_start = (int(cue_x), int(cue_y))
            self.aim_end = (int(x), int(y))
    
    def update_aim(self, x, y):
        """Actualiza la dirección de apunte (NO TOCAR - usado por gestos)"""
        if not self.aiming:
            return

        if self.game_phase == 'aiming_direction':
            # FASE 1: solo dirección, origen = bola blanca
            self.aim_end = (x, y)

        elif self.game_phase == 'aiming_power':
            # FASE 2: dirección FIJA (frozen_direction), solo cambia potencia
            if self.power_origin and self.frozen_direction:
                dx = x - self.power_origin[0]
                dy = y - self.power_origin[1]
                # proyectar movimiento sobre la dirección congelada
                projected = dx * self.frozen_direction[0] + dy * self.frozen_direction[1]
                self.current_power = max(0.0, min(projected / 12.0, 20.0))
            # aim_end NO cambia en fase 2 (la dirección está congelada)
    
    def freeze_direction(self):
        """Congela la dirección y pasa a la fase de ajuste de potencia"""
        if not (self.aiming and self.game_phase == 'aiming_direction' and self.cue_ball_body and self.aim_end):
            return

        cue_x, cue_y = self.cue_ball_body.position
        origin = (float(cue_x), float(cue_y))
        dx = self.aim_end[0] - origin[0]
        dy = self.aim_end[1] - origin[1]
        distance = math.hypot(dx, dy)
        if distance < 10:
            return

        # vector unitario desde la bola blanca hacia aim_end
        self.frozen_direction = (dx / distance, dy / distance)
        self.power_origin = (int(origin[0]), int(origin[1]))
        self.current_power = 0.0
        
        # ✅ FRENO al congelar dirección
        for body in self.ball_bodies.values():
            body.velocity *= 0.05  # Casi parar todo

        # fijar aim_start / aim_end para que la línea se vea en la dirección congelada
        reference_dist = 250
        self.aim_start = (int(origin[0]), int(origin[1]))
        self.aim_end = (
            int(origin[0] + self.frozen_direction[0] * reference_dist),
            int(origin[1] + self.frozen_direction[1] * reference_dist)
        )

        self.game_phase = 'aiming_power'
    
    def cancel_power_phase(self):
        """Volver de FASE 2 → FASE 1 (desactivar potencia, volver a dirección)"""
        if self.game_phase == 'aiming_power':
            print("🔄 Cancelando potencia → Volviendo a dirección")
            self.game_phase = 'aiming_direction'
            self.frozen_direction = None
            self.current_power = 0.0
            self.power_origin = None
            # Mantener aim_start y aim_end para que el usuario vea dónde estaba
    
    def shoot(self):
        """Ejecuta el tiro con PyMunk"""
        if not self.aiming or not self.cue_ball_body:
            return

        # MODO FASE 2 (preferente)
        if self.game_phase == 'aiming_power' and self.frozen_direction is not None:
            direction_x, direction_y = self.frozen_direction
            power = self.current_power
        # MODO FASE 1 (por compatibilidad)
        elif self.aim_start and self.aim_end:
            dx = self.aim_end[0] - self.aim_start[0]
            dy = self.aim_end[1] - self.aim_start[1]
            distance = math.hypot(dx, dy)
            if distance < 10:
                self.reset_aim()
                return
            direction_x = dx / distance
            direction_y = dy / distance
            power = min(distance / 12.0, 20.0)
        else:
            self.reset_aim()
            return

        if power > 1.0:
            velocity_scale = 85  # ANTES 75 → 85 (más potencia)
            
            # ✅ BOLA BLANCA con potencia completa
            self.cue_ball_body.velocity = (
                direction_x * power * velocity_scale,
                direction_y * power * velocity_scale
            )
            self.cue_ball_body.angular_velocity = (power * velocity_scale * 0.6) / BALL_RADIUS
            
            print(f"[DISPARO EXITOSO] dirección=({direction_x:.2f}, {direction_y:.2f}), potencia={power:.1f}")

        self.reset_aim()
    
    def reset_aim(self):
        """Resetea todas las variables de apuntado"""
        self.aiming = False
        self.game_phase = 'idle'
        self.aim_start = None
        self.aim_end = None
        self.frozen_direction = None
        self.power_origin = None
        self.current_power = 0.0
    
    def any_ball_moving(self):
        """Bloquea apuntado si CUALQUIER bola tiene velocidad > 5"""
        for body in self.ball_bodies.values():
            velocity = body.velocity
            if velocity.length > 5.0:  # ANTES 20.0 → 5.0 (ultra estricta)
                return True
        return False
    
    def update_physics(self):
        """Detener bolas con freno progresivo equilibrado"""
        MIN_VELOCITY_SLOW = 6.0  # Nueva: umbral lento
        MIN_VELOCITY_STOP = 3.0  # Umbral parada
        
        for body in self.ball_bodies.values():
            speed = body.velocity.length
            
            # ✅ DURANTE AIMING: PARAR TODO INMEDIATAMENTE
            if self.aiming and speed > 0:
                body.velocity *= 0.8    # Frenar fuerte
                body.angular_velocity *= 0.8
                
            # FRENO PROGRESIVO: solo si va muy rápido
            elif speed > MIN_VELOCITY_SLOW * 2:  # Solo frenar si va muy rápido
                body.velocity *= 0.97     # Freno suave
                
            # ✅ NUEVO: Cuando LENTA → PARADA INMEDIATA
            elif speed > MIN_VELOCITY_STOP:
                body.velocity *= 0.3    # Reducir 70% cada frame
                body.angular_velocity *= 0.3
                
            # Si la bola está muy lenta, detenerla completamente
            else:
                body.velocity = (0, 0)
                body.angular_velocity = 0
    
    def update(self):
        """Actualiza el estado del juego"""
        # Avanzar simulación física
        self.space.step(1/120.0)      # 120 Hz de física
        self.update_physics()         # Frenado personalizado
        self.check_pockets()          # Detección de troneras
    
    def check_pockets(self):
        """Verifica si las bolas caen en las troneras (múltiples por frame, depurable)"""
        balls_to_remove = []

        # 1) Copia de claves para no tocar el diccionario mientras iteramos
        active_numbers = list(self.ball_bodies.keys())
        # DEBUG:
        # print(f"[DEBUG] check_pockets: bolas activas = {active_numbers}")

        for number in active_numbers:
            # Puede haberse eliminado en este mismo frame
            if number not in self.ball_bodies:
                continue

            body = self.ball_bodies[number]
            bx, by = float(body.position.x), float(body.position.y)

            for pocket in self.pockets:
                px, py = pocket['pos']
                distance = math.hypot(bx - px, by - py)

                # Radios efectivos generosos (ajusta si hace falta)
                if number == 0:
                    effective_radius = pocket['radius']  # Blanca
                else:
                    effective_radius = pocket['radius']  # Colores igual de fácil

                # DEBUG:
                # print(f"[DEBUG] bola {number}: dist={distance:.1f}, eff={effective_radius:.1f}")

                if distance < effective_radius:
                    print(f"🎱 BOLA {number} CAE EN TRONERA (dist={distance:.1f} < {effective_radius:.1f})")

                    if number == 0:
                        # Bola blanca: reponer sin eliminar
                        self.score = max(0, self.score - 50)
                        cue_x, cue_y = self.convert_3d_to_2d(0.3, 0.5)
                        body.position = (cue_x, cue_y)
                        body.velocity = (0, 0)
                        body.angular_velocity = 0
                    else:
                        # Marcar bola de color para eliminar
                        balls_to_remove.append(number)
                    break  # Salir del bucle de pockets para esta bola

        # 2) Eliminar bolas marcadas FUERA del bucle principal
        if balls_to_remove:
            print(f"[DEBUG] Eliminando bolas: {balls_to_remove}")

        for number in balls_to_remove:
            body = self.ball_bodies.pop(number, None)
            shape = self.ball_shapes.pop(number, None)
            if body is not None and shape is not None:
                self.space.remove(body, shape)
            self.ball_colors.pop(number, None)
            self.score += 50
            print(f"[DEBUG] Bola {number} eliminada. Score = {self.score}")
    
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
            # Tronera negra
            cv2.circle(frame, pocket['pos'], pocket['radius'], (0, 0, 0), -1)
            # Borde grueso naranja/café
            cv2.circle(frame, pocket['pos'], pocket['radius'] + 3, (100, 50, 0), 4)
        
        # VECTOR PREVIEW (mano izq abierta) - NO TOCAR
        if self.show_aim_vector and self.aim_vector_start and self.aim_vector_end:
            azul_claro = (255, 200, 100)
            self.draw_dashed_line(frame, self.aim_vector_start, self.aim_vector_end, 
                                 azul_claro, 4, 15)
            cv2.circle(frame, self.aim_vector_start, 10, azul_claro, -1)
            cv2.circle(frame, self.aim_vector_start, 10, (255, 255, 255), 2)
            self.draw_arrow(frame, self.aim_vector_start, self.aim_vector_end, azul_claro, 4)
        
        # SISTEMA DE DOS FASES
        if self.aiming and self.aim_start and self.aim_end:
            if self.game_phase == 'aiming_direction':
                # FASE 1: Línea AZUL punteada desde bola blanca
                azul = (255, 150, 0)
                self.draw_dashed_line(frame, self.aim_start, self.aim_end, azul, 4, 15)
                cv2.circle(frame, self.aim_start, 10, azul, -1)
                cv2.circle(frame, self.aim_start, 10, (255, 255, 255), 2)
                cv2.circle(frame, self.aim_end, 8, (255, 200, 100), -1)
                self.draw_arrow(frame, self.aim_start, self.aim_end, azul, 4)
                
            elif self.game_phase == 'aiming_power':
                # FASE 2: Línea ROJA sólida desde power_origin (bola blanca)
                rojo = (0, 0, 255)
                if self.power_origin:
                    cv2.line(frame, self.power_origin, self.aim_end, rojo, 5)
                    cv2.circle(frame, self.power_origin, 10, rojo, -1)
                    cv2.circle(frame, self.power_origin, 10, (255, 255, 255), 2)
                    cv2.circle(frame, self.aim_end, 10, (255, 150, 0), -1)
                    cv2.circle(frame, self.aim_end, 10, (255, 255, 255), 2)
                    self.draw_arrow(frame, self.power_origin, self.aim_end, rojo, 5)
                
                # BARRA DE POTENCIA - Solo en FASE 2
                power = int(self.current_power)
                
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
                elif power <= 15:
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
        
        # Resetear variables del sistema de dos fases
        self.game_phase = 'idle'
        self.frozen_direction = None
        self.current_power = 0.0
        self.power_origin = None
        
        # PYMUNK: Limpiar espacio y recrear
        for number, body in list(self.ball_bodies.items()):
            shape = self.ball_shapes[number]
            self.space.remove(body, shape)
        
        self.ball_bodies.clear()
        self.ball_shapes.clear()
        self.ball_colors.clear()
        
        self.initialize_balls()
