import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
from mediapipe import solutions
import pygame
import pymunk
import cv2
import numpy as np
import time
import os
from dotenv import load_dotenv

# ==========================================================
# CONFIGURACIÓN
# ==========================================================

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "hand_landmarker.task")
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# ==========================================================
# MEDIAPIPE
# ==========================================================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

detection_result = None

def get_result(result, output_image, timestamp_ms):
    global detection_result
    detection_result = result

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=get_result
)

# ==========================================================
# PYGAME + PYMUNK
# ==========================================================

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🎳 Wii Bowling con MediaPipe")
clock = pygame.time.Clock()

space = pymunk.Space()
space.gravity = (0, 900)

# Suelo
floor = pymunk.Segment(space.static_body, (0, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT - 20), 5)
floor.friction = 1.0
space.add(floor)

# ==========================================================
# OBJETOS DEL JUEGO
# ==========================================================

def create_ball():
    body = pymunk.Body(5, pymunk.moment_for_circle(5, 0, 15))
    body.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
    shape = pymunk.Circle(body, 15)
    shape.elasticity = 0.8
    shape.friction = 0.6
    space.add(body, shape)
    return body

def create_pin(x, y):
    body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 10))
    body.position = x, y
    shape = pymunk.Circle(body, 10)
    shape.elasticity = 0.5
    shape.friction = 0.8
    space.add(body, shape)
    return body

ball = create_ball()
launched = False

# Crear bolos
pins = []
start_x = SCREEN_WIDTH // 2
start_y = 150

for row in range(4):
    for i in range(row + 1):
        pins.append(
            create_pin(
                start_x + (i - row / 2) * 30,
                start_y + row * 30
            )
        )

# ==========================================================
# FUNCIONES DE MANO
# ==========================================================

def hand_closed(landmarks):
    thumb = landmarks[4]
    index = landmarks[8]
    dist = np.linalg.norm(
        np.array([thumb.x - index.x, thumb.y - index.y])
    )
    return dist < 0.05

# ==========================================================
# BUCLE PRINCIPAL
# ==========================================================

cap = cv2.VideoCapture(0)

with HandLandmarker.create_from_options(options) as landmarker:
    running = True

    while running and cap.isOpened():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, int(time.time() * 1000))

        if detection_result and detection_result.hand_landmarks:
            landmarks = detection_result.hand_landmarks[0]

            wrist = landmarks[0]
            index_tip = landmarks[8]

            hand_x = int(index_tip.x * SCREEN_WIDTH)
            hand_y = int(index_tip.y * SCREEN_HEIGHT)

            direction = np.array([
                index_tip.x - wrist.x,
                index_tip.y - wrist.y
            ])

            if not launched:
                ball.position = hand_x, hand_y
                ball.velocity = (0, 0)

            if hand_closed(landmarks) and not launched:
                norm = np.linalg.norm(direction)
                if norm > 0:
                    force = direction / norm
                    ball.apply_impulse_at_local_point(
                        (force[0] * 800, -force[1] * 800)
                    )
                    launched = True

        # Física
        space.step(1 / FPS)

        # Render
        screen.fill((240, 240, 240))

        # Bola
        pygame.draw.circle(
            screen,
            (0, 0, 255),
            (int(ball.position.x), int(ball.position.y)),
            15
        )

        # Bolos
        for pin in pins:
            pygame.draw.circle(
                screen,
                (200, 0, 0),
                (int(pin.position.x), int(pin.position.y)),
                10
            )

        pygame.display.flip()
        clock.tick(FPS)

        cv2.imshow("MediaPipe Hands", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
