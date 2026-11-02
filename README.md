# ✍️ Air Writing — Mots, phrases et lecture vocale FR/EN

**Interaction gestuelle — MediaPipe · OpenCV · EasyOCR · scikit-learn**

Air Writing transforme les mouvements de l'index devant une webcam en un tracé,
puis propose du texte. Deux modes sont disponibles :

- **`words` (par défaut)** : OCR du mot ou de la ligne entière, avec aperçu régulier
  pendant le tracé. Pas besoin de valider chaque lettre.
- **`letters`** : ancien classifieur A–Z, une lettre à la fois, avec suggestions de
  mots français/anglais. `TAB` permet de changer de mode quand le canevas est vide.

**Le mode mots est expérimental.** EasyOCR est un OCR généraliste : écrivez des
lettres **détachées, grandes et proches de caractères imprimés**, de gauche à droite.
Il ne s'agit pas d'un modèle entraîné sur l'écriture aérienne ou sur les mots cursifs.
Les lettres qui se chevauchent, la cursive et les mouvements rapides peuvent échouer.
Aucune précision sur de vrais tracés webcam n'est revendiquée.

## 🎬 Démonstration existante

[![Démonstration Air Writing](docs/media/demo-preview.jpg)](https://github.com/NAZMO1/air-writing/blob/main/docs/media/air-writing-demo.mp4)

[▶ Voir la vidéo (21 secondes)](https://github.com/NAZMO1/air-writing/blob/main/docs/media/air-writing-demo.mp4)

Cette vidéo montre la version précédente, lettre par lettre ; elle ne valide pas
les performances du nouveau mode OCR.

## 🎮 Continuité : Turbo Duel — piloter avec la main

Après le tracé avec l’index, le suivi de main devient une manette : **le poignet pilote une voiture en 2D et le pouce déplié active le turbo**. Cette extension est un jeu **solo contre un bot**, sans multijoueur ni salle à code.

**[▶ Jouer dans le navigateur](https://turbo-duel-nazmo.adeptmole259.chatgpt.site)** · **[Code et instructions](extensions/turbo-duel/README.md)**

Les deux projets utilisent les 21 repères de **MediaPipe Hand Landmarker**. Air Writing utilise Python/OpenCV et la reconnaissance de texte ; Turbo Duel est un portage web du principe d’interaction, en JavaScript/Canvas. Il ne dépend pas de l’OCR ni du modèle de lettres.

Webcam : calibration du poignet, mouvement gauche/droite et haut/bas, turbo au pouce, pause automatique en cas de perte de main. Alternative clavier/tactile disponible. Les images sont traitées localement ; Internet sert au téléchargement des bibliothèques et du modèle. La détection reste sensible à l’éclairage et aux occlusions ; les tests avec repères simulés ne remplacent pas un essai à la webcam.

Pour lancer l’extension sans installer les dépendances Python du projet :

```bash
python -m http.server 8000 --directory extensions/turbo-duel --bind 127.0.0.1
```

Ouvrir `http://localhost:8000` dans un navigateur récent. Le navigateur Windows peut utiliser directement sa webcam même si le serveur est lancé sous WSL.

## Installation

### Windows : PowerShell et Python 3.12

Pour accéder à la webcam et aux voix Windows, lancez l'application avec Python
**natif Windows**. WSL peut servir à mettre à jour les sources, mais possède ses
propres installations Python et bibliothèques : une installation dans WSL ne
répare pas l'environnement Windows.

Vérifiez les interpréteurs disponibles depuis PowerShell :

```powershell
py -0p
```

Si Python 3.12 64 bits est disponible, créez un environnement séparé `.venv312`.
Un ancien `.venv` créé avec Python 3.15 reste en 3.15 même après l'installation
de Python 3.12. Cette procédure conserve l'ancien environnement et permet de
tester une installation propre ; elle ne garantit pas à elle seule de résoudre
une erreur de chargement de DLL.

Placez-vous dans le dossier du projet (adaptez le chemin si nécessaire) :

```powershell
cd C:\Users\Etudiant\air-writing-windows
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe --version
.\.venv312\Scripts\python.exe -m pip install --upgrade pip
```

Installez d'abord PyTorch et torchvision CPU, puis vérifiez leur import
**avant de poursuivre**. Un GPU n'est pas nécessaire (`gpu=False`) :

```powershell
.\.venv312\Scripts\python.exe -m pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv312\Scripts\python.exe -c "import torch, torchvision; print('Torch OK:', torch.__version__); print('Torchvision OK:', torchvision.__version__)"
```

Cette paire est issue des [commandes officielles PyTorch](https://pytorch.org/get-started/previous-versions/).
Si une commande échoue, arrêtez cette procédure et conservez la **première erreur complète**.

Lorsque les deux imports fonctionnent, installez les dépendances du projet :

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt
.\.venv312\Scripts\python.exe -m pip install --force-reinstall --no-deps opencv-contrib-python==5.0.0.93
```

**OpenCV graphique doit être réinstallé en dernier.** EasyOCR installe
`opencv-python-headless`, qui partage les fichiers `cv2` avec OpenCV graphique.
La réinstallation ci-dessus restaure la prise en charge de la fenêtre `imshow`.
Répétez-la après une réinstallation des dépendances OCR.

Préparez les modèles (connexion Internet nécessaire au téléchargement) :

```powershell
New-Item -ItemType Directory -Force data
curl.exe -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o data/hand_landmarker.task
.\.venv312\Scripts\python.exe -m src.text_recognition --download-models
```

Si `data/hand_landmarker.task` existe déjà, son téléchargement n'est pas nécessaire.
Vérifiez ensuite l'OCR et lancez l'application :

```powershell
.\.venv312\Scripts\python.exe -c "import torch, torchvision, easyocr; print('Imports OCR OK')"
.\.venv312\Scripts\python.exe main.py
```

Ces commandes utilisent toujours le même interpréteur : il n'est pas nécessaire
d'activer l'environnement ni de modifier la politique d'exécution PowerShell.
Sur CPU, l'aperçu OCR peut prendre plusieurs secondes.

### Mettre à jour sous Windows, avec Git ou WSL

Fermez l'application avant la mise à jour. Si Git est disponible dans PowerShell,
exécutez `git pull origin main` depuis le dossier du dépôt.

Si PowerShell affiche « git n'est pas reconnu », mais que Git est installé dans
WSL, cette commande PowerShell met à jour **le même dossier Windows** :

```powershell
wsl --cd /mnt/c/Users/Etudiant/air-writing-windows git pull origin main
```

Ou, depuis un terminal WSL :

```bash
cd /mnt/c/Users/Etudiant/air-writing-windows
git pull origin main
```

Adaptez le chemin à votre dossier. Si Git signale des modifications locales,
examinez-les et sauvegardez-les avant de poursuivre.
Revenez ensuite dans PowerShell et actualisez les dépendances et modèles :

```powershell
cd C:\Users\Etudiant\air-writing-windows
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt -r requirements-ocr.txt
.\.venv312\Scripts\python.exe -m pip install --force-reinstall --no-deps opencv-contrib-python==5.0.0.93
.\.venv312\Scripts\python.exe -m src.text_recognition --download-models
.\.venv312\Scripts\python.exe main.py
```

Créez d'abord `.venv312` avec la procédure précédente s'il n'existe pas.

### Linux / macOS

Utilisez un Python compatible avec les dépendances et une webcam :

```bash
git clone https://github.com/NAZMO1/air-writing.git
cd air-writing
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-ocr.txt
python -m pip install --force-reinstall --no-deps opencv-contrib-python==5.0.0.93
mkdir -p data
curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o data/hand_landmarker.task
python -m src.text_recognition --download-models
python main.py
```

Pour installer PyTorch séparément, suivez les [instructions officielles adaptées
à votre système](https://pytorch.org/get-started/locally/). La commande CPU Windows
ci-dessus n'est pas une commande universelle pour tous les systèmes.

### Modèles et mode lettres

Les poids OCR français/anglais sont conservés dans `data/easyocr/` et exclus de
Git. Ils restent réutilisables lorsque vous changez d'environnement Python.
Au lancement normal, le téléchargement automatique est désactivé.
Les images de caméra, les tracés et le texte ne sont envoyés à aucune API ;
la reconnaissance et la synthèse sont locales.

Le mode mots ne nécessite pas `data/letter_model.pkl`. Pour le mode **lettres**
uniquement, entraînez le modèle A–Z s'il manque, puis lancez ce mode :

```powershell
# Windows PowerShell
.\.venv312\Scripts\python.exe train_model.py
.\.venv312\Scripts\python.exe main.py --mode letters
```

Sous Linux/macOS avec l'environnement activé : `python train_model.py`, puis
`python main.py --mode letters`. Aucun réentraînement A–Z n'est nécessaire pour l'OCR.

### Dépannage Windows / OCR

- **`WinError 126` sur `torch_python.dll`** : une DLL ou l'une de ses dépendances
  ne peut pas être chargée. Cela ne prouve pas, à lui seul, que la version Python
  est incompatible. Installez ou réparez le
  [Microsoft Visual C++ Redistributable x64](https://aka.ms/vc14/vc_redist.x64.exe)
  **sous Windows**, puis relancez le test d'import dans un nouveau processus.
  Consultez aussi la [documentation Microsoft](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist).
- **`torch can only be initialized once per process`** : ce message peut suivre
  un premier import échoué. Fermez l'application et utilisez la commande de test
  ci-dessous pour obtenir l'erreur initiale, avant de relancer l'OCR.
- **`No module named 'spellchecker'`** : le paquet à installer s'appelle
  `pyspellchecker`, tandis que son module Python s'appelle `spellchecker`.
  Il figure dans `requirements.txt`.
- **Fenêtre OpenCV indisponible** : réinstallez OpenCV graphique en dernier avec
  la commande `--force-reinstall --no-deps` de la procédure d'installation.
- **Poids OCR absents** : relancez `-m src.text_recognition --download-models`
  avec l'interpréteur utilisé pour lancer le projet.
- Les messages MediaPipe concernant les *feedback tensors* ou `NORM_RECT`
  ne suffisent pas à diagnostiquer un échec OCR. Cherchez le traceback ou le
  message `OCR indisponible` qui suit.

Test isolé PyTorch, à exécuter dans PowerShell depuis le dossier du projet :

```powershell
.\.venv312\Scripts\python.exe -c "import torch; print('Torch OK:', torch.__version__)"
```

Installation ciblée si `spellchecker` est encore absent :

```powershell
.\.venv312\Scripts\python.exe -m pip install pyspellchecker
```

## Choisir sa langue avec la main

Au démarrage, le dessin est désactivé tant que la langue n'est pas choisie :

| Choix | Geste maintenu pendant 1 seconde | Alternative clavier |
| --- | --- | --- |
| Français | Index seul levé | `F` |
| Anglais | Index et majeur levés, autres doigts repliés | `E` |

Le pouce est ignoré pour ces deux gestes. Après sélection, repliez les doigts une
fois avant de dessiner, pour éviter de transformer le geste de sélection en trait.
`L` rouvre ce menu lorsque le canevas est vide. Le texte déjà validé est conservé.
La langue sélectionne l'alphabet OCR autorisé, le dictionnaire en mode lettres et
la voix système ; elle ne traduit pas le texte et ne comprend pas son sens.

## Écrire des mots et des phrases

1. Levez l'index seul pour tracer un mot ou une courte ligne de plusieurs mots.
2. Levez **index + majeur** pour déplacer la main sans dessiner, par exemple entre
   deux traits ou deux lettres. Ce geste ne valide pas automatiquement le mot.
3. L'OCR analyse périodiquement le canevas entier dans un thread séparé. L'aperçu
   reste provisoire : il n'est pas ajouté au document ni lu à voix haute.
4. Maintenez la **paume ouverte 1 seconde**, ou appuyez sur **Espace**, pour valider
   le tracé en texte, ajouter un espace et libérer le canevas pour le mot suivant.
   Un poing maintenu 1 seconde réalise la même validation en mode mots.
5. Continuez ainsi votre phrase. Les espaces déjà présents entre les mots d'une
   ligne peuvent aussi être reconnus par l'OCR. Les touches `.`, `!` et `?` permettent
   de ponctuer explicitement le texte.
6. Appuyez sur **Entrée** pour valider le tracé restant, puis lire **tout le texte**.

Pendant une validation OCR finale, le dessin est temporairement suspendu pour
éviter de perdre des traits arrivés après la capture. `x` annule cette validation
et efface le tracé. Si l'OCR ne reconnaît rien ou obtient un score trop faible,
le tracé reste disponible et aucun texte n'est ajouté. Les résultats arrivant
après un effacement ou un changement de langue ne peuvent pas modifier le document.

Il n'y a pas de correction orthographique silencieuse. Un score OCR élevé n'est
pas une garantie : vérifiez le texte affiché avant de l'utiliser.

### Lecture en continu

`A` active/désactive la **lecture automatique des nouveaux mots ou lignes validés**.
La voix ne lit pas chaque aperçu partiel ni chaque lettre. Les éléments confirmés
sont lus dans l'ordre grâce à une file limitée à 20 éléments en attente. Si elle
est pleine, un message invite à utiliser Entrée pour relire le document.

Entrée remplace la lecture en cours et sa file par la lecture du texte complet.
Désactiver la lecture automatique, changer de langue, effacer tout ou quitter
arrête la voix et vide sa file. Les textes de plus de 2 000 caractères ne sont pas lus
par une demande unique. La caméra reste active pendant la parole.

### Commandes

| Action | Geste / touche |
| --- | --- |
| Tracer | Index seul levé |
| Déplacer sans tracer | Index + majeur levés |
| Valider et ajouter un espace | Paume ouverte 1 s / Espace |
| Valider | Poing 1 s (ajoute aussi un espace en mode mots) |
| Valider le tracé et lire tout le texte | Entrée / `V` |
| Lecture automatique des nouveaux mots validés | `A` |
| Lire le dernier mot validé | `B` |
| Ajouter de la ponctuation | `.`, `!`, `?` |
| Revenir au choix de langue | `L`, canevas vide |
| Changer mots / lettres | `TAB`, canevas vide |
| Effacer le tracé / annuler l'OCR en cours | `x` |
| Effacer texte, tracé et lecture | `c` |
| Supprimer le dernier caractère du texte validé | Retour arrière, canevas vide |
| Valider une lettre sans lire (mode lettres) | `R` |
| Accepter une suggestion et ajouter un espace (mode lettres) | `1`, `2`, `3`, canevas vide |
| Quitter | `Q` |

Les touches de commande alphabétiques s'utilisent en minuscules, sauf `F`/`E`
ci-dessus qui désignent les touches `f`/`e`. La fenêtre OpenCV doit avoir le focus.
**Changement par rapport à l'ancienne version : la paume ajoute un espace ; `c`
efface tout. Entrée valide puis lit ; `R` valide une lettre sans lire.**

## Voix française et anglaise

Installez les voix FR/EN dans les paramètres de langue/parole de Windows ou de
macOS. Sous Ubuntu/Debian, installez le moteur nécessaire à pyttsx3 :

```bash
sudo apt install espeak-ng libespeak1
python -m src.speech --language fr --text "Bonjour tout le monde"
python -m src.speech --language en --text "Hello world"
```

Une voix absente produit un message explicite sans empêcher d'écrire. OpenCV
retire les accents de l'affichage, mais le texte interne et la voix les conservent.
Pour éviter que certaines voix épellent les mots en majuscules, les mots connus du
dictionnaire (`EAU`, `BONJOUR`, `HELLO`…) sont mis en minuscules uniquement dans la
copie envoyée à la voix. Le document et les sigles inconnus restent inchangés.
Si le texte reconnu affiche `E A U`, les espaces font réellement partie du texte :
écrivez les lettres plus près et validez uniquement à la fin du mot, ou utilisez
le mode lettres sans ajouter d'espace entre chaque lettre.

## Mode lettres et modèle existant

Le mode `letters` conserve le MLP A–Z : tracer une lettre, puis maintenir le poing
1 seconde ou appuyer sur `R`. Écrire les lettres suivantes au même endroit après
validation. Les dictionnaires de pyspellchecker proposent jusqu'à trois corrections
(`1`/`2`/`3`), y compris des variantes accentuées françaises. Espace conserve les noms
propres et mots inconnus tels quels. Il faut valider ou effacer le tracé avant de
choisir une suggestion.

`train_model.py` produit par défaut jusqu'à 7 800 exemples synthétiques (300 par
lettre) et entraîne un MLP à couches cachées de 128 et 64 neurones. Le prétraitement
recadre le tracé, le centre dans 28 × 28 et fournit 784 valeurs normalisées. Une
lettre est acceptée avec un score ≥ 0,60 et une marge ≥ 0,15. La validation synthétique
ne mesure pas la précision sur webcam. Essai court :

```bash
python train_model.py --samples 100 --iterations 40
```

## Architecture

| Composant | Rôle |
| --- | --- |
| `main.py` | Caméra, menus de langue, commandes et affichage |
| `src/hand_tracker.py` | MediaPipe Hand Landmarker et 21 repères |
| `src/gestures.py` | Angles articulaires, maintien des gestes et lissage du tracé |
| `src/text_recognition.py` | Canevas vers OCR de ligne, préparation des poids et worker asynchrone |
| `src/editor.py` | Aperçu, validation, protection contre les résultats périmés |
| `src/words.py` | Document, espaces, ponctuation et suggestions FR/EN |
| `src/speech.py` | Processus vocal local et file de lecture |
| `src/classifier.py` / `src/preprocessing.py` | Alternative de classification A–Z |
| `tests/` | Tests sans caméra et intégration avec caméra/OCR/voix simulés |

Le suivi coupe les traits lors d'une perte de main ou d'un grand saut de position.
Les gestes reposent sur les angles articulaires ; occlusions, lumière faible et
main de profil peuvent encore les perturber. La perte de main ne valide rien.
Le worker n'accepte qu'un travail OCR à la fois ; les aperçus sont demandés au plus
une fois par seconde. Ce n'est pas une promesse d'un résultat par seconde : le temps
réel dépend du CPU et de la complexité du tracé. Une pause du dessin permet d'obtenir
un aperçu correspondant au canevas actuel.

## Vérification

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py src tests
# Essai facultatif avec les vrais poids OCR déjà préparés :
python -m unittest discover -s tests -p 'check_real_ocr.py' -v
```

Les tests automatiques couvrent : aperçu sans validation, phrase complète + Entrée,
espaces et accents, résultat périmé après effacement/changement de langue, OCR lent,
rejet d'un mot incertain, indisponibilité des poids, gestes maintenus, lecture vocale
en file et arrêt propre. Une intégration simule le parcours dessin → OCR → Entrée →
voix. Ils s'ajoutent aux tests existants du classifieur et des dictionnaires.

Les tests avec poids réels utilisent des caractères **imprimés synthétiques** ; ils
ne remplacent pas un test sur tracés aériens. Avant utilisation, essayer à la webcam :
FR puis EN, BONJOUR puis HELLO, plusieurs traits d'une lettre, déplacement à deux
doigts, paume pour l'espace, Entrée pour lire, `A` pour la lecture continue et `x`
pendant une reconnaissance. Vérifier également les voix FR/EN sur les haut-parleurs.

## Pistes suivantes

- Collecter de vrais tracés de mots et constituer un jeu de test indépendant.
- Évaluer un modèle de reconnaissance manuscrite entraîné sur ces tracés, notamment
  pour la cursive ; l'OCR généraliste actuel n'offre pas cette garantie.
- Mesurer les erreurs de mots/caractères et la latence sur plusieurs ordinateurs.

Références : [EasyOCR](https://github.com/JaidedAI/EasyOCR),
[API OCR](https://www.jaided.ai/easyocr/documentation/),
[MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker).
