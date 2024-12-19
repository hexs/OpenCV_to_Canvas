import json
import time
import cv2
import numpy as np
from random import randint
import base64
from flask import Flask, render_template_string, Response

app = Flask(__name__)

pos_b, pos_g, pos_r = [300, 300], [300, 300], [300, 300]
mouse_pos = (0, 0)
click_event = None


def update_position(pos):
    pos[0] = max(0, min(800, pos[0] + randint(-10, 10)))
    pos[1] = max(0, min(600, pos[1] + randint(-10, 10)))


def generate_image(data):
    while True:
        update_position(pos_b)
        update_position(pos_g)
        update_position(pos_r)
        img = np.full((600, 800, 3), (70, 70, 70), np.uint8)
        cv2.circle(img, pos_b, 10, (255, 0, 0), -1)
        cv2.circle(img, pos_g, 10, (0, 255, 0), -1)
        cv2.circle(img, pos_r, 10, (0, 0, 255), -1)
        cv2.putText(img, f'Mouse Position: {mouse_pos}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        _, buffer = cv2.imencode('.jpg', img)
        data['response'] = {
            "image": 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8'),
            "image_frame": 20,
            "image_name": "image.jpg"
        }
        cv2.waitKey(100)
        time.sleep(0.5)


@app.route('/')
def index():
    return render_template_string('''
        <html>
            <body>
            
                <canvas id="canvas" width="800" height="600" style="border:1px solid #000000;"></canvas>
                <script>
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    const eventSource = new EventSource('/image');

                    eventSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        const image = new Image();
                        image.src = data.image;
                        console.log(data.image_frame, data.image_name)
                        image.onload = function() {
                            ctx.clearRect(0, 0, canvas.width, canvas.height);
                            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                        };
                    };

                    eventSource.onerror = function(err) {
                        console.error("EventSource failed:", err);
                    };
                </script>
            </body>
        </html>
    ''')


@app.route('/image')
def get_image():
    def generate():
        old_data_response = None
        while True:
            if old_data_response != data['response']:
                old_data_response = data['response']
                yield f'''data: {json.dumps(data['response'])}\n\n'''
            time.sleep(0.1)

    return Response(generate(), content_type='text/event-stream')


def run_server(data):
    app.config['data'] = data
    app.run(host="0.0.0.0", port=5695, debug=False, use_reloader=False)


if __name__ == '__main__':
    from hexss.threading import Multithread

    data = {
        'play': True,
        'response': None
    }

    m = Multithread()

    m.add_func(target=generate_image, args=(data,))
    m.add_func(target=run_server, args=(data,), join=False)

    m.start()
    m.join()
