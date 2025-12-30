import cv2
import mediapipe as mp
import numpy as np
import math

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Configuración del juego
GAME_WIDTH = 800
GAME_HEIGHT = 600
PIN_POSITIONS = [
    (400, 100), (370, 130), (430, 130),
    (340, 160), (400, 160), (460, 160),
    (310, 190), (370, 190), (430, 190), (490, 190)
]

class BowlingGame:
    def __init__(self):
        self.ball_pos = [400, 500]
        self.ball_vel = [0, 0]
        self.ball_radius = 15
        self.is_throwing = False
        self.throw_start_pos = None
        self.throw_power = 0
        
        # Pinos
        self.pins = [{'pos': list(pos), 'active': True, 'vel': [0, 0]} for pos in PIN_POSITIONS]
        self.pin_radius = 12
        
        # Control
        self.hand_positions = {'Left': None, 'Right': None}
        self.prev_hand_positions = {'Left': None, 'Right': None}
        
        # Puntuación
        self.score = 0
        self.throws = 0
        
    def reset_ball(self):
        self.ball_pos = [400, 500]
        self.ball_vel = [0, 0]
        self.is_throwing = False
        self.throw_start_pos = None
        self.throw_power = 0
        
    def reset_pins(self):
        self.pins = [{'pos': list(pos), 'active': True, 'vel': [0, 0]} for pos in PIN_POSITIONS]
        
    def update_hand_position(self, hand_label, x, y):
        """Actualiza la posición de la mano"""
        self.prev_hand_positions[hand_label] = self.hand_positions[hand_label]
        self.hand_positions[hand_label] = (x, y)
        
    def detect_throw_gesture(self):
        """Detecta el gesto de lanzamiento usando ambas manos"""
        left = self.hand_positions['Left']
        right = self.hand_positions['Right']
        prev_left = self.prev_hand_positions['Left']
        prev_right = self.prev_hand_positions['Right']
        
        # Lanzar con mano derecha (movimiento rápido hacia arriba)
        if right and prev_right and not self.is_throwing:
            dy = prev_right[1] - right[1]  # Movimiento hacia arriba
            if dy > 30:  # Umbral de velocidad
                self.throw_start_pos = list(self.ball_pos)
                self.is_throwing = True
                self.throw_power = min(dy / 2, 20)
                # Calcular dirección basada en posición horizontal de la mano
                dx = (right[0] - self.ball_pos[0]) * 0.3
                self.ball_vel = [dx, -self.throw_power]
                self.throws += 1
                return True
                
        return False
        
    def update_ball_control(self):
        """Controla la posición de la bola con la mano izquierda"""
        if not self.is_throwing:
            left = self.hand_positions['Left']
            if left:
                # Mover la bola horizontalmente con la mano izquierda
                target_x = left[0]
                self.ball_pos[0] += (target_x - self.ball_pos[0]) * 0.2
                # Mantener la bola en la zona de lanzamiento
                self.ball_pos[0] = max(50, min(GAME_WIDTH - 50, self.ball_pos[0]))
                
    def update_physics(self):
        """Actualiza la física del juego"""
        if self.is_throwing:
            # Actualizar posición de la bola
            self.ball_pos[0] += self.ball_vel[0]
            self.ball_pos[1] += self.ball_vel[1]
            
            # Fricción
            self.ball_vel[0] *= 0.99
            self.ball_vel[1] *= 0.99
            
            # Rebote en paredes
            if self.ball_pos[0] - self.ball_radius < 0 or self.ball_pos[0] + self.ball_radius > GAME_WIDTH:
                self.ball_vel[0] *= -0.8
                self.ball_pos[0] = max(self.ball_radius, min(GAME_WIDTH - self.ball_radius, self.ball_pos[0]))
                
            # Detectar colisiones con pinos
            for pin in self.pins:
                if pin['active']:
                    dist = math.sqrt((self.ball_pos[0] - pin['pos'][0])**2 + 
                                   (self.ball_pos[1] - pin['pos'][1])**2)
                    if dist < self.ball_radius + self.pin_radius:
                        pin['active'] = False
                        self.score += 10
                        # Transferir momento al pino
                        angle = math.atan2(pin['pos'][1] - self.ball_pos[1], 
                                         pin['pos'][0] - self.ball_pos[0])
                        pin['vel'] = [math.cos(angle) * 5, math.sin(angle) * 5]
                        
            # Actualizar pinos caídos
            for pin in self.pins:
                if not pin['active']:
                    pin['pos'][0] += pin['vel'][0]
                    pin['pos'][1] += pin['vel'][1]
                    pin['vel'][0] *= 0.95
                    pin['vel'][1] *= 0.95
                    
            # Resetear si la bola sale de la pantalla
            if self.ball_pos[1] < -50 or self.ball_pos[1] > GAME_HEIGHT + 50:
                self.reset_ball()
                # Resetear pinos si todos cayeron
                if all(not pin['active'] for pin in self.pins):
                    self.reset_pins()
                    
    def draw(self, frame):
        """Dibuja el juego"""
        # Fondo
        frame[:] = (34, 139, 34)  # Verde césped
        
        # Zona de bolos
        cv2.rectangle(frame, (200, 50), (600, 250), (139, 90, 43), -1)
        
        # Línea de lanzamiento
        cv2.line(frame, (0, 450), (GAME_WIDTH, 450), (255, 255, 255), 2)
        
        # Dibujar pinos
        for pin in self.pins:
            if pin['active']:
                cv2.circle(frame, (int(pin['pos'][0]), int(pin['pos'][1])), 
                          self.pin_radius, (255, 255, 255), -1)
                cv2.circle(frame, (int(pin['pos'][0]), int(pin['pos'][1])), 
                          self.pin_radius, (0, 0, 0), 2)
            else:
                # Pinos caídos
                cv2.circle(frame, (int(pin['pos'][0]), int(pin['pos'][1])), 
                          self.pin_radius // 2, (150, 150, 150), -1)
                
        # Dibujar bola
        cv2.circle(frame, (int(self.ball_pos[0]), int(self.ball_pos[1])), 
                  self.ball_radius, (0, 0, 255), -1)
        cv2.circle(frame, (int(self.ball_pos[0]), int(self.ball_pos[1])), 
                  self.ball_radius, (0, 0, 0), 2)
        
        # Indicadores de manos
        left = self.hand_positions['Left']
        right = self.hand_positions['Right']
        
        if left and not self.is_throwing:
            cv2.circle(frame, (int(left[0]), int(left[1])), 20, (255, 0, 0), 3)
            cv2.putText(frame, 'IZQUIERDA: Mover', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                       
        if right:
            cv2.circle(frame, (int(right[0]), int(right[1])), 20, (0, 255, 0), 3)
            cv2.putText(frame, 'DERECHA: Lanzar', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Puntuación
        cv2.putText(frame, f'Puntos: {self.score}', (GAME_WIDTH - 200, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'Lanzamientos: {self.throws}', (GAME_WIDTH - 200, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Instrucciones
        if not self.is_throwing:
            cv2.putText(frame, 'Mano izquierda: posicionar | Mano derecha: lanzar hacia arriba', 
                       (50, GAME_HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame

def main():
    # Inicializar captura de video
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Crear juego
    game = BowlingGame()
    
    print("🎳 Juego de Bolos con MediaPipe")
    print("=" * 50)
    print("Controles:")
    print("  - Mano IZQUIERDA: Mover la bola horizontalmente")
    print("  - Mano DERECHA: Lanzar (mover rápido hacia arriba)")
    print("  - Presiona 'R' para resetear")
    print("  - Presiona 'Q' para salir")
    print("=" * 50)
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("No se pudo acceder a la cámara")
            continue
            
        # Voltear imagen horizontalmente para efecto espejo
        image = cv2.flip(image, 1)
        
        # Convertir BGR a RGB para MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        
        # Crear frame del juego
        game_frame = np.zeros((GAME_HEIGHT, GAME_WIDTH, 3), dtype=np.uint8)
        
        # Procesar detección de manos
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Dibujar landmarks en la imagen de la cámara
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
                
                # Obtener etiqueta de la mano (Left/Right)
                hand_label = handedness.classification[0].label
                
                # Obtener posición de la palma (landmark 0)
                palm = hand_landmarks.landmark[0]
                
                # Convertir coordenadas normalizadas a coordenadas del juego
                game_x = int(palm.x * GAME_WIDTH)
                game_y = int(palm.y * GAME_HEIGHT)
                
                # Actualizar posición de la mano en el juego
                game.update_hand_position(hand_label, game_x, game_y)
                
                # Mostrar etiqueta en la cámara
                h, w, _ = image.shape
                cx, cy = int(palm.x * w), int(palm.y * h)
                cv2.putText(image, hand_label, (cx - 30, cy - 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Actualizar juego
        game.update_ball_control()
        game.detect_throw_gesture()
        game.update_physics()
        
        # Dibujar juego
        game_frame = game.draw(game_frame)
        
        # Mostrar ventanas
        cv2.imshow('🎳 Juego de Bolos', game_frame)
        cv2.imshow('📹 Camara con Tracking de Manos', image)
        
        # Controles de teclado
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            game.reset_ball()
            game.reset_pins()
            game.score = 0
            game.throws = 0
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
