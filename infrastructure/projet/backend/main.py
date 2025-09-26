from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from virtualization_manager import create_vm_with_libvirt, create_network_with_libvirt, list_isos
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remplacez par l'URL de votre frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ISO_DIR = "/var/lib/libvirt/isos"

vms_db = []
networks_db = []

class VMCreate(BaseModel):
    name: str
    cpu: int
    ram: int
    disk_size: int
    network_name: str
    iso: str  # Nom du fichier ISO sélectionné
    cloud_init: Optional[dict] = None

class NetworkCreate(BaseModel):
    name: str
    ip_address: str
    netmask: str
    dhcp_start: str
    dhcp_end: str


@app.get("/isos/", response_model=List[str])
def get_isos():
    print(f"{list_isos(ISO_DIR)}")
    return list_isos(ISO_DIR)

@app.post("/vms/")
def create_vm(vm_data: VMCreate):
    iso_path = f"{ISO_DIR}/{vm_data.iso}"
    if not os.path.exists(iso_path):
        raise HTTPException(status_code=404, detail=f"ISO {vm_data.iso} non trouvé")

    vm_data_dict = vm_data.dict()
    vm_data_dict["iso_path"] = iso_path  # Ajoute le chemin complet de l'ISO

    create_vm_with_libvirt(vm_data_dict)

    vm_id = len(vms_db) + 1
    new_vm = {**vm_data_dict, 'id': vm_id}
    vms_db.append(new_vm)

    return new_vm

@app.get("/vms/", response_model=List[dict])
def list_vms():
    return vms_db

@app.post("/networks/")
def create_network(network_data: NetworkCreate):
    create_network_with_libvirt(network_data.dict())

    network_id = len(networks_db) + 1
    new_network = {**network_data.dict(), 'id': network_id}
    networks_db.append(new_network)

    return new_network

@app.get("/networks/", response_model=List[dict])
def list_networks():
    return networks_db

@app.get("/")
def read_root():
    return {"message": "Bienvenue dans l'API de gestion des VMs et réseaux"}
