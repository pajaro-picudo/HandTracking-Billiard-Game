import cv2
import mediapipe as mp
import numpy as np

class HandTracker:
    """
    Módulo de detección de manos usando MediaPipe.
    Detecta ambas manos simultáneamente y proporciona landmarks.
    """
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Suavizado de posiciones (media móvil)
        self.left_hand_buffer = []
        self.right_hand_buffer = []
        self.buffer_size = 5
        
    def process_frame(self, frame):
        """
        Procesa un frame de la cámara y detecta las manos.
        
        Returns:
            tuple: (left_hand_landmarks, right_hand_landmarks, annotated_frame)
        """
        # Voltear frame horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)
        
        # Convertir BGR a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Procesar con MediaPipe
        results = self.hands.process(rgb_frame)
        
        left_hand = None
        right_hand = None
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Dibujar landmarks en el frame
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS
                )
                
                # Identificar si es mano izquierda o derecha
                label = handedness.classification[0].label
                
                if label == "Left":
                    right_hand = hand_landmarks  # Invertido por el espejo
                else:
                    left_hand = hand_landmarks
        
        # Aplicar suavizado
        if left_hand:
            self.left_hand_buffer.append(left_hand)
            if len(self.left_hand_buffer) > self.buffer_size:
                self.left_hand_buffer.pop(0)
                
        if right_hand:
            self.right_hand_buffer.append(right_hand)
            if len(self.right_hand_buffer) > self.buffer_size:
                self.right_hand_buffer.pop(0)
        
        return left_hand, right_hand, frame
    
    def get_smoothed_position(self, hand_type='left'):
        """
        Obtiene la posición suavizada de la muñeca (landmark 0).
        
        Args:
            hand_type: 'left' o 'right'
            
        Returns:
            tuple: (x, y) normalizado [0-1]
        """
        buffer = self.left_hand_buffer if hand_type == 'left' else self.right_hand_buffer
        
        if not buffer:
            return None
            
        # Calcular promedio de posiciones
        x_sum = sum([lm.landmark[0].x for lm in buffer])
        y_sum = sum([lm.landmark[0].y for lm in buffer])
        
        return (x_sum / len(buffer), y_sum / len(buffer))
    
    def release(self):
        """Libera recursos de MediaPipe."""
        self.hands.close()
