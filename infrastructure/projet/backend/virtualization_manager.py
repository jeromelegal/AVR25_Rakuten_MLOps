import libvirt
import os
from fastapi import HTTPException

def list_isos(iso_dir):
    """Liste les fichiers ISO disponibles dans le répertoire spécifié."""
    try:
        return [f for f in os.listdir(iso_dir) if f.endswith('.iso')]
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Répertoire {iso_dir} non trouvé")

def create_vm_with_libvirt(vm_data):
    conn = libvirt.open("qemu:///system")
    if conn is None:
        raise HTTPException(status_code=500, detail="Échec de la connexion à libvirt")

    vm_xml_config = f"""
    <domain type='kvm'>
        <name>{vm_data['name']}</name>
        <memory unit='KiB'>{vm_data['ram'] * 1024}</memory>
        <vcpu placement='static'>{vm_data['cpu']}</vcpu>
        <os>
            <type arch='x86_64' machine='pc'>hvm</type>
            <boot dev='cdrom'/>
        </os>
        <devices>
            <disk type='file' device='cdrom'>
                <driver name='qemu' type='raw'/>
                <source file='{vm_data['iso_path']}'/>
                <target dev='sda' bus='sata'/>
            </disk>
            <disk type='file' device='disk'>
                <driver name='qemu' type='qcow2'/>
                <source file='/var/lib/libvirt/images/{vm_data['name']}.qcow2'/>
                <target dev='vdb' bus='virtio'/>
            </disk>
            <interface type='network'>
                <source network='{vm_data['network_name']}'/>
                <model type='virtio'/>
            </interface>
        </devices>
    </domain>
    """

    try:
        domain = conn.defineXML(vm_xml_config)
        if domain is None:
            raise HTTPException(status_code=500, detail="Échec de la définition du domaine")
        domain.create()
    except libvirt.libvirtError as e:
        raise HTTPException(status_code=500, detail=f"Erreur libvirt: {e}")


def create_network_with_libvirt(network_data):
    conn = libvirt.open("qemu:///system")
    if conn is None:
        raise HTTPException(status_code=500, detail="Failed to open connection to libvirt")

    network_xml_config = f"""
    <network>
        <name>{network_data['name']}</name>
        <bridge name='{network_data.get('bridge_name', 'virbr0')}' />
        <forward mode='nat'/>
        <ip address='{network_data['ip_address']}' netmask='{network_data['netmask']}'>
            <dhcp>
                <range start='{network_data['dhcp_start']}' end='{network_data['dhcp_end']}'/>
            </dhcp>
        </ip>
    </network>
    """

    try:
        network = conn.networkDefineXML(network_xml_config)
        if network is None:
            raise HTTPException(status_code=500, detail="Failed to define network")
        network.setActive(True)
    except libvirt.libvirtError as e:
        raise HTTPException(status_code=500, detail=f"Libvirt error: {e}")
