#!/usr/bin/env python3
import os
import yaml
import libvirt
import jinja2
import subprocess
import grp
import pwd
from pathlib import Path
from typing import Dict, List, Optional

# Chemins et constants
ISO_DIR = "/var/lib/libvirt/isos"
VM_IMAGES_DIR = "/var/lib/libvirt/images"
CLOUD_INIT_ISO_DIR = "/var/lib/libvirt/cloud_init_isos"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Initialiser Jinja2 pour les templates
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True
)

class InfraDeployer:
    def __init__(self, yaml_file: str):
        self.yaml_file = yaml_file
        self.conn = None
        self._infra = None

    @property
    def infra(self):
        if self._infra is None:
            raise RuntimeError("L'infrastructure n'a pas été chargée. Appelez load_infra() d'abord.")
        return self._infra

    @infra.setter
    def infra(self, value):
        self._infra = value

    def check_prerequisites(self):
        """Vérifie les prérequis avant déploiement."""
        errors = []
        # 1. Vérifier les groupes utilisateur
        user_groups = [g.gr_name for g in grp.getgrall() if pwd.getpwuid(os.getuid()).pw_name in g.gr_mem]
        required_groups = ['kvm', 'libvirt']
        for group in required_groups:
            if group not in user_groups:
                errors.append(f"L'utilisateur doit être dans le groupe '{group}' (sudo usermod -aG {group} $USER)")
        # 2. Vérifier les répertoires
        for dir_path in [ISO_DIR, VM_IMAGES_DIR, CLOUD_INIT_ISO_DIR]:
            if not os.path.exists(dir_path):
                errors.append(f"Répertoire introuvable: {dir_path} (sudo mkdir -p {dir_path})")
            else:
                if not os.access(dir_path, os.W_OK):
                    errors.append(f"Permissions insuffisantes sur {dir_path} (sudo chown -R $USER:$USER {dir_path})")
        # 3. Vérifier que libvirtd est actif
        try:
            subprocess.run(['systemctl', 'is-active', 'libvirtd'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            errors.append("Le service libvirtd n'est pas actif (sudo systemctl start libvirtd)")
        # 4. Vérifier la connexion à libvirt
        try:
            self.conn = libvirt.open("qemu:///system")
            if self.conn is None:
                errors.append("Impossible de se connecter à libvirt (vérifiez les permissions)")
        except Exception as e:
            errors.append(f"Erreur de connexion à libvirt: {e}")
        if errors:
            raise RuntimeError("Prérequis non satisfaits:\n" + "\n".join(f"  - {e}" for e in errors))

    def load_infra(self):
        """Charge et valide le fichier YAML."""
        with open(self.yaml_file, 'r') as f:
            self.infra = yaml.safe_load(f)
        self._apply_defaults()
        self.validate()

    def _apply_defaults(self):
        """Applique les valeurs par défaut."""
        defaults = self.infra.get('defaults', {})
        # Defaults pour les VMs
        vm_defaults = defaults.get('vm', {})
        for vm in self.infra['vms']:
            for key, value in vm_defaults.items():
                if key not in vm:
                    vm[key] = value
        # Defaults pour les réseaux
        network_defaults = defaults.get('network', {})
        for network in self.infra['networks']:
            for key, value in network_defaults.items():
                if key not in network:
                    network[key] = value

    def validate(self):
        """Valide le fichier YAML."""
        errors = []
        # Vérifier que les ISO existent
        for vm in self.infra['vms']:
            iso_path = os.path.join(ISO_DIR, vm['iso'])
            if not os.path.exists(iso_path):
                errors.append(f"ISO introuvable: {iso_path}")
        # Vérifier que les réseaux référencés existent
        network_names = {net['name'] for net in self.infra['networks']}
        for vm in self.infra['vms']:
            for net in vm['networks']:
                if net['name'] not in network_names:
                    errors.append(f"Réseau {net['name']} non défini (utilisé par {vm['name']})")
        if errors:
            raise ValueError("Erreurs de validation:\n" + "\n".join(f"  - {e}" for e in errors))

    def network_exists(self, name: str) -> bool:
        """Vérifie si un réseau existe (actif ou inactif)."""
        networks = self.conn.listAllNetworks(0)
        return any(net.name() == name for net in networks)

    def network_is_active(self, name: str) -> bool:
        """Vérifie si un réseau est actif."""
        try:
            net = self.conn.networkLookupByName(name)
            return net.isActive()
        except libvirt.libvirtError:
            return False

    def vm_exists(self, name: str) -> bool:
        """Vérifie si une VM existe."""
        try:
            self.conn.lookupByName(name)
            return True
        except libvirt.libvirtError:
            return False

    def create_network(self, network: Dict):
        """Crée un réseau (sans l'activer)."""
        if self.network_exists(network['name']):
            print(f"  ! Réseau {network['name']} existe déjà, ignoré")
            return
        template = env.get_template('network.xml.j2')
        network_xml = template.render(network=network, netmask=netmask)
        try:
            self.conn.networkDefineXML(network_xml)
            print(f"  ✓ Réseau {network['name']} créé")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de la création du réseau {network['name']}: {e}")
            raise

    def start_network(self, name: str):
        """Active un réseau."""
        if self.network_is_active(name):
            print(f"  ! Réseau {name} est déjà actif")
            return
        try:
            net = self.conn.networkLookupByName(name)
            # net.setActive(True)
            net.create() 
            print(f"  ✓ Réseau {name} activé")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de l'activation du réseau {name}: {e}")
            raise

    def deploy_networks(self):
        """Déploie tous les réseaux (création + activation)."""
        for network in self.infra['networks']:
            print(f"Déploiement du réseau {network['name']}...")
            self.create_network(network)
            self.start_network(network['name'])

    def create_vm(self, vm: Dict):
        """Crée une VM (sans la démarrer)."""
        if self.vm_exists(vm['name']):
            print(f"  ! VM {vm['name']} existe déjà, ignorée")
            return
        # Créer le disque système
        disk_path = os.path.join(VM_IMAGES_DIR, f"{vm['name']}.qcow2")
        self._create_disk(disk_path, vm['disk_size'])
        # Créer les disques supplémentaires
        additional_disks = []
        for i, volume in enumerate(vm.get('volumes', [])):
            vol_path = os.path.join(VM_IMAGES_DIR, f"{vm['name']}-{volume['name']}.qcow2")
            self._create_disk(vol_path, volume['size'])
            additional_disks.append({'path': vol_path, 'target': f"vdb{i+1}"})
        # Générer l'ISO cloud-init
        cloud_init_iso = None
        if 'cloud_init' in vm:
            cloud_init_iso = self._create_cloud_init_iso(vm['name'], vm['cloud_init'])
        # Générer le XML
        template = env.get_template('vm.xml.j2')
        vm_xml = template.render(
            vm=vm,
            disk_path=disk_path,
            iso_path=os.path.join(ISO_DIR, vm['iso']),
            cloud_init_iso=cloud_init_iso,
            additional_disks=additional_disks,
            netmask=netmask
        )
        try:
            self.conn.defineXML(vm_xml)
            print(f"  ✓ VM {vm['name']} créée")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors de la création de la VM {vm['name']}: {e}")
            raise

    def start_vm(self, name: str):
        """Démarre une VM."""
        try:
            domain = self.conn.lookupByName(name)
            if domain.isActive():
                print(f"  ! VM {name} est déjà démarrée")
                return
            domain.create()
            print(f"  ✓ VM {name} démarrée")
        except libvirt.libvirtError as e:
            print(f"  ✗ Erreur lors du démarrage de la VM {name}: {e}")
            raise

    def deploy_vms(self):
        """Déploie toutes les VMs (création + démarrage)."""
        for vm in self.infra['vms']:
            print(f"Déploiement de la VM {vm['name']}...")
            self.create_vm(vm)
            # self.start_vm(vm['name'])

    def _create_disk(self, path: str, size_gb: int):
        """Crée un disque qcow2."""
        if os.path.exists(path):
            print(f"  ! Disque {path} existe déjà, ignoré")
            return
        subprocess.run(['qemu-img', 'create', '-f', 'qcow2', path, f"{size_gb}G"], check=True)
        print(f"  ✓ Disque {path} créé ({size_gb} Go)")

    def _create_cloud_init_iso(self, vm_name: str, cloud_init: Dict) -> str:
        """Génère une ISO cloud-init."""
        iso_path = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm_name}-cloudinit.iso")
        user_data_template = env.get_template('user_data.j2')
        user_data = user_data_template.render(cloud_init=cloud_init, password_hash=password_hash)
        with open("user-data", "w") as f:
            f.write(user_data)
        with open("meta-data", "w") as f:
            f.write(f"instance-id: iid-local01\nlocal-hostname: {vm_name}\n")
        subprocess.run([
            'genisoimage', '-output', iso_path,
            '-volid', 'cidata', '-joliet', '-rock',
            'user-data', 'meta-data'
        ], check=True)
        print(f"  ✓ ISO cloud-init générée: {iso_path}")
        return iso_path

    def deploy_firewall(self):
        """Affiche les règles de pare-feu à appliquer manuellement."""
        if 'firewall' not in self.infra:
            return
        print("\nRègles de pare-feu à appliquer manuellement:")
        for rule in self.infra['firewall']['rules']:
            action = "AUTHORISER" if rule['action'] == "allow" else "REFUSER"
            print(f"  {action} {rule['protocol']}/{rule['port']} vers {rule['vm']} depuis {rule['source']}")

    def clean(self):
        """Nettoie l'infrastructure."""
        print(f"Nettoyage de l'infrastructure {self.infra['name']}...")
        for vm in self.infra['vms']:
            self._clean_vm(vm)
        for network in reversed(self.infra['networks']):
            self._clean_network(network)
        print("\n✅ Nettoyage terminé !")

    def _clean_vm(self, vm: Dict):
        """Supprime une VM et ses ressources."""
        print(f"Suppression de la VM {vm['name']}...")
        try:
            domain = self.conn.lookupByName(vm['name'])
            if domain.isActive():
                domain.destroy()
            domain.undefine()
            print(f"  ✓ VM {vm['name']} supprimée")
        except libvirt.libvirtError as e:
            print(f"  ! VM {vm['name']} non trouvée: {e}")
        # Supprimer les disques
        disk_path = os.path.join(VM_IMAGES_DIR, f"{vm['name']}.qcow2")
        if os.path.exists(disk_path):
            os.remove(disk_path)
            print(f"  ✓ Disque {disk_path} supprimé")
        for volume in vm.get('volumes', []):
            vol_path = os.path.join(VM_IMAGES_DIR, f"{vm['name']}-{volume['name']}.qcow2")
            if os.path.exists(vol_path):
                os.remove(vol_path)
                print(f"  ✓ Disque {vol_path} supprimé")
        # Supprimer l'ISO cloud-init
        cloud_init_iso = os.path.join(CLOUD_INIT_ISO_DIR, f"{vm['name']}-cloudinit.iso")
        if os.path.exists(cloud_init_iso):
            os.remove(cloud_init_iso)
            print(f"  ✓ ISO cloud-init {cloud_init_iso} supprimée")

    def _clean_network(self, network: Dict):
        """Supprime un réseau."""
        print(f"Suppression du réseau {network['name']}...")
        try:
            net = self.conn.networkLookupByName(network['name'])
            if net.isActive():
                net.destroy()
            net.undefine()
            print(f"  ✓ Réseau {network['name']} supprimé")
        except libvirt.libvirtError as e:
            print(f"  ! Réseau {network['name']} non trouvé: {e}")

    def deploy(self):
        """Déploie l'infrastructure complète."""
        print(f"Déploiement de l'infrastructure {self.infra['name']}...")
        # self.check_prerequisites()
        # self.load_infra()
        self.deploy_networks()
        self.deploy_vms()
        self.deploy_firewall()
        print("\n✅ Déploiement terminé !")

# Fonctions utilitaires
def netmask(cidr: str) -> str:
    import ipaddress
    network = ipaddress.IPv4Network(cidr, strict=False)
    return str(network.netmask)

def password_hash(password: str, algorithm: str = 'sha512') -> str:
    import crypt
    return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Déployer/nettoyer une infrastructure KVM/QEMU.")
    parser.add_argument("yaml_file", help="Chemin vers le fichier YAML")
    parser.add_argument("--clean", action="store_true", help="Nettoyer l'infrastructure")
    args = parser.parse_args()
    try:
        deployer = InfraDeployer(args.yaml_file)
        deployer.check_prerequisites()
        deployer.load_infra()
        if args.clean:
            deployer.clean()
        else:
            deployer.deploy()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        exit(1)
