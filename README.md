# depute_double_mandats

Croise le Répertoire National des Élus (RNE) pour identifier les députés exerçant simultanément un mandat local (commune, département, région).

## Données source

Fichiers issus du RNE sur [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/repertoire-national-des-elus-1/), mis à jour mensuellement.

## Résultat

Le fichier `output/depute_double_mandats.csv` contient une ligne par mandat local détecté.

| Colonne | Description |
|---|---|
| `nom` | Nom de l'élu |
| `prenom` | Prénom |
| `date_naissance` | Date de naissance (YYYY-MM-DD) |
| `sexe` | M / F |
| `dept_depute_code` | Code du département de la circonscription |
| `dept_depute_libelle` | Libellé du département |
| `num_circo` | Numéro de la circonscription législative |
| `libelle_circo` | Libellé de la circonscription |
| `date_debut_mandat_depute` | Date d'entrée à l'Assemblée nationale |
| `type_mandat_local` | Commune / Département / Région |
| `libelle_territoire` | Nom de la collectivité |
| `libelle_fonction_locale` | Maire, Adjoint, Conseiller… |
| `date_debut_mandat_local` | Date de début du mandat local |

## Mise à jour

Le workflow GitHub Actions se déclenche automatiquement **le 10 de chaque mois** et commit le CSV mis à jour.

Pour déclencher manuellement : onglet **Actions** → *Mise à jour double mandats* → **Run workflow**.

## Clé de déduplication

`prénom + nom + date de naissance` normalisés (sans accents, majuscules, tirets remplacés par des espaces).
