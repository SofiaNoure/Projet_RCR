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
from extensions import (
    applicable, generer_extensions, sceptique, credule,
    litteraux, extensions_contenant,
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

print("--- Limite du nombre de défauts ---")
T = theorie([], [f": P{i} / Q{i}" for i in range(13)])
try:
    generer_extensions(T)
    verifier(False, "13 défauts : ValueError attendue")
except ValueError:
    verifier(True, "13 défauts : ValueError levée")

print()
print("Tous les tests réussis." if echecs == 0
      else f"{echecs} test(s) en échec.")
sys.exit(1 if echecs else 0)
