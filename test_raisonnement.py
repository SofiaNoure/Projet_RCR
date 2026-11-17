"""Jeu de tests du module raisonnement.py.

Lancement :  python test_raisonnement.py
Chaque ligne affiche PASS ou FAIL ; le programme se termine par un
code d'erreur s'il y a au moins un échec.
"""

import sys

from formules import lire_formule
from raisonnement import est_coherent, consequence, sous_ensemble_incoherent

echecs = 0


def verifier(condition, libelle):
    """Affiche PASS ou FAIL pour un test."""
    global echecs
    print(("PASS  " if condition else "FAIL  ") + libelle)
    if not condition:
        echecs += 1


def mondes(*textes):
    """Construit une liste de formules à partir de textes."""
    return [lire_formule(t) for t in textes]


# ----------------------------------------------------------------------
# est_coherent
# ----------------------------------------------------------------------
print("--- est_coherent ---")
verifier(est_coherent([]), "monde vide : cohérent")
verifier(est_coherent(mondes("P")), "{P} : cohérent")
verifier(not est_coherent(mondes("P", "~P")), "{P, ¬P} : incohérent")
verifier(not est_coherent(mondes("P", "P -> Q", "~Q")),
         "{P, P→Q, ¬Q} : incohérent")
verifier(est_coherent(mondes("P | Q", "~P")), "{P∨Q, ¬P} : cohérent")
verifier(est_coherent(mondes("P <-> Q", "P")), "{P↔Q, P} : cohérent")
verifier(est_coherent(mondes("true")), "{Vrai} : cohérent")
verifier(not est_coherent(mondes("false")), "{Faux} : incohérent")
verifier(not est_coherent(mondes("x & ~x")), "{x ∧ ¬x} : incohérent")
verifier(not est_coherent(mondes("Oiseau(tweety)", "~Oiseau(tweety)")),
         "prédicats : {Oiseau(tweety), ¬Oiseau(tweety)} incohérent")

# ----------------------------------------------------------------------
# consequence
# ----------------------------------------------------------------------
print("--- consequence ---")
W = mondes("P", "P -> Q")
verifier(consequence(W, lire_formule("Q")), "{P, P→Q} ⊨ Q (modus ponens)")
verifier(not consequence(W, lire_formule("R")), "{P, P→Q} ⊭ R")
verifier(consequence([], lire_formule("P | ~P")), "∅ ⊨ P∨¬P (tautologie)")
verifier(not consequence([], lire_formule("P")), "∅ ⊭ P")
verifier(consequence(mondes("P & Q"), lire_formule("P")), "{P∧Q} ⊨ P")
verifier(consequence(mondes("P | Q", "~P"), lire_formule("Q")),
         "{P∨Q, ¬P} ⊨ Q (syllogisme disjonctif)")
verifier(consequence(mondes("P -> Q", "~Q"), lire_formule("~P")),
         "{P→Q, ¬Q} ⊨ ¬P (modus tollens)")
verifier(consequence(mondes("P <-> Q", "P"), lire_formule("Q")),
         "{P↔Q, P} ⊨ Q")
verifier(consequence(mondes("P", "~P"), lire_formule("R")),
         "monde incohérent : tout est conséquence")
verifier(consequence(mondes("Oiseau(tweety)"), lire_formule("Oiseau(tweety)")),
         "prédicat : {Oiseau(tweety)} ⊨ Oiseau(tweety)")
verifier(not consequence(mondes("Oiseau(tweety)"), lire_formule("Oiseau(x)")),
         "prédicats différents : pas de conséquence")

# ----------------------------------------------------------------------
# sous_ensemble_incoherent
# ----------------------------------------------------------------------
print("--- sous_ensemble_incoherent ---")
verifier(sous_ensemble_incoherent(mondes("P", "P -> Q")) == [],
         "monde cohérent : liste vide")

W2 = mondes("P", "P -> Q", "~Q", "R")
sous = sous_ensemble_incoherent(W2)
verifier(not est_coherent(sous), "W2 : le sous-ensemble est incohérent")
verifier(all(est_coherent(sous[:i] + sous[i + 1:]) for i in range(len(sous))),
         "W2 : le sous-ensemble est minimal")
verifier(all(f is not W2[3] for f in sous),
         "W2 : la formule R (hors conflit) n'y figure pas")
verifier(len(sous) == 3, "W2 : 3 formules incohérentes")

sous = sous_ensemble_incoherent(mondes("P", "~P"))
verifier(len(sous) == 2, "{P, ¬P} : les deux formules sont renvoyées")

sous = sous_ensemble_incoherent(mondes("A", "x & ~x", "B"))
verifier(len(sous) == 1, "formule seule incohérente : une seule formule")

print()
print("Tous les tests réussis." if echecs == 0
      else f"{echecs} test(s) en échec.")
sys.exit(1 if echecs else 0)
