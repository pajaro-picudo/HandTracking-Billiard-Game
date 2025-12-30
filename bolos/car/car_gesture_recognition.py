import math

class CarGestureRecognizer:
    """
    Reconocedor de gestos específico para el juego de coche.
    
    Gestos:
    - Mano izquierda: Rotación de muñeca controla la rotación del coche
    - Mano derecha: Cerrar la mano acelera (cuanto más cerrada, más rápido)
    """
    
    def __init__(self):
        self.prev_left_angle = None
    
    def get_hand_rotation_angle(self, hand_landmarks):
        """
        Calcula el ángulo de rotación de la mano.
        Usa el vector entre muñeca y nudillo del dedo medio.
        
        Returns:
            float: Ángulo en grados [-180, 180]
        """
        if not hand_landmarks:
            return None
        
        wrist = hand_landmarks.landmark[0]
        middle_mcp = hand_landmarks.landmark[9]
        
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        
        angle = math.degrees(math.atan2(dy, dx))
        return angle
    
    def get_car_rotation_from_hand(self, hand_landmarks):
        """
        Obtiene la rotación del coche basada en la rotación de la mano izquierda.
        
        Returns:
            float: Ángulo de rotación para aplicar al coche (-180 a 180)
        """
        current_angle = self.get_hand_rotation_angle(hand_landmarks)
        
        if current_angle is None:
            self.prev_left_angle = None
            return 0
        
        # Normalizar el ángulo a un rango de control
        # Mapear de -180-180 a -30-30 para control más suave
        rotation = current_angle * 0.3
        
        return rotation
    
    def get_hand_closure(self, hand_landmarks):
        """
        Calcula qué tan cerrada está la mano (0 = abierta, 1 = cerrada).
        
        Returns:
            float: Valor entre 0 y 1
        """
        if not hand_landmarks:
            return 0
        
        # Calcular distancias de las puntas de los dedos a la palma
        palm = hand_landmarks.landmark[0]  # Muñeca
        finger_tips = [8, 12, 16, 20]  # Índice, medio, anular, meñique
        
        total_distance = 0
        max_distance = 0.3  # Distancia máxima esperada cuando la mano está abierta
        
        for tip_idx in finger_tips:
            tip = hand_landmarks.landmark[tip_idx]
            distance = math.sqrt((tip.x - palm.x)**2 + (tip.y - palm.y)**2)
            total_distance += distance
        
        avg_distance = total_distance / len(finger_tips)
        
        # Invertir y normalizar (0 = abierta, 1 = cerrada)
        closure = 1 - (avg_distance / max_distance)
        closure = max(0, min(1, closure))
        
        return closure
    
    def get_throttle_from_hand(self, hand_landmarks):
        """
        Obtiene el acelerador basado en qué tan cerrada está la mano derecha.
        
        Returns:
            float: Valor entre 0 (sin acelerar) y 1 (máximo)
        """
        closure = self.get_hand_closure(hand_landmarks)
        return closure
