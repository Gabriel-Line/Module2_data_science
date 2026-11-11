
import pandas as pd
from datetime import datetime, timedelta
 
# Lire le fichier placé directement dans le même dossier
with open("S06_sms_urgence.txt", encoding="utf-8") as f:
    lignes = f.read().strip().splitlines()

entete, messages = lignes[0], lignes[1:]          # en-tête + SMS
print(f"{len(messages)} SMS lus. En-tête : {entete}")
 
# Transformer un SMS brut en dictionnaire, ou lever une erreur
def lire_sms(texte):
    """Découpe 'LIEU|THEME|STATUT|NOMBRE|HORODATAGE'.
    Lève ValueError si le SMS est invalide."""
    morceaux = [m.strip() for m in texte.split("|")]
    if len(morceaux) != 5:
        raise ValueError(f"{len(morceaux)} éléments au lieu de 5")
    lieu, theme, statut, nombre, horodatage = morceaux
    if not nombre.isdigit():
        raise ValueError("Le nombre doit contenir uniquement des chiffres")
    return {
        "lieu": lieu.title(),
        "theme": theme.upper(),
        "statut": statut.upper(),
        "nombre": int(nombre),
        "horodatage": datetime.strptime(horodatage, "%Y-%m-%d %H:%M"),
    }
 
# Séparer les SMS valides et les SMS rejetés
valides, rejets = [], []
for numero, texte in enumerate(messages, start=1):
    try:
        valides.append(lire_sms(texte))
    except ValueError as erreur:
        rejets.append({"ligne": numero, "sms": texte, "motif": str(erreur)})
 
# Contrôle 1 : SMS lus = valides + rejetés
assert len(messages) == len(valides) + len(rejets)
print(f"Validés : {len(valides)} | Rejetés : {len(rejets)}")
print("\n--- REJETS ---")
print(pd.DataFrame(rejets))
print("\n--- VALIDES ---")
print(pd.DataFrame(valides))
 
# Dédoublonnage : même lieu, thème, statut, nombre dans une fenêtre de 3 h
FENETRE = timedelta(hours=3)
CLES = ["lieu", "theme", "statut", "nombre"]
evenements = []
for sms in sorted(valides, key=lambda s: s["horodatage"]):
    for ev in evenements:
        if all(ev[c] == sms[c] for c in CLES) and \
           sms["horodatage"] - ev["premier_sms"] <= FENETRE:
            ev["nb_sms"] += 1          # renvoi du même événement
            break
    else:
        evenements.append({**{c: sms[c] for c in CLES},
                           "premier_sms": sms["horodatage"], "nb_sms": 1})
 
evenements = pd.DataFrame(evenements)
 
# Contrôle 2 : chaque SMS valide est rattaché à un événement
assert evenements["nb_sms"].sum() == len(valides)
print("\n--- ÉVÉNEMENTS ---")
print(evenements)


# Conversion de la liste valides en DataFrame
df_valides = pd.DataFrame(valides)

# Regroupement par thème et sommation de la colonne nombre (total brut)
total_sms_brut = df_valides.groupby("theme")["nombre"].sum()

# Regroupement similaire sur le DataFrame des événements (total par événement)
total_evenements = evenements.groupby("theme")["nombre"].sum()

# Fusion des deux résultats dans un nouveau DataFrame
tableau_comparatif = pd.DataFrame({
    "personnes_si_on_additionne_les_sms": total_sms_brut,
    "personnes_par_evenement": total_evenements
})

# Affichage du tableau comparatif final
print(tableau_comparatif)