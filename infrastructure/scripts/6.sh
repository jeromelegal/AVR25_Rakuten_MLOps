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



# sudo apt install whois

# echo 'ubuntu' | mkpasswd -m sha-512 -s
# #  Résultat -> $6$XanRXtK0W2bUVhJc$PUWpdK.POqJdRtrnov6rDz1.CbeZNHmVY4/.gbL4ZkEYyeyNIRErqK8dOvQCyFCcDlxE9MJvtPfj.AcRuKF431

#####utililser le résultat du hash pour le mettre dans le fichier user-data
##### se placer dans le répertoire cloud-init qui contient meta-data et user-data
#genisoimage -output frontend-cloudinit.iso -volid cidata -joliet -rock user-data meta-data

# sudo cp /home/ubuntu/infrastructure/cloud-init/frontend-cloudinit.iso /var/lib/libvirt/cloud_init_isos/
# sudo chown libvirt-qemu:libvirt-qemu /var/lib/libvirt/cloud_init_isos/frontend-cloudinit.iso
# sudo chmod 644 /var/lib/libvirt/cloud_init_isos/frontend-cloudinit.iso

# virt-install \
#   --name test-cpu \
#   --ram 3072 \
#   --vcpus 2 \
#   --cpu qemu64 \
#   --disk path=/var/lib/libvirt/images/test-cpu.qcow2,size=10,bus=virtio \
#   --disk path=/var/lib/libvirt/cloud_init_isos/frontend-cloudinit.iso,device=cdrom \
#   --location /var/lib/libvirt/isos/ubuntu-24.04.1-live-server-amd64.iso \
#   --extra-args "console=ttyS0 autoinstall ds=nocloud-net" \
#   --console pty,target_type=serial \
#   --noautoconsole