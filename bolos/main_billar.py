import cv2
import numpy as np
from hand_tracking import HandTracker
from billiard_game import BilliardGame

def main():
    # Inicializar componentes
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    hand_tracker = HandTracker()
    game = BilliardGame(width=1200, height=800)
    
    # Variables para control de gestos
    prev_left_pos = None
    prev_right_pos = None
    
    print("=== JUEGO DE BILLAR CON MEDIAPIPE ===")
    print("Mano izquierda ABIERTA (azul): Muestra vector de apunte")
    print("Mano izquierda CERRADA: Marca el inicio del tiro")
    print("Mano derecha (verde): Marca la dirección y dispara")
    print("Presiona 'R' para reiniciar | 'Q' para salir")
    print("=====================================")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Voltear frame horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)
        
        # Procesar detección de manos
        results = hand_tracker.process_frame(frame)
        
        # Dibujar manos en el frame de la cámara
        camera_display = frame.copy()
        camera_display = hand_tracker.draw_hands(camera_display, results)
        
        # Obtener datos de ambas manos
        left_hand, right_hand = hand_tracker.get_hand_data(results, frame.shape)
        
        # Control del juego con las manos
        if not game.any_ball_moving():
            # MANO IZQUIERDA: Controla el vector de apunte y inicio del tiro
            if left_hand is not None:
                left_x = int(left_hand['index'][0])
                left_y = int(left_hand['index'][1])
                
                # Mapear posición de la cámara a la pantalla del juego
                game_x = int(np.interp(left_x, [0, frame.shape[1]], [0, game.width]))
                game_y = int(np.interp(left_y, [0, frame.shape[0]], [0, game.height]))
                
                is_hand_open = hand_tracker.is_hand_open(left_hand['landmarks'])
                
                if is_hand_open:
                    if right_hand is not None:
                        right_x = int(right_hand['index'][0])
                        right_y = int(right_hand['index'][1])
                        
                        # Mapear mano derecha al juego
                        game_right_x = int(np.interp(right_x, [0, frame.shape[1]], [0, game.width]))
                        game_right_y = int(np.interp(right_y, [0, frame.shape[0]], [0, game.height]))
                        
                        # El vector va desde mano izquierda hacia mano derecha
                        game.set_aim_vector((game_x, game_y), (game_right_x, game_right_y))
                    else:
                        # Si solo hay mano izquierda, usar dirección por defecto
                        game.set_aim_vector((game_x, game_y), (game_x, game_y - 100))
                    
                    # Cancelar apunte si está activo
                    if game.aiming:
                        game.aiming = False
                        game.aim_start = None
                        game.aim_end = None
                else:
                    game.hide_aim_vector()
                    
                    if not game.aiming:
                        game.start_aiming(game_x, game_y)
                        prev_right_pos = None
                
                prev_left_pos = (game_x, game_y)
            else:
                game.hide_aim_vector()
                if game.aiming and prev_left_pos is None:
                    game.aiming = False
                    game.aim_start = None
                    game.aim_end = None
                prev_left_pos = None
            
            # MANO DERECHA: Marca la dirección y dispara
            if right_hand is not None and game.aiming:
                right_x = int(right_hand['index'][0])
                right_y = int(right_hand['index'][1])
                
                # Mapear posición de la cámara a la pantalla del juego
                game_x = int(np.interp(right_x, [0, frame.shape[1]], [0, game.width]))
                game_y = int(np.interp(right_y, [0, frame.shape[0]], [0, game.height]))
                
                # Actualizar dirección de apunte
                game.update_aim(game_x, game_y)
                
                # Detectar gesto de disparo (movimiento rápido)
                if prev_right_pos is not None:
                    dx = game_x - prev_right_pos[0]
                    dy = game_y - prev_right_pos[1]
                    speed = np.sqrt(dx**2 + dy**2)
                    
                    # Si hay movimiento significativo, validar dirección
                    if speed > 30:
                        # Calcular distancia actual: aim_start -> mano_derecha_actual
                        dx_now = game_x - game.aim_start[0]
                        dy_now = game_y - game.aim_start[1]
                        distance_now = np.sqrt(dx_now**2 + dy_now**2)
                        
                        # Calcular distancia anterior: aim_start -> mano_derecha_anterior
                        dx_prev = prev_right_pos[0] - game.aim_start[0]
                        dy_prev = prev_right_pos[1] - game.aim_start[1]
                        distance_prev = np.sqrt(dx_prev**2 + dy_prev**2)
                        
                        # Solo disparar si la mano se está ALEJANDO de aim_start
                        if distance_now > distance_prev:
                            game.shoot()
                            print(f"[DISPARO] Alejándose: dist_now={distance_now:.1f} > dist_prev={distance_prev:.1f}")
                        else:
                            print(f"[BLOQUEADO] Acercándose: dist_now={distance_now:.1f} <= dist_prev={distance_prev:.1f}")
                
                prev_right_pos = (game_x, game_y)
            
            # Si se pierde la mano derecha mientras apuntaba, disparar
            if right_hand is None and game.aiming and prev_right_pos is not None:
                game.shoot()
                prev_right_pos = None

        # Actualizar física del juego
        game.update()
        
        # Crear frame del juego
        game_frame = np.zeros((game.height, game.width, 3), dtype=np.uint8)
        game_frame = game.draw(game_frame)
        
        if game.any_ball_moving():
            msg = "BOLAS EN MOVIMIENTO..."
            cv2.putText(game_frame, msg, (game.width//2 - 200, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 100, 100), 3)
        elif game.show_aim_vector:
            # MODO PREVIEW - Azul claro
            msg1 = "MODO PREVIEW (Mano Izq ABIERTA)"
            msg2 = "Cierra mano izquierda para PREPARAR TIRO"
            azul = (255, 200, 100)
            cv2.putText(game_frame, msg1, (game.width//2 - 280, 140), 
                       cv2.FONT_HERSHEY_DUPLEX, 1, azul, 3)
            cv2.putText(game_frame, msg2, (game.width//2 - 300, 175), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        elif game.aiming:
            # MODO APUNTE - Rojo
            msg1 = "MODO APUNTE (Mano Izq CERRADA)"
            msg2 = "Mueve mano DERECHA rapidamente para DISPARAR"
            rojo = (0, 0, 255)
            cv2.putText(game_frame, msg1, (game.width//2 - 280, 140), 
                       cv2.FONT_HERSHEY_DUPLEX, 1, rojo, 3)
            cv2.putText(game_frame, msg2, (game.width//2 - 320, 175), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        else:
            msg1 = "MANO IZQUIERDA:"
            msg2 = "ABIERTA = Preview  |  CERRADA = Apuntar"
            cv2.putText(game_frame, msg1, (game.width//2 - 180, 140), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)
            cv2.putText(game_frame, msg2, (game.width//2 - 280, 175), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 200, 255), 2)
        
        # Mostrar ventanas
        cv2.imshow('Camara - Tracking de Manos', camera_display)
        cv2.imshow('Juego de Billar', game_frame)
        
        # Control de teclado
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            game.reset()
            print("Juego reiniciado!")
    
    # Limpieza
    cap.release()
    hand_tracker.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
