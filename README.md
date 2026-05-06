# 🏛️ Députés & Cumul des Mandats

**Qui sont les député(e)s qui siègent aussi localement ?**

Ce projet automatise le croisement des données du **Répertoire National des Élus (RNE)** pour identifier les députés de l'Assemblée nationale qui exercent simultanément un mandat local (commune, département ou région).

L'objectif est d'offrir une vision claire et actualisée du paysage politique français en un seul fichier actionnable et transparent.

---

## 🔍 Pourquoi ce projet ?

Ce script permet de :

1.  **Identifier** ces doubles fonctions instantanément sans fouiller manuellement dans les fichiers de l'État.
2.  **Suivre** l'évolution des mandats au fil des mises à jour officielles (mises à jour mensuelles).
3.  **Faciliter** le travail d'analyse pour les journalistes, chercheurs et citoyens engagés.

---

## 📊 Les Données

Le projet s'appuie exclusivement sur les données officielles de [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/repertoire-national-des-elus-1/), la source de référence pour le Répertoire National des Élus (RNE) publié par le Ministère de l'intérieur.

### 📁 Résultat
Le fichier final est généré automatiquement et disponible ici :  
👉 [**`output/depute_double_mandats.csv`**](./output/depute_double_mandats.csv)

### 📋 Structure du fichier
Le CSV contient une ligne par mandat local détecté pour chaque député :

| Colonne | Description |
| :--- | :--- |
| `nom`, `prenom`, `sexe` | Identité de l'élu |
| `date_naissance` | Date de naissance (pour la déduplication) |
| `dept_depute_code` / `libelle` | Département de la circonscription législative |
| `num_circo` / `libelle_circo` | Détails de la circonscription |
| `date_debut_mandat_depute` | Date d'entrée à l'Assemblée nationale |
| `type_mandat_local` | Commune, Département ou Région |
| `libelle_territoire` | Nom de la collectivité locale |
| `libelle_fonction_locale` | Maire, Adjoint, Conseiller, etc. |
| `date_debut_mandat_local` | Date de début du mandat local |

---

## ⚙️ Automatisation (GitHub Actions)

Pas besoin de lancer de script sur votre machine, le projet est autonome :

* **Mise à jour programmée :** Le workflow se déclenche automatiquement **le 10 de chaque mois**.
* **Mise à jour manuelle :** Si vous souhaitez forcer une mise à jour :
    1.  Allez dans l'onglet **Actions** de ce dépôt.
    2.  Sélectionnez le workflow `Mise à jour double mandats`.
    3.  Cliquez sur `Run workflow`.

---

## 🧪 Méthodologie technique

Pour garantir la fiabilité des données et éviter les homonymes (ex: deux "Jean Dupont"), nous utilisons une **clé de déduplication unique** :
`prénom + nom + date de naissance`

Ces champs sont normalisés avant comparaison :
* Passage en minuscules.
* Suppression des accents.
* Remplacement des tirets par des espaces.

---

## 🤝 Contribuer

Les suggestions d'amélioration (ajout de mandats EPCI, statistiques, visualisations) sont les bienvenues ! 

1. Forkez le projet.
2. Créez une branche (`git checkout -b feature/ma-super-idee`).
3. Proposez une **Pull Request**.

---
*Projet propulsé par l'envie d'avoir envie avec le concours des données ouvertes de la République Française 🇫🇷*
