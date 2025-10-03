import argparse
import logging
import os
import subprocess
import yaml
import json
from pathlib import Path

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('registry_mirror.log'),
        logging.StreamHandler()
    ]
)

def configure_docker_for_insecure_registry(registry, use_sudo=False):
    try:
        logging.info(f"Configuring Docker for insecure registry: {registry}")
        daemon_config = "/etc/docker/daemon.json"
        config = {"insecure-registries": [registry]}
        with open(daemon_config, 'w') as f:
            json.dump(config, f)
        cmd = ['sudo', 'systemctl', 'restart', 'docker'] if use_sudo else ['systemctl', 'restart', 'docker']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to restart Docker daemon: {result.stderr}")
            return False
        logging.info(f"Successfully configured Docker for insecure registry: {registry}")
        return True
    except Exception as e:
        logging.error(f"Error configuring Docker for insecure registry {registry}: {str(e)}")
        return False

def image_exists_locally(image_name, use_sudo=False):
    try:
        cmd = ['sudo', 'docker', 'inspect', image_name] if use_sudo else ['docker', 'inspect', image_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error checking if image exists locally {image_name}: {str(e)}")
        return False

def image_exists_on_registry(image_name, registry, use_sudo=False):
    try:
        tagged_image = f"{registry}/{image_name}"
        cmd = ['sudo', 'docker', 'manifest', 'inspect', tagged_image] if use_sudo else ['docker', 'manifest', 'inspect', tagged_image]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error checking if image exists on registry {tagged_image}: {str(e)}")
        return False

def pull_image(image_name, use_sudo=False):
    try:
        logging.info(f"Pulling image: {image_name}")
        cmd = ['sudo', 'docker', 'pull', image_name] if use_sudo else ['docker', 'pull', image_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to pull image {image_name}: {result.stderr}")
            # If the image is a Bitnami image, try pulling from the legacy repository
            if 'bitnami' in image_name:
                legacy_image_name = image_name.replace('docker.io/bitnami', 'docker.io/bitnamilegacy')
                logging.info(f"Trying to pull from legacy repository: {legacy_image_name}")
                cmd = ['sudo', 'docker', 'pull', legacy_image_name] if use_sudo else ['docker', 'pull', legacy_image_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"Successfully pulled image from legacy repository: {legacy_image_name}")
                    return True, legacy_image_name
                else:
                    logging.error(f"Failed to pull image from legacy repository {legacy_image_name}: {result.stderr}")
            return False, image_name
        logging.info(f"Successfully pulled image: {image_name}")
        return True, image_name
    except Exception as e:
        logging.error(f"Error pulling image {image_name}: {str(e)}")
        return False, image_name

def tag_image(image_name, registry, use_sudo=False):
    try:
        clean_image_name = image_name.split('@')[0]
        logging.info(f"Tagging image: {clean_image_name}")
        cmd = ['sudo', 'docker', 'inspect', '--format={{.Id}}', image_name] if use_sudo else ['docker', 'inspect', '--format={{.Id}}', image_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to get image ID for {image_name}: {result.stderr}")
            return False
        image_id = result.stdout.strip()
        tagged_image = f"{registry}/{clean_image_name}"
        cmd = ['sudo', 'docker', 'tag', image_id, tagged_image] if use_sudo else ['docker', 'tag', image_id, tagged_image]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to tag image {clean_image_name}: {result.stderr}")
            return False
        logging.info(f"Successfully tagged image: {clean_image_name}")
        return True
    except Exception as e:
        logging.error(f"Error tagging image {clean_image_name}: {str(e)}")
        return False

def push_image(image_name, registry, use_sudo=False):
    try:
        clean_image_name = image_name.split('@')[0]
        tagged_image = f"{registry}/{clean_image_name}"
        logging.info(f"Pushing image: {tagged_image}")
        cmd = ['sudo', 'docker', 'push', tagged_image] if use_sudo else ['docker', 'push', tagged_image]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to push image {tagged_image}: {result.stderr}")
            # Try to push using HTTP explicitly
            os.environ['DOCKER_CLIENT_TIMEOUT'] = '120'
            os.environ['COMPOSE_HTTP_TIMEOUT'] = '120'
            cmd = ['sudo', 'docker', 'push', tagged_image] if use_sudo else ['docker', 'push', tagged_image]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Failed to push image {tagged_image} with HTTP: {result.stderr}")
                return False
        logging.info(f"Successfully pushed image: {tagged_image}")
        return True
    except Exception as e:
        logging.error(f"Error pushing image {tagged_image}: {str(e)}")
        return False

def extract_images_from_doc(doc):
    images = set()
    if not doc:
        return images
    if isinstance(doc, dict):
        spec = doc.get('spec', {})
        if 'template' in spec:
            spec = spec['template'].get('spec', {})
        containers = spec.get('containers', [])
        for container in containers:
            image = container.get('image')
            if image:
                images.add(image)
        init_containers = spec.get('initContainers', [])
        for init_container in init_containers:
            image = init_container.get('image')
            if image:
                images.add(image)
        volumes = spec.get('volumes', [])
        for volume in volumes:
            if volume.get('name') and 'projection' in volume:
                sources = volume['projection'].get('sources', [])
                for source in sources:
                    if source.get('configMap'):
                        images.add(source['configMap'].get('name'))
    return images

def rewrite_manifests(manifests_dir, rewrite_out_dir, mapping, registry):
    Path(rewrite_out_dir).mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(manifests_dir):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                input_file = os.path.join(root, file)
                # Calculer le chemin relatif par rapport à manifests_dir
                rel_path = os.path.relpath(root, manifests_dir)
                # Créer le répertoire de destination correspondant
                dest_dir = os.path.join(rewrite_out_dir, rel_path)
                Path(dest_dir).mkdir(parents=True, exist_ok=True)
                output_file = os.path.join(dest_dir, file)
                with open(input_file, 'r') as f:
                    try:
                        docs = list(yaml.safe_load_all(f))
                    except Exception as e:
                        logging.error(f"Error reading file {input_file}: {str(e)}")
                        continue
                # Filter out None or empty documents
                valid_docs = [doc for doc in docs if doc is not None and doc != {}]
                for i, doc in enumerate(valid_docs):
                    doc_images = extract_images_from_doc(doc)
                    for image in doc_images:
                        new_image = f"{registry}/{image.split('@')[0]}"
                        if isinstance(doc, dict):
                            spec = doc.get('spec', {})
                            if 'template' in spec:
                                spec = spec['template'].get('spec', {})
                            containers = spec.get('containers', [])
                            for container in containers:
                                if container.get('image') == image:
                                    container['image'] = new_image
                                    logging.info(f"Updated image reference in {file}: {image} -> {new_image}")
                            init_containers = spec.get('initContainers', [])
                            for init_container in init_containers:
                                if init_container.get('image') == image:
                                    init_container['image'] = new_image
                                    logging.info(f"Updated init container image reference in {file}: {image} -> {new_image}")
                with open(output_file, 'w') as f:
                    yaml.dump_all(valid_docs, f)
                logging.info(f"Successfully rewrote manifest: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifests', required=True, help='Directory containing manifests')
    parser.add_argument('--images-file', required=True, help='File to write images to')
    parser.add_argument('--registry', required=True, help='Registry to push images to')
    parser.add_argument('--rewrite-out', required=True, help='Directory to write rewritten manifests to')
    parser.add_argument('--mapping-file', required=True, help='File to write mapping to')
    parser.add_argument('--pull', action='store_true', help='Pull images')
    parser.add_argument('--push', action='store_true', help='Push images')
    parser.add_argument('--rewrite', action='store_true', help='Rewrite manifests')
    parser.add_argument('--sudo', action='store_true', help='Use sudo for docker commands')
    args = parser.parse_args()
    logging.info(f"Manifests: {args.manifests}")
    logging.info(f"Images file: {args.images_file}")
    logging.info(f"Registry: {args.registry}")
    logging.info(f"Rewrite out: {args.rewrite_out}")
    logging.info(f"Mapping file: {args.mapping_file}")
    logging.info(f"Pull: {args.pull}")
    logging.info(f"Push: {args.push}")
    logging.info(f"Rewrite: {args.rewrite}")
    logging.info(f"Sudo: {args.sudo}")

    if args.push:
        configure_docker_for_insecure_registry(args.registry, args.sudo)

    logging.info(f"Reading manifests from: {args.manifests}")
    images = set()
    for root, dirs, files in os.walk(args.manifests):
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                with open(os.path.join(root, file), 'r') as f:
                    try:
                        for doc in yaml.safe_load_all(f):
                            if doc is not None:
                                images.update(extract_images_from_doc(doc))
                    except Exception as e:
                        logging.error(f"Error reading file {os.path.join(root, file)}: {str(e)}")
                        continue
    logging.info(f"Found images: {images}")
    logging.info(f"Writing images to: {args.images_file}")
    with open(args.images_file, 'w') as f:
        for image in images:
            f.write(f"{image}\n")

    mapping = {}
    if os.path.exists(args.mapping_file):
        with open(args.mapping_file, 'r') as f:
            existing_mapping = json.load(f)
            mapping.update(existing_mapping)

    if args.pull or args.push:
        with open(args.mapping_file, 'w') as f:
            for image in images:
                if image in mapping:
                    logging.info(f"Image already in mapping: {image} -> {mapping[image]}")
                    continue
                # Ajouter toutes les images au mapping, même si elles ne sont pas tirées ou poussées
                mapping[image] = f"{args.registry}/{image.split('@')[0]}"
                if args.pull:
                    if not image_exists_locally(image, args.sudo):
                        success, actual_image = pull_image(image, args.sudo)
                        if success:
                            mapping[image] = f"{args.registry}/{actual_image.split('@')[0]}"
                if args.push:
                    if tag_image(image, args.registry, args.sudo):
                        if not image_exists_on_registry(image, args.registry, args.sudo):
                            if push_image(image, args.registry, args.sudo):
                                mapping[image] = f"{args.registry}/{image.split('@')[0]}"
                        else:
                            logging.info(f"Image already exists on registry: {image}")
                            mapping[image] = f"{args.registry}/{image.split('@')[0]}"
            json.dump(mapping, f)

    logging.info(f"Mapping: {mapping}")

    if args.rewrite:
        logging.info(f"Rewriting manifests to: {args.rewrite_out}")
        rewrite_manifests(args.manifests, args.rewrite_out, mapping, args.registry)

if __name__ == "__main__":
    main()
