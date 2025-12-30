import cv2
import mediapipe as mp
import numpy as np

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def process_frame(self, frame):
        """Procesa el frame y detecta las manos"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        return results
    
    def draw_hands(self, frame, results):
        """Dibuja los landmarks de las manos en el frame"""
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Determinar color según la mano
                label = handedness.classification[0].label
                color = (255, 0, 0) if label == "Left" else (0, 255, 0)
                
                # Dibujar conexiones
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=color, thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=color, thickness=2)
                )
                
                # Etiqueta
                h, w, _ = frame.shape
                x = int(hand_landmarks.landmark[0].x * w)
                y = int(hand_landmarks.landmark[0].y * h)
                cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame
    
    def get_hand_data(self, results, frame_shape):
        """Extrae datos de posición de ambas manos"""
        left_hand = None
        right_hand = None
        
        if results.multi_hand_landmarks:
            h, w = frame_shape[:2]
            
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                label = handedness.classification[0].label
                
                # Obtener posiciones importantes
                index_finger = hand_landmarks.landmark[8]
                wrist = hand_landmarks.landmark[0]
                middle_finger = hand_landmarks.landmark[12]
                
                hand_data = {
                    'index': np.array([index_finger.x * w, index_finger.y * h]),
                    'wrist': np.array([wrist.x * w, wrist.y * h]),
                    'middle': np.array([middle_finger.x * w, middle_finger.y * h]),
                    'landmarks': hand_landmarks
                }
                
                if label == "Left":
                    left_hand = hand_data
                else:
                    right_hand = hand_data
        
        return left_hand, right_hand
    
    def is_hand_open(self, hand_landmarks):
        """Detecta si la mano está abierta comparando distancias de dedos"""
        # Puntos clave: muñeca, punta dedos, base dedos
        wrist = hand_landmarks.landmark[0]
        
        # Puntas de los dedos
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        # Bases de los dedos
        index_base = hand_landmarks.landmark[5]
        middle_base = hand_landmarks.landmark[9]
        ring_base = hand_landmarks.landmark[13]
        pinky_base = hand_landmarks.landmark[17]
        
        # Calcular distancias
        def distance(p1, p2):
            return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        
        # Verificar si los dedos están extendidos
        fingers_extended = 0
        
        if distance(index_tip, index_base) > distance(wrist, index_base) * 0.5:
            fingers_extended += 1
        if distance(middle_tip, middle_base) > distance(wrist, middle_base) * 0.5:
            fingers_extended += 1
        if distance(ring_tip, ring_base) > distance(wrist, ring_base) * 0.5:
            fingers_extended += 1
        if distance(pinky_tip, pinky_base) > distance(wrist, pinky_base) * 0.5:
            fingers_extended += 1
        
        # Mano abierta si al menos 3 dedos están extendidos
        return fingers_extended >= 3

    def release(self):
        """Libera recursos"""
        self.hands.close()
