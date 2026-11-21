"""Jeu de tests du module extensions.py.

Chaque résultat attendu a été établi à la main à partir de la définition
des extensions de Reiter (et des exemples du cours), pas à partir de la
sortie du programme.

Lancement :  python test_extensions.py
"""

import sys

from defauts import Theorie
from formules import lire_formule
from raisonnement import consequence
import json
import os
import tempfile

from extensions import (
    applicable, generer_extensions, sceptique, credule,
    litteraux, extensions_contenant,
    extensions_vers_donnees, extensions_depuis_donnees, equivalentes,
    expliquer_extension,
)

echecs = 0


def verifier(condition, libelle):
    """Affiche PASS ou FAIL pour un test."""
    global echecs
    print(("PASS  " if condition else "FAIL  ") + libelle)
    if not condition:
        echecs += 1


def theorie(formules, defauts):
    """Construit une théorie (W, D) à partir de textes."""
    t = Theorie()
    for f in formules:
        t.ajouter_formule(f)
    for d in defauts:
        t.ajouter_defaut(d)
    return t


def f(texte):
    return lire_formule(texte)


# ----------------------------------------------------------------------
# Exemples du cours
# ----------------------------------------------------------------------
print("--- Cours, slide 18 : W={A}  D={A:B/C, A:¬C/¬B} ---")
T = theorie(["A"], ["A : B / C", "A : ~C / ~B"])
E = generer_extensions(T)
verifier(len(E) == 2, "2 extensions")
verifier(E[0].defauts_appliques == [1] and E[1].defauts_appliques == [2],
         "E1 applique d1, E2 applique d2")
verifier(consequence(E[0].base, f("C")), "E1 contient C")
verifier(consequence(E[1].base, f("~B")), "E2 contient ¬B")
verifier(credule(E, f("C")), "C est crédule")
verifier(not sceptique(E, f("C")), "C n'est pas sceptique")
verifier(sceptique(E, f("A")), "A est sceptique (fait de W)")
verifier(not credule(E, f("B")), "B n'est pas crédule")
verifier(litteraux(E[0]) == ["A", "C"], "littéraux de E1 : A, C")
verifier(litteraux(E[1]) == ["A", "¬B"], "littéraux de E2 : A, ¬B")
verifier(extensions_contenant(E, f("C")) == [1], "C est dans E1 seulement")
verifier(extensions_contenant(E, f("A")) == [1, 2], "A est dans E1 et E2")

print("--- Cours, slide 21 : W=∅  D={:A/B, :C/¬A} ---")
T = theorie([], [": A / B", ": C / ~A"])
E = generer_extensions(T)
verifier(len(E) == 1, "1 seule extension")
verifier(consequence(E[0].base, f("~A")), "l'extension contient ¬A")
verifier(not consequence(E[0].base, f("B")), "l'extension ne contient pas B")
verifier(E[0].defauts_appliques == [2], "seul d2 est appliqué")
verifier(sceptique(E, f("~A")), "¬A est sceptique")
verifier(not sceptique(E, f("B")), "B n'est pas sceptique")

# ----------------------------------------------------------------------
# Exemple de l'énoncé
# ----------------------------------------------------------------------
print("--- Énoncé : W={o, p→o, p→¬v}  D={o:v/v, a:c/b} ---")
T = theorie(["o", "p -> o", "p -> ~v"], ["o : v / v", "a : c / b"])
E = generer_extensions(T)
verifier(len(E) == 1, "1 extension")
verifier(E[0].defauts_appliques == [1], "seul d1 est appliqué")
verifier(litteraux(E[0]) == ["o", "¬p", "v"], "littéraux : o, ¬p, v")
verifier(sceptique(E, f("v")), "v est sceptique")
verifier(not credule(E, f("b")), "b n'est pas crédule (d2 inapplicable)")

# ----------------------------------------------------------------------
# Théories classiques
# ----------------------------------------------------------------------
print("--- Diamant de Nixon ---")
T = theorie(
    ["Quaker(nixon)", "Republicain(nixon)"],
    ["Quaker(nixon) : Pacifiste(nixon) / Pacifiste(nixon)",
     "Republicain(nixon) : ~Pacifiste(nixon) / ~Pacifiste(nixon)"])
E = generer_extensions(T)
verifier(len(E) == 2, "2 extensions")
verifier(credule(E, f("Pacifiste(nixon)")), "Pacifiste crédule")
verifier(credule(E, f("~Pacifiste(nixon)")), "¬Pacifiste crédule")
verifier(not sceptique(E, f("Pacifiste(nixon)")), "Pacifiste non sceptique")
verifier(not sceptique(E, f("~Pacifiste(nixon)")), "¬Pacifiste non sceptique")
verifier(sceptique(E, f("Quaker(nixon)")), "Quaker sceptique")

print("--- Tweety (cas normal) ---")
T = theorie(["Oiseau(tweety)"],
            ["Oiseau(tweety) : Vole(tweety) / Vole(tweety)"])
E = generer_extensions(T)
verifier(len(E) == 1, "1 extension")
verifier(sceptique(E, f("Vole(tweety)")), "Vole(tweety) sceptique")

print("--- Pingouin (exception : le défaut est bloqué) ---")
T = theorie(
    ["Pingouin(tweety)", "Pingouin(tweety) -> Oiseau(tweety)",
     "Pingouin(tweety) -> ~Vole(tweety)"],
    ["Oiseau(tweety) : Vole(tweety) / Vole(tweety)"])
E = generer_extensions(T)
verifier(len(E) == 1, "1 extension")
verifier(E[0].defauts_appliques == [], "aucun défaut appliqué")
verifier(sceptique(E, f("~Vole(tweety)")), "¬Vole(tweety) sceptique")
verifier(not credule(E, f("Vole(tweety)")), "Vole(tweety) non crédule")

# ----------------------------------------------------------------------
# Cas limites
# ----------------------------------------------------------------------
print("--- Aucune extension : D={:A/¬A} ---")
T = theorie([], [": A / ~A"])
E = generer_extensions(T)
verifier(len(E) == 0, "0 extension")
verifier(sceptique(E, f("A")) is None, "sceptique non défini (None)")
verifier(credule(E, f("A")) is None, "crédule non défini (None)")

print("--- Aucun défaut : l'extension est Th(W) ---")
E = generer_extensions(theorie(["A", "A -> B"], []))
verifier(len(E) == 1, "1 extension")
verifier(sceptique(E, f("B")), "B conséquence de W")
verifier(not credule(E, f("C")), "C n'est pas conséquence de W")

print("--- Théorie vide ---")
E = generer_extensions(theorie([], []))
verifier(len(E) == 1, "1 extension (Th(∅))")
verifier(sceptique(E, f("A | ~A")), "une tautologie est sceptique")
verifier(not credule(E, f("A")), "A n'est pas crédule")

print("--- Prérequis non démontré : D={A:B/B}, W=∅ ---")
E = generer_extensions(theorie([], ["A : B / B"]))
verifier(len(E) == 1 and E[0].defauts_appliques == [], "défaut non appliqué")
verifier(not credule(E, f("B")), "B n'est pas crédule")

print("--- Justification contredite par W : W={¬B}, D={:B/C} ---")
E = generer_extensions(theorie(["~B"], [": B / C"]))
verifier(len(E) == 1 and E[0].defauts_appliques == [], "défaut bloqué")
verifier(not credule(E, f("C")), "C n'est pas crédule")

print("--- Justification incohérente : D={:A∧¬A/B} ---")
E = generer_extensions(theorie([], [": A & ~A / B"]))
verifier(len(E) == 1 and E[0].defauts_appliques == [],
         "défaut jamais applicable")
verifier(not credule(E, f("B")), "B n'est pas crédule")

print("--- Plusieurs justifications : D={A:B,C/D} ---")
E = generer_extensions(theorie(["A"], ["A : B, C / D"]))
verifier(sceptique(E, f("D")), "B et C cohérents : D est appliqué")
E = generer_extensions(theorie(["A", "~C"], ["A : B, C / D"]))
verifier(not credule(E, f("D")), "C contredit par W : D n'est pas appliqué")

print("--- Chaînage : W={A}, D={A:B/B, B:C/C} ---")
E = generer_extensions(theorie(["A"], ["A : B / B", "B : C / C"]))
verifier(len(E) == 1, "1 extension")
verifier(sceptique(E, f("C")), "C est obtenu par chaînage")
verifier(E[0].defauts_appliques == [1, 2], "d1 puis d2 appliqués")

print("--- Pas de doublon : deux défauts identiques ---")
E = generer_extensions(theorie([], [": A / B", ": A / B"]))
verifier(len(E) == 1, "1 seule extension")

print("--- Applicabilité (fonction applicable) ---")
T = theorie(["A"], ["A : B / C", "D : B / C", "A : ~A / C"])
verifier(applicable(T.D[0], T.W), "A : B / C applicable")
verifier(not applicable(T.D[1], T.W), "D : B / C : prérequis non démontré")
verifier(not applicable(T.D[2], T.W), "A : ¬A / C : justification incohérente")

print("--- Sauvegarde et chargement des extensions (étape 4) ---")
T = theorie(["A"], ["A : B / C", "A : ~C / ~B"])
E = generer_extensions(T)
donnees = extensions_vers_donnees(E)
verifier(len(donnees) == 2 and donnees[0]["defauts_appliques"] == [1],
         "conversion en données : 2 extensions, d1 pour E1")
json.dumps(donnees)   # doit être sérialisable en JSON
E2 = extensions_depuis_donnees(donnees)
verifier(len(E2) == 2 and all(
    equivalentes(a.base, b.base) and a.defauts_appliques == b.defauts_appliques
    for a, b in zip(E, E2)), "aller-retour : mêmes extensions")
verifier(credule(E2, f("C")) and not sceptique(E2, f("C")),
         "extensions rechargées : C crédule, non sceptique")

chemin = os.path.join(tempfile.mkdtemp(), "theorie.json")
T.enregistrer(chemin, donnees)
rechargee = Theorie.charger(chemin)
verifier(len(rechargee.W) == 1 and len(rechargee.D) == 2,
         "fichier : W et D retrouvés")
E3 = extensions_depuis_donnees(rechargee.extensions_sauvegardees)
verifier(len(E3) == 2 and E3[1].defauts_appliques == [2],
         "fichier : extensions retrouvées")

T.enregistrer(chemin)                      # sans extensions
verifier(Theorie.charger(chemin).extensions_sauvegardees is None,
         "fichier sans extensions : None")

E0 = generer_extensions(theorie([], [": A / ~A"]))
T0 = theorie([], [": A / ~A"])
T0.enregistrer(chemin, extensions_vers_donnees(E0))
verifier(Theorie.charger(chemin).extensions_sauvegardees == [],
         "aucune extension : liste vide enregistrée et retrouvée")

for mauvais, libelle in [
        ([{"base": "x", "defauts_appliques": []}], "base de mauvais type"),
        ([{"base": ["A"]}], "clé défauts_appliques absente"),
        ([{"base": ["A"], "defauts_appliques": ["x"]}], "numéro de défaut invalide"),
        (["texte"], "élément qui n'est pas un dictionnaire"),
        ([{"base": ["A &"], "defauts_appliques": []}], "formule incorrecte")]:
    try:
        extensions_depuis_donnees(mauvais)
        verifier(False, "données invalides : " + libelle)
    except ValueError:
        verifier(True, "données invalides refusées : " + libelle)

print("--- Explication des extensions (étape 6) ---")
T = theorie(["A"], ["A : B / C", "A : ~C / ~B"])
E = generer_extensions(T)
ex1 = expliquer_extension(T, E[0], "E1")
ex2 = expliquer_extension(T, E[1], "E2")
verifier(len(ex1) == 2 and [x.numero for x in ex1] == [1, 2],
         "une explication par défaut")
verifier(ex1[0].applique and not ex1[1].applique, "E1 : d1 appliqué, d2 non")
verifier(not ex2[0].applique and ex2[1].applique, "E2 : d1 non, d2 appliqué")
verifier("contredite" in ex1[1].raisons[0] and "¬C" in ex1[1].raisons[0]
         and "E1 démontre C" in ex1[1].raisons[0],
         "E1 : d2 bloqué car la justification ¬C est contredite par C")
verifier("contredite" in ex2[0].raisons[0] and "E2 démontre ¬B" in ex2[0].raisons[0],
         "E2 : d1 bloqué car la justification B est contredite par ¬B")
verifier(any("prérequis A démontré" in r for r in ex1[0].raisons),
         "défaut appliqué : prérequis démontré")
verifier(any("conséquent C est obtenu" in r for r in ex1[0].raisons),
         "défaut appliqué : conséquent obtenu dans l’extension")
verifier([x.applique for x in ex1] == [n in E[0].defauts_appliques for n in (1, 2)],
         "cohérent avec defauts_appliques")

T = theorie(["o", "p -> o", "p -> ~v"], ["o : v / v", "a : c / b"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(ex[0].applique and not ex[1].applique, "énoncé : d1 appliqué, d2 non")
verifier("prérequis a non démontré" in ex[1].raisons[0],
         "énoncé : d2 non appliqué car le prérequis a n'est pas démontré")

T = theorie(["Pingouin(tweety)", "Pingouin(tweety) -> Oiseau(tweety)",
             "Pingouin(tweety) -> ~Vole(tweety)"],
            ["Oiseau(tweety) : Vole(tweety) / Vole(tweety)"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(not ex[0].applique and "contredite" in ex[0].raisons[0],
         "pingouin : la justification Vole(tweety) est contredite")

T = theorie([], [": A & ~A / B"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(not ex[0].applique and "incohérente" in ex[0].raisons[0],
         "justification incohérente signalée")

T = theorie(["A"], ["B : C / D"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(not ex[0].applique and any("prérequis B non démontré" in r for r in ex[0].raisons),
         "prérequis non démontré signalé")

T = theorie(["~B"], ["A : B / C"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(len(ex[0].raisons) == 2, "prérequis ET justification : deux raisons")

T = theorie(["A"], [": B / A"])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(ex[0].applique and any("pas de prérequis" in r for r in ex[0].raisons),
         "défaut sans prérequis")
verifier(any("déjà conséquence de W" in r for r in ex[0].raisons),
         "conséquent déjà dans W signalé")

T = theorie(["A"], [])
ex = expliquer_extension(T, generer_extensions(T)[0], "E1")
verifier(ex == [], "aucun défaut : aucune explication")

print("--- Plus de 12 défauts : aucune limite artificielle ---")
# 20 défauts indépendants : on doit retrouver leurs 20 conséquents
# dans une seule extension, sans explorer toutes les permutations.
T = theorie([], [f": P{i} / Q{i}" for i in range(20)])
E = generer_extensions(T)
verifier(len(E) == 1, "20 défauts : une seule extension")
verifier(len(E[0].defauts_appliques) == 20,
         "20 défauts : tous les défauts ont été appliqués")
verifier(all(consequence(E[0].base, f(f"Q{i}")) for i in range(20)),
         "20 défauts : tous les conséquents sont déductibles")

# Contrôler que les défauts contradictoires restent séparés.
T = theorie(["A"], ["A : B / C", "A : ~C / ~B"])
E = generer_extensions(T)
verifier(len(E) == 2, "défauts contradictoires : deux extensions maintenues")

print()
print("Tous les tests réussis." if echecs == 0
      else f"{echecs} test(s) en échec.")
sys.exit(1 if echecs else 0)
