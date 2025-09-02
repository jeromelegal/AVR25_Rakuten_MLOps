#!/bin/bash

# Contenu du fichier server.js avec les variables d'environnement
SERVER_JS_CONTENT=$(cat <<EOF
const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');

const app = express();

// Chemin vers votre application React construite
const buildPath = path.join(__dirname, 'build');

// Servez les fichiers statiques de votre application React
app.use(express.static(buildPath));

// Gérer les requêtes GET
app.get('*', (req, res) => {
  res.sendFile(path.join(buildPath, 'index.html'));
});

// Configuration SSL/TLS pour mTLS
const sslOptions = {
  key: fs.readFileSync(process.env.FRONTEND_KEY_PATH),
  cert: fs.readFileSync(process.env.FRONTEND_CERT_PATH),
  ca: fs.readFileSync(process.env.FRONTEND_CA_PATH),
  requestCert: true,
  rejectUnauthorized: true,
};

// Créer un serveur HTTPS avec mTLS
const server = https.createServer(sslOptions, app);

// Démarrer le serveur
const PORT = 3000;
server.listen(PORT, () => {
  console.log(\`Server is running on https://localhost:\${PORT}\`);
});
EOF
)

# Écrire le contenu dans le fichier server.js
echo "$SERVER_JS_CONTENT" > "$NODE_CONFIG_FILE"


echo "Fichier server.js généré avec succès."
