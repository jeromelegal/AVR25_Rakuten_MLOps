from netfilterqueue import NetfilterQueue
import certifi
import socket
from scapy.all import *
import subprocess
import requests
import os
import logging
import time



# Configurer la journalisation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variable pour mettre en cache l'état du coffre
vault_sealed = None
cache_timeout = 60  # Durée de validité du cache en secondes
last_check_time = 0

# Fonction pour vérifier l'état du coffre
def check_vault_status():
    global vault_sealed, last_check_time
    current_time = time.time()
    if current_time - last_check_time < cache_timeout and vault_sealed is not None:
        return vault_sealed

    try:
        logging.info(f"SSL_CERT_FILE SSL_CERT_FILE : {os.environ['SSL_CERT_FILE']}")
        response = requests.get('https://127.0.0.1:8200/v1/sys/seal-status', verify=os.environ['SSL_CERT_FILE'])
        response.raise_for_status()
        data = response.json()
        vault_sealed = data.get('sealed', True)
        last_check_time = current_time
        return vault_sealed
    except requests.RequestException as e:
        logging.error(f"Erreur lors de la vérification de l'état du coffre : {e}")
        return True

# Fonction pour déverrouiller le coffre
def unseal_vault(unseal_keys):
    try:
        for key in unseal_keys:
            address = "https://127.0.0.1:8200"
            subprocess.run(['vault', 'operator', 'unseal', '-address', address, key], check=True)
        logging.info("Vault déverrouillé avec succès.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors du déverrouillage du coffre : {e}")

# Fonction de rappel pour traiter les paquets
def callback(packet):
    data = packet.get_payload()
    pkt = IP(data)

    logging.info(f"Paquet capturé : {pkt.summary()}")

    # Vérifiez si la variable d'environnement est définie
    logging.info(f"UNSEAL_KEYS UNSEAL_KEYS : {os.environ['UNSEAL_KEYS']}")
    logging.info(f"VAULT_ADDR VAULT_ADDR : {os.environ['VAULT_ADDR']}")        


    # Vérifiez l'état du coffre
    sealed_status = check_vault_status()
    if sealed_status:
        # Lire les clés de déverrouillage à partir de la variable d'environnement
        unseal_keys = os.getenv('UNSEAL_KEYS', '').split()
        if unseal_keys:
            # Déverrouillez le coffre
            unseal_vault(unseal_keys)
        else:
            logging.error("Aucune clé de déverrouillage trouvée dans la variable d'environnement UNSEAL_KEYS.")
    else:
        logging.info("Vault est déjà déverrouillé.")

    # Acceptez le paquet
    packet.accept()

def main():
    logging.info(f"certifi.where() : {certifi.where()}")   

    # Créez une instance de NFQueue
    nfqueue = NetfilterQueue()

    # Ouvrez la file d'attente 1
    nfqueue.bind(1, callback)

    try:
        logging.info("NFQUEUE en cours d'exécution...")
        nfqueue.run()  # Lancez la boucle de traitement
    except KeyboardInterrupt:
        logging.info("Arrêt de NFQUEUE...")

    # Nettoyez
    nfqueue.unbind()

if __name__ == "__main__":
    main()
