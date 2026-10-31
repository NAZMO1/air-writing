# Turbo Duel — Air Control

**De l’écriture dans l’air au pilotage par gestes.** Extension web d’[Air Writing](https://github.com/NAZMO1/air-writing) : un jeu de football motorisé en 2D, solo contre un bot, contrôlé avec une seule main devant une webcam.

**[Jouer à la version hébergée](https://turbo-duel-nazmo.adeptmole259.chatgpt.site)**

La version hébergée a une interface React ; cette extension autonome utilise les **mêmes modules de suivi de main, de commandes gestuelles, de physique et de rendu**, avec une interface HTML/JavaScript sans compilation.

## Lancer en local

Depuis la racine d’Air Writing :

```bash
python -m http.server 8000 --directory extensions/turbo-duel --bind 127.0.0.1
```

Ouvrir **http://localhost:8000** dans Chrome/Edge récent et autoriser la caméra. `python3` convient aussi sous Linux. Une page `file://` ou HTTP sur une adresse distante n’est pas une méthode prise en charge ; la webcam exige localhost ou HTTPS. Si le serveur tourne sous WSL, le navigateur Windows utilise sa propre webcam : aucune capture OpenCV depuis WSL n’est nécessaire pour cette extension.

## Jouer

- Cliquer **Activer la caméra**. Montrer une seule main de face, avec le poignet près du centre ; rester immobile environ une seconde pour calibrer.
- Déplacer le **poignet** à gauche/droite pour avancer/reculer ; le lever pour voler et le baisser pour descendre. L’aperçu est en miroir. Revenir à la position neutre ralentit la voiture et stabilise l’altitude.
- **Déplier le pouce** à l’écart de la paume pour le turbo ; le replier pour recharger. Les autres doigts sont libres.
- **Recentrer** réinitialise le point neutre ; la sensibilité règle l’amplitude du geste.
- Main perdue : commandes neutralisées et match en pause. Le retour de la main reprend le match, sauf pause manuelle. Changer d’onglet éteint la webcam ; il faut la relancer.
- Le **mode clavier** lance un nouveau match sans webcam : flèches ou Q/D, Espace pour sauter, Maj pour le turbo. Des boutons tactiles sont disponibles.

Voiture bleue : toi ; orange : bot. Match de 2 minutes ou premier à 5 buts ; but en or en cas d’égalité. Aucune salle multijoueur, aucun code de connexion.

## Lien technique avec Air Writing

| Air Writing | Turbo Duel |
| --- | --- |
| Python + OpenCV + MediaPipe | JavaScript + Canvas + MediaPipe |
| Index : tracer des lettres et des mots | Poignet (repère 0) : déplacement en 2D |
| Gestes : tracer, valider, espacer | Pouce (repères 1–4) : turbo |
| OCR / classifieur puis lecture vocale | Commandes continues puis simulation physique |

Les deux expériences utilisent **les 21 repères de MediaPipe Hand Landmarker**. Cette extension est un portage web du principe d’interaction ; elle n’appelle pas le programme Python et ne réutilise pas le classifieur A–Z pour le jeu. Elle ne nécessite ni EasyOCR, ni modèle de lettres, ni synthèse vocale.

## Architecture

- `gesture/camera.mjs` : webcam, chargement MediaPipe, GPU avec repli CPU, aperçu et arrêt des ressources.
- `gesture/wrist-controls.mjs` : calibration, miroir, lissage, zone neutre, détection géométrique du pouce et stabilisation temporelle.
- `physics.mjs` : physique à petits pas, vol, collisions, scores et chronomètre.
- `game.mjs` : rendu Canvas et bot local, sans réseau multijoueur.
- `main.mjs` : interface et cycle de vie du match.
- `tests/` : tests de physique, gestes simulés et erreurs caméra.

Avec Node.js récent : `node --test extensions/turbo-duel/tests/*.test.mjs` depuis la racine du dépôt. Les tests automatisés ne remplacent pas un essai des vrais gestes devant une webcam. Aucun taux de précision réel n’est revendiqué.

## Confidentialité et limites

Les images sont analysées **dans le navigateur**, sans enregistrement ni envoi à une API. Aucun microphone demandé. La bibliothèque MediaPipe et le WASM sont téléchargés depuis jsDelivr ; le modèle est téléchargé depuis Google. Ces requêtes de fichiers nécessitent Internet et exposent les métadonnées réseau habituelles aux hébergeurs, mais pas les images de la caméra.

Lumière faible, main de profil, occlusions ou changement de main peuvent perturber le suivi. Garder le poignet et le pouce dans le cadre. Les seuils du pouce sont géométriques, pas un modèle personnalisé entraîné sur toutes les mains.

Le code a été développé avec une assistance IA. La continuité à présenter sur LinkedIn est : **suivi de main → interprétation des gestes → interaction en temps réel**, appliqué d’abord à l’écriture puis au jeu.
