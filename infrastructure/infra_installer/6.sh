#!/bin/bash

# Vérifie qu'un argument (utilisateur) est passé
if [ $# -eq 0 ]; then
    echo "Erreur : Aucun utilisateur spécifié."
    echo "Usage : $0 <utilisateur>"
    exit 1
fi

USERNAME="$1"

# Vérifie que l'utilisateur existe sur la machine
if ! id "$USERNAME" &>/dev/null; then
    echo "Erreur : L'utilisateur '$USERNAME' n'existe pas sur cette machine."
    exit 1
fi

# Crée les répertoires et copie les fichiers
sudo mkdir -p ~/isos
sudo mkdir -p /var/lib/libvirt/isos
sudo mkdir -p /var/lib/libvirt/images
sudo mkdir -p /var/lib/libvirt/cloud_init_isos
sudo cp -R isos/* /var/lib/libvirt/isos/
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/isos
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/images
sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/cloud_init_isos

echo "Répertoires créés et permissions mises à jour pour l'utilisateur $USERNAME."

mkdir -p ~/qemu_boot

sudo cp /boot/vmlinuz-$(uname -r) ~/qemu_boot/
sudo cp /boot/initrd.img-$(uname -r) ~/qemu_boot/

sudo chown -R "$USERNAME:$USERNAME" ~/qemu_boot/

sudo chmod u+rw ~/qemu_boot/vmlinuz-*
sudo chmod u+rw ~/qemu_boot/initrd.img-*
sudo chmod u+rw ~/qemu_boot/*


sudo mkdir -p /var/lib/libvirt/shared

sudo chown -R "$USERNAME:$USERNAME" /var/lib/libvirt/shared

sudo chmod 666 /var/lib/libvirt/shared


sudo usermod -aG kvm $USERNAME







# Vérifier si l'utilisateur est root
if [ "$(id -u)" != "0" ]; then
   echo "Ce script doit être exécuté en tant que root" 1>&2
   exit 1
fi

# Définir le nom de l'utilisateur courant
USERNAME=$(logname)

# Vérifier si le groupe libvirt existe
if grep -q '^libvirt:' /etc/group; then
    # Ajouter l'utilisateur au groupe libvirt
    usermod -aG libvirt "$USERNAME"
    echo "L'utilisateur $USERNAME a été ajouté au groupe libvirt."
else
    echo "Le groupe libvirt n'existe pas."
fi

# Configurer sudo pour permettre à l'utilisateur d'exécuter la commande qemu-img resize sur n'importe quel fichier sans mot de passe
SUDOERS_FILE="/etc/sudoers"
if ! grep -q "$USERNAME ALL=(root) NOPASSWD: /usr/bin/qemu-img resize *" "$SUDOERS_FILE"; then
    echo "$USERNAME ALL=(root) NOPASSWD: /usr/bin/qemu-img resize *" >> "$SUDOERS_FILE"
    echo "La règle sudo a été ajoutée pour permettre à $USERNAME d'exécuter la commande qemu-img resize sur n'importe quel fichier sans mot de passe."
fi

echo "Les permissions ont été configurées avec succès."