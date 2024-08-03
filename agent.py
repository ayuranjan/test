from flask import Flask, request
import cv2
import numpy as np
import os

agent_app = Flask(__name__)

@agent_app.route('/receive_frame', methods=['POST'])
def receive_frame():
    frame = request.data
    np_img = np.frombuffer(frame, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    # Save the received frame to a file
    if not os.path.exists('received_frames'):
        os.makedirs('received_frames')
    frame_number = len(os.listdir('received_frames'))
    cv2.imwrite(f'received_frames/frame_{frame_number}.jpg', img)

    cv2.imshow('Received Frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return 'Stopping', 200
    return 'Frame received', 200

if __name__ == '__main__':
    agent_app.run(host='0.0.0.0', port=5001)