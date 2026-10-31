import socket
import struct
import time
import cv2
import numpy as np

SERVER_IP = '127.0.0.1'
PORT = 8080


def generate_test_image(IMAGE_PATH, width, height):
    
    image = np.full((height, width, 3), 40, dtype=np.uint8)

   
    for y in range(height):
        for x in range(width):
            image[y, x, 0] = int((x / width) * 255)
            image[y, x, 1] = int((y / height) * 255)

   
    center_coordinates = (width // 2, height // 2)
    cv2.circle(image, center_coordinates, 80, (0, 0, 255), -1)

    
    cv2.rectangle(image, (50, 50), (200, 150), (0, 255, 255), 3)

   
    cv2.line(image, (50, height - 50), (width - 50, height - 50), (0, 255, 0), 4)

    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, 'TCP IMAGE TEST', (width // 2 - 140, 60),
                font, 1.0, (255, 255, 255), 2)
    cv2.putText(image, f'{width}x{height} px',
                (width // 2 - 60, height // 2 + 120),
                font, 0.7, (255, 255, 255), 1)

   
    cv2.imwrite(IMAGE_PATH, image)
    print(f"Test image successfully generated and saved as '{IMAGE_PATH}' ({width}x{height} pixels).")


def send_pixel_by_pixel(sock, header, img):
    """Send the header, then every pixel in its own sendall() call.

    Pixels are sent row by row (top to bottom, left to right).
    Each pixel is `channels` bytes (BGR order for a colour image, as read by OpenCV).
    """
    height, width, _ = img.shape

    sock.sendall(header)
    calls = 1

    for y in range(height):
        for x in range(width):
            sock.sendall(img[y, x].tobytes())
            calls += 1

    return calls


def run_client():

    
    IMAGE_PATH = "test_image.jpg"
    mode = "pixel-by-pixel"
    width = 640
    height = 480
    generate_test_image(IMAGE_PATH, width, height)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    client_socket.connect((SERVER_IP, PORT))
    print(f"Connected to server at {SERVER_IP}:{PORT} (mode: {mode})")

    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"Error: {IMAGE_PATH} not found.")
        client_socket.close()
        return

   
    height, width, channels = img.shape

    payload = img.tobytes()
    payload_length = len(payload)

    try:
        start_time = time.time()
 
        header = struct.pack('!HHI', height, width, payload_length)

        
        calls = send_pixel_by_pixel(client_socket, header, img)

        elapsed = time.time() - start_time
        throughput = (payload_length / (1024 * 1024)) / elapsed if elapsed > 0 else 0

        print(f"Sent raw image {width}x{height}x{channels} "
              f"({payload_length} bytes) in {elapsed:.4f} seconds "
              f"using {calls} send call(s) ({throughput:.2f} MB/s).")

    finally:
        client_socket.close()


if __name__ == '__main__':
    run_client()
