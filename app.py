from flask import Flask, Response
import cv2
import threading
import requests
import signal
import sys

app = Flask(__name__)
video_capture = cv2.VideoCapture(0)  # Capture video from the default camera

# Set up a global flag to control the capture thread
running = True

def generate_frames():
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def send_frame_to_agent(frame):
    url = 'http://127.0.0.1:5001/receive_frame'  # Replace with your agent's URL
    headers = {'Content-Type': 'application/octet-stream'}
    response = requests.post(url, headers=headers, data=frame)
    print(f'Sent frame to agent, response status code: {response.status_code}')
    return response

def capture_and_send_frames():
    while running:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            send_frame_to_agent(frame)

def signal_handler(sig, frame):
    global running
    running = False
    print('Stopping capture...')
    video_capture.release()
    cv2.destroyAllWindows()
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handler to handle CTRL+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start a thread to capture and send frames to the agent
    thread = threading.Thread(target=capture_and_send_frames)
    thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)