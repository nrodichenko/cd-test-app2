from flask import Flask, render_template, request, jsonify
import docker
from docker.errors import APIError
import yaml
import requests

app = Flask(__name__)

# Configuration
DOCKER_REGISTRY = "localhost:5100"
REGISTRY_URL = f"http://{DOCKER_REGISTRY}/"
DOCKER_USERNAME = "username"
DOCKER_PASSWORD = "3133"
COMPOSE_FILE_PATH = 'docker-compose.yml'
git_commit_hash = "{{GIT_COMMIT_HASH}}"
git_tag = "{{GIT_TAG}}"
git_commit_date = "{{GIT_COMMIT_DATE}}"


client = docker.from_env()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', git_hash=git_commit_hash, git_tag=git_tag, git_date=git_commit_date)

@app.route('/check_updates', methods=['POST'])
def check_updates():
    images = read_docker_compose_images(COMPOSE_FILE_PATH)
    print(images)
    updates = []
    for image in images:
        print(image)
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

@app.route('/check_docker_daemon', methods=['POST'])
def check_docker_daemon():
    ret = "Checking connectivity to Docker daemon..." + "\n"
    try:
        response = client.ping()
        if response:
            ret += "Docker daemon is reachable."
        else:
            ret += "Docker daemon is not reachable."
    except APIError as e:
        ret += f"Failed to connect to Docker daemon: {str(e)}"
    return render_template('index.html', ret1=ret)

@app.route('/check_registry_reachability', methods=['POST'])
def check_registry_reachability():
    ret = "Checking connectivity to Docker registry..." + "\n"
    try:
        response = requests.get(REGISTRY_URL, timeout=5)
        if response.status_code == 200:
            ret += "Registry is reachable."
        else:
            ret += f"Registry is not reachable. Status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        ret += f"Failed to connect to the registry: {str(e)}"
    return render_template('index.html', ret2=ret)

@app.route('/authenticate_registry', methods=['POST'])
def authenticate_registry():
    ret = "Authenticating to Docker registry..." + "\n"
    try:
        client.login(username=DOCKER_USERNAME, password=DOCKER_PASSWORD, registry=DOCKER_REGISTRY)
        ret += "Successfully authenticated."
    except APIError as e:
        ret += f"Authentication failed: {str(e)}"
    return render_template('index.html', ret3=ret)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
