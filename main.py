import pygame
import threading
import time
import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json

# MQTT Config
BROKER = "broker.hivemq.com"
TOPIC = "iot/traffic/data"

# Global lane data
lane_counts = [0, 0, 0, 0]
emergency_detected = [False, False, False, False]

# YOLO Setup
net = cv2.dnn.readNet("yolov2.weights", "yolov2.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
classes = open("coco.names").read().strip().split("\n")

# MQTT Setup
client = mqtt.Client()
client.connect(BROKER, 1883, 60)

# Simulation Constants
WIDTH, HEIGHT = 800, 800
FPS = 30
LANES = 4
GREEN_TIME_MIN = 5
SCALING_FACTOR = 2

pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def draw_simulation():
    win.fill((30, 30, 30))
    font = pygame.font.SysFont(None, 24)
    for i in range(LANES):
        pygame.draw.rect(win, (100 + i*30, 200, 200), (i * 200, 300, 100, 100))
        txt = font.render(f"Lane {i+1}: {lane_counts[i]}", True, (255, 255, 255))
        win.blit(txt, (i * 200 + 10, 270))
    pygame.display.update()

def detect_vehicles():
    global lane_counts, emergency_detected
    cap = cv2.VideoCapture("simulated_video.mp4")  # Replace with camera if needed

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), swapRB=True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        counts = [0] * LANES
        emergency_flags = [False] * LANES

        for out in outs:
            for det in out:
                scores = det[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    x_center = int(det[0] * width)
                    lane = min(x_center // (width // LANES), LANES - 1)
                    counts[lane] += 1
                    if classes[class_id] in ["ambulance", "fire truck"]:
                        emergency_flags[lane] = True

        lane_counts = counts
        emergency_detected = emergency_flags

        data = {
            "lanes": lane_counts,
            "emergency": emergency_detected
        }
        client.publish(TOPIC, json.dumps(data))
        time.sleep(0.2)

def simulation_loop():
    while True:
        draw_simulation()
        clock.tick(FPS)

# Threads
t1 = threading.Thread(target=simulation_loop)
t2 = threading.Thread(target=detect_vehicles)

t1.start()
t2.start()
