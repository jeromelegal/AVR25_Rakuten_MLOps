-- Connect to databse
\c file_storage;

-- Insert categories
INSERT INTO categories (code, label, created_by) VALUES
(10, 'Livre occasion', 1),
(40, 'Jeu vidéo, accessoire tech', 1),
(50, 'Accessoire Console', 1),
(60, 'Console de jeu', 1),
(1140, 'Figurine', 1),
(1160, 'Carte Collection', 1),
(1180, 'Jeu Plateau', 1),
(1280, 'Jouet enfant, déguisement', 1),
(1281, 'Jeu de société', 1),
(1300, 'Jouet tech', 1),
(1301, 'Paire de chaussettes', 1),
(1302, 'Jeu extérieur, vêtement', 1),
(1320, 'Autour du bébé', 1),
(1560, 'Mobilier intérieur', 1),
(1920, 'Chambre', 1),
(1940, 'Cuisine', 1),
(2060, 'Décoration intérieure', 1),
(2220, 'Animal', 1),
(2280, 'Revues et journaux', 1),
(2403, 'Magazines, livres et BDs', 1),
(2462, 'Jeu occasion', 1),
(2522, 'Bureautique et papeterie', 1),
(2582, 'Mobilier extérieur', 1),
(2583, 'Autour de la piscine', 1),
(2585, 'Bricolage', 1),
(2705, 'Livre neuf', 1),
(2905, 'Jeu PC', 1)
ON CONFLICT (code) DO UPDATE
SET label = EXCLUDED.label;