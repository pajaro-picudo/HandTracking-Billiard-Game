import cv2
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from hand_tracking import HandTracker
from car_gesture_recognition import CarGestureRecognizer
from car_game import CarGameEngine

class CarGameController:
    """
    Controlador principal que integra el tracking de manos con el juego de coche.
    """
    
    def __init__(self):
        # Inicializar módulos
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = CarGestureRecognizer()
        self.game = CarGameEngine(screen_width=1200, screen_height=600)
        
        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Estado
        self.running = True
    
    def process_gestures(self, left_hand, right_hand):
        """
        Procesa los gestos de ambas manos y actualiza controles del juego.
        
        Args:
            left_hand: Landmarks de la mano izquierda
            right_hand: Landmarks de la mano derecha
        """
        # Mano izquierda: Rotación del coche
        if left_hand:
            rotation = self.gesture_recognizer.get_car_rotation_from_hand(left_hand)
            self.game.set_rotation(rotation)
        else:
            self.game.set_rotation(0)
        
        # Mano derecha: Acelerador
        if right_hand:
            throttle = self.gesture_recognizer.get_throttle_from_hand(right_hand)
            self.game.set_throttle(throttle)
        else:
            self.game.set_throttle(0)
    
    def run(self):
        """Loop principal del juego."""
        print("Iniciando juego de coche...")
        print("Controles:")
        print("  - Mano Derecha: Cerrar para acelerar")
        print("  - Mano Izquierda: Girar para rotar el coche")
        print("  - Presiona 'Q' para salir")
        print("  - Presiona 'R' para reiniciar posición del coche")
        
        while self.running:
            # Capturar frame de la cámara
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Procesar manos
            left_hand, right_hand, annotated_frame = self.hand_tracker.process_frame(frame)
            
            # Procesar gestos
            self.process_gestures(left_hand, right_hand)
            
            # Añadir información al frame de la cámara
            self.draw_camera_info(annotated_frame, left_hand, right_hand)
            
            # Mostrar ventana de cámara
            cv2.imshow('Cámara - Control de Manos', annotated_frame)
            
            # Ejecutar frame del juego
            self.running = self.game.run_frame()
            
            # Tecla para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
        
        # Limpieza
        self.cleanup()
    
    def draw_camera_info(self, frame, left_hand, right_hand):
        """Dibuja información de control en el frame de la cámara."""
        h, w = frame.shape[:2]
        
        # Información de mano izquierda
        if left_hand:
            rotation = self.gesture_recognizer.get_car_rotation_from_hand(left_hand)
            cv2.putText(frame, f"Rotacion: {int(rotation)} grados", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Mano Izquierda: No detectada", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Información de mano derecha
        if right_hand:
            throttle = self.gesture_recognizer.get_throttle_from_hand(right_hand)
            cv2.putText(frame, f"Acelerador: {int(throttle * 100)}%", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Mano Derecha: No detectada", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Instrucciones
        cv2.putText(frame, "Gira MANO IZQ para rotar coche", 
                   (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Cierra MANO DER para acelerar", 
                   (10, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def cleanup(self):
        """Libera recursos."""
        self.cap.release()
        cv2.destroyAllWindows()
        self.hand_tracker.release()
        self.game.cleanup()
        print("Juego finalizado.")

if __name__ == "__main__":
    controller = CarGameController()
    controller.run()
