import React, { useState, useEffect } from 'react';
import axios from 'axios';

function VmManager() {
  const [vms, setVms] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [isos, setIsos] = useState([]);
  const [vmDetails, setVmDetails] = useState({
    name: '',
    cpu: 2,
    ram: 2048,
    disk_size: 20,
    network_name: '',
    iso: '',
    cloud_init: ''
  });
  const [networkDetails, setNetworkDetails] = useState({
    name: '',
    ip_address: '192.168.100.1',
    netmask: '255.255.255.0',
    dhcp_start: '192.168.100.2',
    dhcp_end: '192.168.100.254',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Charger la liste des ISO au démarrage
  useEffect(() => {
    const fetchIsos = async () => {
      try {
        const response = await axios.get('/isos/');
        setIsos(response.data);
      } catch (error) {
        setError("Échec de la récupération des ISO.");
        console.error("Erreur lors de la récupération des ISO :", error);
      }
    };
    fetchIsos();
  }, []);

  const handleVmInputChange = (e) => {
    const { name, value } = e.target;
    setVmDetails(prev => ({ ...prev, [name]: value }));
  };

  const handleNetworkInputChange = (e) => {
    const { name, value } = e.target;
    setNetworkDetails(prev => ({ ...prev, [name]: value }));
  };

  const handleVmSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/vms/', vmDetails);
      setSuccess("VM créée avec succès !");
      setVms([...vms, response.data]);
    } catch (error) {
      setError("Échec de la création de la VM. Veuillez vérifier les détails.");
      console.error("Erreur lors de la création de la VM :", error);
    }
  };

  const handleNetworkSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/networks/', networkDetails);
      setSuccess("Réseau créé avec succès !");
      setNetworks([...networks, response.data]);
    } catch (error) {
      setError("Échec de la création du réseau. Veuillez vérifier les détails.");
      console.error("Erreur lors de la création du réseau :", error);
    }
  };

  const fetchVms = async () => {
    try {
      const response = await axios.get('/vms/');
      setVms(response.data);
    } catch (error) {
      setError("Échec de la récupération des VMs.");
      console.error("Erreur lors de la récupération des VMs :", error);
    }
  };

  const fetchNetworks = async () => {
    try {
      const response = await axios.get('/networks/');
      setNetworks(response.data);
    } catch (error) {
      setError("Échec de la récupération des réseaux.");
      console.error("Erreur lors de la récupération des réseaux :", error);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Gestion des VMs et Réseaux</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}

      <div style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '20px', borderRadius: '5px' }}>
        <h2>Créer une VM</h2>
        <form onSubmit={handleVmSubmit}>
          <div style={{ marginBottom: '10px' }}>
            <label>Nom : </label>
            <input type="text" name="name" value={vmDetails.name} onChange={handleVmInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>CPU : </label>
            <input type="number" name="cpu" value={vmDetails.cpu} onChange={handleVmInputChange} min="1" required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>RAM (Mo) : </label>
            <input type="number" name="ram" value={vmDetails.ram} onChange={handleVmInputChange} min="512" required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Disque (Go) : </label>
            <input type="number" name="disk_size" value={vmDetails.disk_size} onChange={handleVmInputChange} min="10" required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Nom du Réseau : </label>
            <input type="text" name="network_name" value={vmDetails.network_name} onChange={handleVmInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Image ISO : </label>
            <select name="iso" value={vmDetails.iso} onChange={handleVmInputChange} required>
              <option value="">-- Sélectionnez une ISO --</option>
              {isos.map(iso => (
                <option key={iso} value={iso}>{iso}</option>
              ))}
            </select>
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Cloud-init (optionnel) : </label>
            <textarea name="cloud_init" value={vmDetails.cloud_init} onChange={handleVmInputChange} />
          </div>
          <button type="submit" style={{ padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
            Créer VM
          </button>
        </form>
      </div>

      <div style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '20px', borderRadius: '5px' }}>
        <h2>Créer un Réseau</h2>
        <form onSubmit={handleNetworkSubmit}>
          <div style={{ marginBottom: '10px' }}>
            <label>Nom du Réseau : </label>
            <input type="text" name="name" value={networkDetails.name} onChange={handleNetworkInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Adresse IP : </label>
            <input type="text" name="ip_address" value={networkDetails.ip_address} onChange={handleNetworkInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Masque de sous-réseau : </label>
            <input type="text" name="netmask" value={networkDetails.netmask} onChange={handleNetworkInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Début DHCP : </label>
            <input type="text" name="dhcp_start" value={networkDetails.dhcp_start} onChange={handleNetworkInputChange} required />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Fin DHCP : </label>
            <input type="text" name="dhcp_end" value={networkDetails.dhcp_end} onChange={handleNetworkInputChange} required />
          </div>
          <button type="submit" style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
            Créer Réseau
          </button>
        </form>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>Liste des VMs</h2>
        <button onClick={fetchVms} style={{ padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}>
          Rafraîchir la liste des VMs
        </button>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {vms.map(vm => (
            <li key={vm.id} style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
              {vm.name} - CPU: {vm.cpu}, RAM: {vm.ram} Mo, Disque: {vm.disk_size} Go, Réseau: {vm.network_name}, ISO: {vm.iso}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2>Liste des Réseaux</h2>
        <button onClick={fetchNetworks} style={{ padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px' }}>
          Rafraîchir la liste des réseaux
        </button>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {networks.map(network => (
            <li key={network.id} style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
              {network.name} - IP: {network.ip_address}, Masque: {network.netmask}, DHCP: {network.dhcp_start} - {network.dhcp_end}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default VmManager;
