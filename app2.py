from flask import Flask, render_template, request, jsonify
import docker
from docker.errors import APIError
import yaml

app = Flask(__name__)

# Configuration
DOCKER_REGISTRY = "localhost:5100"
DOCKER_USERNAME = "username"
DOCKER_PASSWORD = "3133"
COMPOSE_FILE_PATH = '/docker-compose.yml'
client = docker.from_env()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/check_updates', methods=['POST'])
def check_updates():
    images = read_docker_compose_images(COMPOSE_FILE_PATH)
    updates = []
    for image in images:
        current_image = client.images.get(image)
        try:
            client.images.pull(image)
            latest_image = client.images.get(image)
            if current_image.id != latest_image.id:
                updates.append(f"Update available for {image}")
            else:
                updates.append(f"No updates for {image}")
        except APIError as e:
            updates.append(f"Error checking updates for {image}: {str(e)}")
    return render_template('index.html', updates=updates, images=images)

@app.route('/update_images', methods=['POST'])
def update_images():
    images = request.form.getlist('images')
    output = []
    for image in images:
        try:
            response = client.images.pull(image)
            output.append(f"Updated {image}: {response}")
        except APIError as e:
            output.append(f"Failed to update {image}: {str(e)}")
    return render_template('index.html', output=output)

def read_docker_compose_images(compose_path):
    with open(compose_path, 'r') as file:
        compose_data = yaml.safe_load(file)
        images = [service['image'] for service in compose_data['services'].values() if 'image' in service]
        return images

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
