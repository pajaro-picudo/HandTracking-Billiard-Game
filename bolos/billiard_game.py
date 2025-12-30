import cv2
import numpy as np
import math

class Ball:
    def __init__(self, x, y, number, color, is_cue=False):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 15
        self.number = number
        self.color = color
        self.is_cue = is_cue
        self.active = True
        self.friction = 0.98
        
    def update(self):
        """Actualiza posición con física"""
        self.x += self.vx
        self.y += self.vy
        
        # Fricción
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Detener si velocidad muy baja
        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0
    
    def is_moving(self):
        return abs(self.vx) > 0.1 or abs(self.vy) > 0.1

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
        
        self.pockets = []
        self.init_pockets()
        
        self.balls = []
        self.cue_ball = None
        self.aiming = False
        self.aim_start = None
        self.aim_end = None
        self.shot_power = 0
        self.score = 0
        
        self.show_aim_vector = False
        self.aim_vector_start = None
        self.aim_vector_end = None
        
        self.init_balls()
    
    def init_pockets(self):
        """Inicializa las troneras en las esquinas y centros"""
        self.pockets = [
            {'pos': self.table_3d['near_left'], 'radius': 25},      # Esquina inferior izquierda
            {'pos': self.table_3d['near_right'], 'radius': 25},     # Esquina inferior derecha
            {'pos': self.table_3d['far_left'], 'radius': 20},       # Esquina superior izquierda
            {'pos': self.table_3d['far_right'], 'radius': 20},      # Esquina superior derecha
        ]
        
        # Troneras centrales en los lados largos
        near_center = (
            (self.table_3d['near_left'][0] + self.table_3d['near_right'][0]) // 2,
            (self.table_3d['near_left'][1] + self.table_3d['near_right'][1]) // 2
        )
        far_center = (
            (self.table_3d['far_left'][0] + self.table_3d['far_right'][0]) // 2,
            (self.table_3d['far_left'][1] + self.table_3d['far_right'][1]) // 2
        )
        
        self.pockets.append({'pos': near_center, 'radius': 22})  # Centro inferior
        self.pockets.append({'pos': far_center, 'radius': 18})   # Centro superior
        
    def init_balls(self):
        """Inicializa las bolas en formación de triángulo"""
        self.balls = []
        
        # Bola blanca (cue ball) - posición inicial
        cue_x, cue_y = self.convert_3d_to_2d(0.2, 0.5)
        self.cue_ball = Ball(cue_x, cue_y, 0, (255, 255, 255), is_cue=True)
        self.balls.append(self.cue_ball)
        
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
        
        # Formar triángulo de bolas - posición más al fondo
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
                    ball = Ball(x, y, ball_num, colors[ball_num-1])
                    self.balls.append(ball)
                    ball_num += 1
    
    def convert_3d_to_2d(self, norm_x, norm_y):
        """Convierte coordenadas normalizadas (0-1) a coordenadas de pantalla con perspectiva"""
        # Interpolación con perspectiva
        # norm_x: 0 = cerca, 1 = lejos
        # norm_y: 0 = izquierda, 1 = derecha
        
        near_left = np.array(self.table_3d['near_left'])
        near_right = np.array(self.table_3d['near_right'])
        far_left = np.array(self.table_3d['far_left'])
        far_right = np.array(self.table_3d['far_right'])
        
        # Interpolar en la parte cercana y lejana
        near_point = near_left + norm_y * (near_right - near_left)
        far_point = far_left + norm_y * (far_right - far_left)
        
        # Interpolar entre cerca y lejos
        point = near_point + norm_x * (far_point - near_point)
        
        return int(point[0]), int(point[1])
    
    def convert_2d_to_3d(self, x, y):
        """Convierte coordenadas de pantalla a normalizadas con perspectiva (aproximado)"""
        # Simplificación: usar interpolación inversa
        near_left = np.array(self.table_3d['near_left'])
        near_right = np.array(self.table_3d['near_right'])
        far_left = np.array(self.table_3d['far_left'])
        far_right = np.array(self.table_3d['far_right'])
        
        point = np.array([x, y])
        
        # Encontrar la posición aproximada
        # Calcular distancia a cada esquina
        total_near = near_right - near_left
        total_far = far_right - far_left
        
        # Estimar norm_y (izquierda-derecha) usando proyección
        norm_y = 0.5
        norm_x = 0.5
        
        # Método simplificado: interpolar basado en Y
        if y > (near_left[1] + far_left[1]) / 2:
            norm_x = (y - far_left[1]) / (near_left[1] - far_left[1])
        else:
            norm_x = 1 - (far_left[1] - y) / (far_left[1] - near_left[1])
        
        norm_x = np.clip(norm_x, 0, 1)
        
        # Estimar norm_y basado en X
        near_point = near_left + norm_x * (far_left - near_left)
        far_point = near_right + norm_x * (far_right - near_right)
        total_width = far_point[0] - near_point[0]
        
        if total_width != 0:
            norm_y = (x - near_point[0]) / total_width
            norm_y = np.clip(norm_y, 0, 1)
        
        return norm_x, norm_y
    
    def start_aiming(self, x, y):
        """Inicia el proceso de apuntar"""
        if not self.any_ball_moving():
            self.aiming = True
            self.aim_start = (x, y)
            self.aim_end = (x, y)
    
    def update_aim(self, x, y):
        """Actualiza la dirección de apunte"""
        if self.aiming:
            self.aim_end = (x, y)
    
    def shoot(self):
        """Ejecuta el tiro"""
        if self.aiming and self.aim_start and self.aim_end:
            # Calcular dirección y potencia desde aim_start hasta aim_end
            dx = self.aim_end[0] - self.aim_start[0]
            dy = self.aim_end[1] - self.aim_start[1]
            
            # Validar que el movimiento sea hacia la derecha (dx > 0)
            if dx <= 0:
                print(f"[DISPARO DESCARTADO] Movimiento hacia la izquierda (dx={dx:.1f}). Mueve la mano derecha hacia la DERECHA.")
                self.aiming = False
                self.aim_start = None
                self.aim_end = None
                return
            
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 10:  # Mínimo movimiento para disparar
                # Normalizar dirección
                direction_x = dx / distance
                direction_y = dy / distance
                
                # Potencia basada en distancia (limitada)
                power = min(distance / 15, 30)
                
                # Aplicar velocidad a la bola blanca
                self.cue_ball.vx = direction_x * power
                self.cue_ball.vy = direction_y * power
                print(f"[DISPARO EXITOSO] dx={dx:.1f}, dy={dy:.1f}, potencia={power:.1f}")
            
            self.aiming = False
            self.aim_start = None
            self.aim_end = None
    
    def any_ball_moving(self):
        """Verifica si alguna bola está en movimiento"""
        return any(ball.is_moving() for ball in self.balls if ball.active)
    
    def update(self):
        """Actualiza el estado del juego"""
        for ball in self.balls:
            if ball.active:
                ball.update()
        
        # Colisiones entre bolas
        self.check_collisions()
        
        # Verificar límites de la mesa (aproximado)
        self.check_table_bounds()
        
        self.check_pockets()

    def check_collisions(self):
        """Detecta y resuelve colisiones entre bolas"""
        for i, ball1 in enumerate(self.balls):
            if not ball1.active:
                continue
                
            for ball2 in self.balls[i+1:]:
                if not ball2.active:
                    continue
                
                dx = ball2.x - ball1.x
                dy = ball2.y - ball1.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < ball1.radius + ball2.radius:
                    # Colisión detectada
                    # Separar bolas
                    overlap = ball1.radius + ball2.radius - distance
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                        
                        ball1.x -= dx * overlap / 2
                        ball1.y -= dy * overlap / 2
                        ball2.x += dx * overlap / 2
                        ball2.y += dy * overlap / 2
                        
                        # Transferencia de momento (simplificada)
                        v1 = math.sqrt(ball1.vx**2 + ball1.vy**2)
                        v2 = math.sqrt(ball2.vx**2 + ball2.vy**2)
                        
                        ball2.vx += dx * v1 * 0.8
                        ball2.vy += dy * v1 * 0.8
                        ball1.vx *= 0.5
                        ball1.vy *= 0.5
                        
                        # Incrementar score si la bola blanca golpea otra
                        if ball1.is_cue and v1 > 1:
                            self.score += 10
    
    def check_table_bounds(self):
        """Verifica límites de la mesa con perspectiva"""
        for ball in self.balls:
            if not ball.active:
                continue
            
            # Límites simples (ajustar según mesa)
            margin = ball.radius
            
            # Límites horizontales
            if ball.x < self.table_3d['near_left'][0] + margin:
                ball.x = self.table_3d['near_left'][0] + margin
                ball.vx = -ball.vx * 0.7
            elif ball.x > self.table_3d['near_right'][0] - margin:
                ball.x = self.table_3d['near_right'][0] - margin
                ball.vx = -ball.vx * 0.7
            
            # Límites verticales
            if ball.y < self.table_3d['far_left'][1] + margin:
                ball.y = self.table_3d['far_left'][1] + margin
                ball.vy = -ball.vy * 0.7
            elif ball.y > self.table_3d['near_left'][1] - margin:
                ball.y = self.table_3d['near_left'][1] - margin
                ball.vy = -ball.vy * 0.7
    
    def check_pockets(self):
        """Verifica si las bolas caen en las troneras"""
        for ball in self.balls:
            if not ball.active:
                continue
            
            for pocket in self.pockets:
                dx = ball.x - pocket['pos'][0]
                dy = ball.y - pocket['pos'][1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < pocket['radius']:
                    # Bola cae en la tronera
                    ball.active = False
                    
                    if ball.is_cue:
                        # Si es la bola blanca, restarle puntos y reposicionarla
                        self.score = max(0, self.score - 50)
                        ball.active = True
                        ball.x, ball.y = self.convert_3d_to_2d(0.3, 0.5)
                        ball.vx = 0
                        ball.vy = 0
                    else:
                        # Bola de color metida, añadir puntos
                        self.score += 50
    
    def draw(self, frame):
        """Dibuja el juego en el frame"""
        frame[:] = (40, 40, 40)  # Fondo oscuro
        
        # Dibujar mesa en perspectiva
        table_points = np.array([
            self.table_3d['near_left'],
            self.table_3d['near_right'],
            self.table_3d['far_right'],
            self.table_3d['far_left']
        ], np.int32)
        
        cv2.fillPoly(frame, [table_points], (20, 100, 40))  # Verde mesa
        cv2.polylines(frame, [table_points], True, (139, 69, 19), 15)  # Borde marrón
        
        for pocket in self.pockets:
            cv2.circle(frame, pocket['pos'], pocket['radius'], (0, 0, 0), -1)
            cv2.circle(frame, pocket['pos'], pocket['radius'], (100, 50, 0), 2)
        
        if self.show_aim_vector and self.aim_vector_start and self.aim_vector_end:
            # MODO PREVIEW: Línea discontinua AZUL CLARO
            azul_claro = (255, 200, 100)  # BGR: Azul claro
            self.draw_dashed_line(frame, self.aim_vector_start, self.aim_vector_end, 
                                 azul_claro, 4, 15)
            cv2.circle(frame, self.aim_vector_start, 10, azul_claro, -1)
            cv2.circle(frame, self.aim_vector_start, 10, (255, 255, 255), 2)
            
            # Flecha al final
            self.draw_arrow(frame, self.aim_vector_start, self.aim_vector_end, 
                          azul_claro, 4)
        
        # Dibujar línea de apunte
        if self.aiming and self.aim_start and self.aim_end:
            # MODO APUNTE: Línea sólida ROJA
            rojo = (0, 0, 255)  # BGR: Rojo puro
            cv2.line(frame, self.aim_start, self.aim_end, rojo, 5)
            cv2.circle(frame, self.aim_start, 10, rojo, -1)
            cv2.circle(frame, self.aim_start, 10, (255, 255, 255), 2)
            cv2.circle(frame, self.aim_end, 10, (255, 150, 0), -1)  # Cyan para el final
            cv2.circle(frame, self.aim_end, 10, (255, 255, 255), 2)
            
            # Calcular potencia
            dx = self.aim_end[0] - self.aim_start[0]
            dy = self.aim_end[1] - self.aim_start[1]
            distance = math.sqrt(dx**2 + dy**2)
            power = min(int(distance / 15), 30)
            
            # BARRA DE POTENCIA GRANDE (centrada arriba)
            bar_width = 400
            bar_height = 40
            bar_x = (self.width - bar_width) // 2
            bar_y = 30
            
            # Fondo de la barra (negro con borde)
            cv2.rectangle(frame, (bar_x - 5, bar_y - 5), 
                         (bar_x + bar_width + 5, bar_y + bar_height + 5), 
                         (0, 0, 0), -1)
            cv2.rectangle(frame, (bar_x - 5, bar_y - 5), 
                         (bar_x + bar_width + 5, bar_y + bar_height + 5), 
                         (255, 255, 255), 3)
            
            # Color según potencia
            if power <= 10:
                bar_color = (0, 255, 0)  # Verde
                status = "BAJA"
            elif power <= 20:
                bar_color = (0, 165, 255)  # Naranja
                status = "MEDIA"
            else:
                bar_color = (0, 0, 255)  # Rojo
                status = "ALTA"
            
            # Rellenar barra según potencia
            fill_width = int((power / 30) * bar_width)
            cv2.rectangle(frame, (bar_x, bar_y), 
                         (bar_x + fill_width, bar_y + bar_height), 
                         bar_color, -1)
            
            # Texto de potencia
            text = f"POWER: {power}/30 [{status}]"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.2, 3)[0]
            text_x = (self.width - text_size[0]) // 2
            text_y = bar_y + bar_height + 35
            
            # Sombra del texto
            cv2.putText(frame, text, (text_x + 2, text_y + 2), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 0), 3)
            # Texto principal
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.2, bar_color, 3)
        
        # Dibujar bolas
        for ball in self.balls:
            if ball.active:
                # Sombra
                cv2.circle(frame, (int(ball.x + 3), int(ball.y + 3)), 
                          ball.radius, (0, 0, 0), -1)
                # Bola
                cv2.circle(frame, (int(ball.x), int(ball.y)), 
                          ball.radius, ball.color, -1)
                cv2.circle(frame, (int(ball.x), int(ball.y)), 
                          ball.radius, (255, 255, 255), 2)
                
                # Número en la bola
                if not ball.is_cue:
                    cv2.putText(frame, str(ball.number), 
                               (int(ball.x - 8), int(ball.y + 6)), 
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
        """Establece el vector de apunte cuando la mano izquierda está abierta"""
        if start_pos and end_pos and not self.any_ball_moving():
            self.show_aim_vector = True
            self.aim_vector_start = (int(self.cue_ball.x), int(self.cue_ball.y))
            
            # La dirección va desde la posición de la mano izquierda hacia la derecha
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            
            length = 400
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 10:  # Solo mostrar si hay suficiente separación entre manos
                norm_dx = dx / distance
                norm_dy = dy / distance
                
                self.aim_vector_end = (
                    int(self.cue_ball.x + norm_dx * length),
                    int(self.cue_ball.y + norm_dy * length)
                )
            else:
                # Si las manos están muy juntas, dirección por defecto hacia adelante
                self.aim_vector_end = (
                    int(self.cue_ball.x),
                    int(self.cue_ball.y - length)
                )
        else:
            self.show_aim_vector = False
            self.aim_vector_start = None
            self.aim_vector_end = None

    def hide_aim_vector(self):
        """Oculta el vector de apunte"""
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
        self.init_balls()
