# DEKAL Books

Plateforme web de publication et de consultation de PDF, construite avec Flask, SQLite, HTML, CSS et JavaScript vanilla.

## Fonctionnalités

- catalogue de PDF ;
- recherche instantanée côté API ;
- filtres par catégorie ;
- tri par récence, téléchargements ou A-Z ;
- pagination ;
- page de détail avec prévisualisation PDF ;
- téléchargement réel avec compteur ;
- authentification administrateur par session ;
- ajout, modification et suppression de PDF ;
- interface responsive pensée pour Android ;
- préparation pour Render.

## 1. Installation locale

Python 3.11+ est recommandé.

### Linux / macOS

```bash
cd DEKAL_BOOKS/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows

```powershell
cd DEKAL_BOOKS\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurer l'administrateur

Copiez `.env.example` vers `.env`.

```bash
cp .env.example .env
```

Sous Windows, copiez simplement le fichier manuellement.

Générez un hash de mot de passe :

```bash
python generate_admin_hash.py
```

Copiez la valeur `ADMIN_PASSWORD_HASH=...` affichée dans `.env`.

Définissez également :

```env
SECRET_KEY=une-valeur-longue-et-aleatoire
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=...
MAX_FILE_SIZE_MB=25
```

Le mot de passe en clair n'est jamais stocké dans la base.

## 3. Base de données

La base `backend/dekal_books.db` est créée automatiquement au démarrage. Le dossier `backend/uploads/pdfs/` est également créé automatiquement.

## 4. Lancer localement

Depuis `DEKAL_BOOKS/backend` :

```bash
python app.py
```

Puis ouvrez :

```text
http://127.0.0.1:5000
```

Administration :

```text
http://127.0.0.1:5000/login.html
```

## 5. Ajouter un PDF

Connectez-vous avec le compte administrateur, remplissez le formulaire et choisissez un vrai fichier `.pdf`. Le fichier est stocké dans `backend/uploads/pdfs/` et ses métadonnées dans SQLite.

## 6. API

- `GET /api/books`
- `GET /api/books/<id>`
- `GET /api/books/category/<category>`
- `GET /api/books/<id>/download`
- `POST /api/books`
- `PUT /api/books/<id>`
- `DELETE /api/books/<id>`
- `POST /api/admin/login`
- `POST /api/admin/logout`
- `GET /api/admin/me`

## 7. Render

Le fichier `render.yaml` configure le service Web.

Le serveur est lancé avec :

```bash
gunicorn app:app
```

Le `rootDir` Render est `backend`.

### Important concernant SQLite et les uploads

SQLite et les fichiers locaux conviennent à un prototype, à un petit projet ou à un environnement avec disque persistant. Sur Render, si vous avez besoin que les PDF et la base persistent durablement lors des redéploiements/recréations d'instance, configurez un Persistent Disk ou migrez ensuite vers une base et un stockage externes.

## 8. Git

Ne commitez jamais `.env`, la base SQLite de production ou des secrets. Le `.gitignore` fourni protège ces fichiers.

## 9. Démonstration

Le projet inclut un script optionnel `backend/seed_demo.py` qui crée quelques métadonnées et de petits PDF de démonstration. Il n'est pas exécuté automatiquement.
