"""
depute_double_mandats — build_csv.py
Croise le fichier des députés (RNE) avec les élus municipaux,
départementaux et régionaux pour identifier les doubles mandats.
Une ligne par mandat local détecté.
"""

import io
import sys
import unicodedata
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Découverte dynamique des URLs RNE via l'API data.gouv.fr
# ---------------------------------------------------------------------------
DATASET_API = "https://www.data.gouv.fr/api/1/datasets/5c34944606e3e73d4a551889/"

RESOURCE_KEYWORDS = {
    "deputes":        "deputés",
    "municipaux":     "municipaux",
    "departementaux": "départementaux",
    "regionaux":      "régionaux",
}

def fetch_latest_urls() -> dict:
    print("Récupération des URLs depuis data.gouv.fr...")
    r = requests.get(DATASET_API, timeout=30)
    r.raise_for_status()
    resources = r.json().get("resources", [])

    # Debug : afficher tous les titres disponibles
    print("  Ressources disponibles :")
    for res in resources:
        print(f"    - {res.get('title', '(sans titre)')}")

    urls = {}
    for key, keyword in RESOURCE_KEYWORDS.items():
        match = next(
            (res.get("latest") or res.get("url") for res in resources
             if keyword.lower() in res.get("title", "").lower()),
            None
        )
        if not match:
            raise ValueError(f"Ressource introuvable pour : {keyword}")
        print(f"  {key}: {match}")
        urls[key] = match

    return urls

OUTPUT_PATH = "output/depute_double_mandats.csv"
CHUNK_SIZE = 50_000  # lignes par chunk pour le fichier communes (~600k lignes)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def normalize_str(s: str) -> str:
    """Supprime accents, met en majuscule, remplace tirets par espaces."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.upper().replace("-", " ").strip()


def make_key(nom: str, prenom: str, ddn: str) -> str:
    return f"{normalize_str(nom)}|{normalize_str(prenom)}|{ddn}"


def fix_date(date_str: str) -> str:
    """Corrige les dates décalées de 100 ans dans le fichier députés."""
    if not isinstance(date_str, str) or date_str == "":
        return date_str
    try:
        parts = date_str.split("-")
        year = int(parts[0])
        if year > 2024:
            parts[0] = str(year - 100)
        return "-".join(parts)
    except Exception:
        return date_str


# ---------------------------------------------------------------------------
# Téléchargement
# ---------------------------------------------------------------------------
def download(url: str) -> bytes:
    print(f"  Téléchargement : {url}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.content


def read_csv_bytes(data: bytes, **kwargs) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(data), sep=";", dtype=str, **kwargs)


# ---------------------------------------------------------------------------
# Construction de l'index des élus locaux
# Index : clé → liste de dicts (un dict par mandat)
# ---------------------------------------------------------------------------
def build_index_from_df(df: pd.DataFrame, type_mandat: str, index: dict) -> None:
    """Ajoute les entrées d'un DataFrame dans l'index."""
    for _, row in df.iterrows():
        nom = row.get("Nom de l'élu", "")
        prenom = row.get("Prénom de l'élu", "")
        ddn = row.get("Date de naissance", "")
        key = make_key(nom, prenom, ddn)
        if not key:
            continue

        if type_mandat == "Commune":
            territoire = row.get("Libellé de la commune", "")
            dept = row.get("Libellé du département", "")
            territoire_complet = f"{territoire} ({dept})"
        elif type_mandat == "Département":
            territoire_complet = row.get("Libellé du département", "")
        else:  # Région
            territoire_complet = row.get("Libellé de la région", row.get("Libellé de la collectivité à statut particulier", ""))

        mandat = {
            "type_mandat_local": type_mandat,
            "libelle_territoire": territoire_complet,
            "libelle_fonction_locale": row.get("Libellé de la fonction", ""),
            "date_debut_mandat_local": row.get("Date de début du mandat", ""),
        }

        index.setdefault(key, []).append(mandat)


def build_local_index(urls: dict) -> dict:
    index = {}

    # Régionaux
    print("\n[1/3] Conseillers régionaux...")
    data = download(urls["regionaux"])
    df = read_csv_bytes(data)
    build_index_from_df(df, "Région", index)
    print(f"      {len(df)} lignes chargées")

    # Départementaux
    print("\n[2/3] Conseillers départementaux...")
    data = download(urls["departementaux"])
    df = read_csv_bytes(data)
    build_index_from_df(df, "Département", index)
    print(f"      {len(df)} lignes chargées")

    # Municipaux en chunks
    print("\n[3/3] Conseillers municipaux (fichier volumineux)...")
    data = download(urls["municipaux"])
    total = 0
    reader = pd.read_csv(
        io.BytesIO(data),
        sep=";",
        dtype=str,
        chunksize=CHUNK_SIZE,
    )
    for chunk in reader:
        build_index_from_df(chunk, "Commune", index)
        total += len(chunk)
        print(f"      {total} lignes traitées...", end="\r")
    print(f"      {total} lignes chargées      ")

    print(f"\n  Index total : {len(index)} élus locaux uniques")
    return index


# ---------------------------------------------------------------------------
# Traitement des députés
# ---------------------------------------------------------------------------
def load_deputes(urls: dict) -> pd.DataFrame:
    print("\n[Députés] Chargement...")
    data = download(urls["deputes"])
    df = read_csv_bytes(data)
    print(f"  {len(df)} députés chargés")

    # Correction date de naissance
    df["Date de naissance"] = df["Date de naissance"].apply(fix_date)

    # Clé de jointure
    df["_key"] = df.apply(
        lambda r: make_key(r.get("Nom de l'élu", ""), r.get("Prénom de l'élu", ""), r.get("Date de naissance", "")),
        axis=1,
    )
    return df


# ---------------------------------------------------------------------------
# Jointure et construction du CSV final
# ---------------------------------------------------------------------------
def build_output(deputes: pd.DataFrame, index: dict) -> pd.DataFrame:
    rows = []
    matches = 0

    for _, dep in deputes.iterrows():
        key = dep["_key"]
        mandats_locaux = index.get(key)
        if not mandats_locaux:
            continue

        matches += 1
        for mandat in mandats_locaux:
            rows.append({
                "nom": dep.get("Nom de l'élu", ""),
                "prenom": dep.get("Prénom de l'élu", ""),
                "date_naissance": dep.get("Date de naissance", ""),
                "sexe": dep.get("Code sexe", ""),
                "dept_depute_code": dep.get("Code du département", ""),
                "dept_depute_libelle": dep.get("Libellé du département", ""),
                "num_circo": dep.get("Code de la circonscription législative", ""),
                "libelle_circo": dep.get("Libellé de la circonscription législative", ""),
                "date_debut_mandat_depute": dep.get("Date de début du mandat", ""),
                "type_mandat_local": mandat["type_mandat_local"],
                "libelle_territoire": mandat["libelle_territoire"],
                "libelle_fonction_locale": mandat["libelle_fonction_locale"],
                "date_debut_mandat_local": mandat["date_debut_mandat_local"],
            })

    print(f"\n  {matches} députés avec au moins un mandat local ({len(rows)} lignes au total)")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("depute_double_mandats — build_csv.py")
    print("=" * 60)

    urls = fetch_latest_urls()
    local_index = build_local_index(urls)
    deputes = load_deputes(urls)
    result = build_output(deputes, local_index)

    if result.empty:
        print("\nAucun double mandat détecté — vérifier les URLs.")
        sys.exit(1)

    result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nFichier généré : {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
