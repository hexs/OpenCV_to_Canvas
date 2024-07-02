import cv2
import numpy as np
from random import randint
import base64
from flask import Flask, render_template_string, request, jsonify
import threading

app = Flask(__name__)

# Initialize positions
pos_b, pos_g, pos_r = [300, 300], [300, 300], [300, 300]
mouse_pos = (0, 0)
click_event = None

def update_position(pos):
    pos[0] = max(0, min(600, pos[0] + randint(-10, 10)))
    pos[1] = max(0, min(600, pos[1] + randint(-10, 10)))

def generate_image():
    global encoded_image, mouse_pos, click_event
    while True:
        update_position(pos_b)
        update_position(pos_g)
        update_position(pos_r)
        img = np.full((600, 800, 3), (70, 70, 70), np.uint8)
        cv2.circle(img, pos_b, 10, (255, 0, 0), -1)
        cv2.circle(img, pos_g, 10, (0, 255, 0), -1)
        cv2.circle(img, pos_r, 10, (0, 0, 255), -1)
        cv2.putText(img, f'{mouse_pos}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        if click_event:
            cv2.putText(img, click_event['text'], (click_event['x'], click_event['y']), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        _, buffer = cv2.imencode('.jpg', img)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        cv2.waitKey(100)

@app.route('/')
def index():
    return render_template_string('''
        <html>
            <body>
                <canvas id="canvas" width="600" height="600" style="border:1px solid #000000;"></canvas>
                <script>
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');

                    canvas.addEventListener('mousemove', function(event) {
                        const rect = canvas.getBoundingClientRect();
                        const x = event.clientX - rect.left;
                        const y = event.clientY - rect.top;
                        fetch('/mousemove', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({x: x, y: y})
                        });
                    });

                    canvas.addEventListener('click', function(event) {
                        const rect = canvas.getBoundingClientRect();
                        const x = event.clientX - rect.left;
                        const y = event.clientY - rect.top;
                        let click_type = 'left click!';
                        if (event.detail === 2) {
                            click_type = 'double click!';
                        }
                        fetch('/click', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({x: x, y: y, text: click_type})
                        });
                    });

                    canvas.addEventListener('contextmenu', function(event) {
                        event.preventDefault();
                        const rect = canvas.getBoundingClientRect();
                        const x = event.clientX - rect.left;
                        const y = event.clientY - rect.top;
                        fetch('/click', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({x: x, y: y, text: 'right click!'})
                        });
                    });

                    function updateCanvas() {
                        fetch('/image')
                            .then(response => response.json())
                            .then(data => {
                                let img = new Image();
                                img.onload = function() {
                                    canvas.width = img.width;
                                    canvas.height = img.height;
                                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                                    ctx.drawImage(img, 0, 0);
                                }
                                img.src = 'data:image/jpeg;base64,' + data.image;
                            });
                        requestAnimationFrame(updateCanvas);
                    }
                    updateCanvas();
                </script>
            </body>
        </html>
    ''')

@app.route('/image')
def get_image():
    return jsonify({'image': encoded_image})

@app.route('/mousemove', methods=['POST'])
def mousemove():
    global mouse_pos
    data = request.get_json()
    mouse_pos = (data['x'], data['y'])
    return '', 204

@app.route('/click', methods=['POST'])
def click():
    global click_event
    data = request.get_json()
    click_event = {'x': data['x'], 'y': data['y'], 'text': data['text']}
    return '', 204

if __name__ == '__main__':
    encoded_image = ""
    threading.Thread(target=generate_image).start()
    app.run(debug=True)
