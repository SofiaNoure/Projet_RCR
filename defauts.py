
import json
from dataclasses import dataclass, field
from sympy import Symbol, true, false
from sympy.logic.boolalg import Not, And, Or, Implies, Equivalent

from formules import lire_formule, afficher_formule
from raisonnement import est_coherent


# Séparer les justifications, sans couper les arguments de P(x,y)
def separer_justifications(texte):
    morceaux = []
    debut = 0
    profondeur = 0

    for i, caractere in enumerate(texte):
        if caractere == "(":
            profondeur += 1
        elif caractere == ")":
            profondeur -= 1
            if profondeur < 0:
                raise ValueError("Parenthèse fermante inattendue.")

        elif caractere == "," and profondeur == 0:
            morceaux.append(texte[debut:i].strip())
            debut = i + 1

    if profondeur != 0:
        raise ValueError("Parenthèse non fermée.")

    morceaux.append(texte[debut:].strip())
    return morceaux


# Convertir une formule SymPy en texte réutilisable
def formule_en_texte(f):
    if f is true:
        return "true"

    if f is false:
        return "false"

    if isinstance(f, Symbol):
        return str(f)

    if f.func == Not:
        return "~(" + formule_en_texte(f.args[0]) + ")"

    connecteurs = {
        And: " & ",
        Or: " | ",
        Implies: " -> ",
        Equivalent: " <-> "
    }

    if f.func in connecteurs:
        return "(" + connecteurs[f.func].join(
            formule_en_texte(x) for x in f.args
        ) + ")"

    raise ValueError("Formule non prise en charge.")


# Représentation d'un défaut
@dataclass
class Defaut:
    prerequis: object
    justifications: list
    consequent: object

    def __str__(self):
        pre = (
            "" if self.prerequis is true
            else formule_en_texte(self.prerequis)
        )

        just = ", ".join(
            formule_en_texte(j) for j in self.justifications
        )

        return f"{pre} : {just} / {formule_en_texte(self.consequent)}"


# Lire un défaut saisi par l'utilisateur
def lire_defaut(texte):
    if texte.count(":") != 1 or texte.count("/") != 1:
        raise ValueError(
            "Un défaut doit contenir exactement ':' et '/'."
        )

    pre, reste = texte.split(":", 1)
    just, cons = reste.split("/", 1)

    if not just.strip() or not cons.strip():
        raise ValueError(
            "Justification et conséquent obligatoires."
        )

    justifs = separer_justifications(just)

    if any(not x for x in justifs):
        raise ValueError("Une justification est vide.")

    return Defaut(
        lire_formule(pre) if pre.strip() else true,
        [lire_formule(x) for x in justifs],
        lire_formule(cons)
    )


# Signaler les justifications incohérentes
def avertissements_defaut(defaut):
    return [
        f"Justification incohérente : {afficher_formule(j)}"
        for j in defaut.justifications
        if not est_coherent([j])
    ]


# Représentation d'une théorie T = (W, D)
@dataclass
class Theorie:
    W: list = field(default_factory=list)
    D: list = field(default_factory=list)

    def ajouter_formule(self, texte):
        formule = lire_formule(texte)
        self.W.append(formule)
        return formule

    def ajouter_defaut(self, texte):
        defaut = lire_defaut(texte)
        self.D.append(defaut)
        return defaut

    # Sauvegarder la théorie dans un fichier JSON
    def enregistrer(self, chemin):
        donnees = {
            "W": [formule_en_texte(f) for f in self.W],
            "D": [str(d) for d in self.D]
        }

        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump(
                donnees, fichier,
                indent=2, ensure_ascii=False
            )

    # Recharger une théorie depuis un fichier JSON
    @classmethod
    def charger(cls, chemin):
        with open(chemin, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)

        if (
            not isinstance(donnees, dict)
            or not isinstance(donnees.get("W"), list)
            or not isinstance(donnees.get("D"), list)
        ):
            raise ValueError("Fichier de théorie invalide.")

        theorie = cls()

        for texte in donnees["W"]:
            theorie.ajouter_formule(texte)

        for texte in donnees["D"]:
            theorie.ajouter_defaut(texte)

        return theorie


# Tests
if __name__ == "__main__":
    theorie = Theorie()

    theorie.ajouter_formule("P")
    theorie.ajouter_formule("P -> Q")

    d1 = theorie.ajouter_defaut("Q : R / R")
    d2 = theorie.ajouter_defaut(": P(x,y), ~Q / R")

    print("Monde W :", [
        formule_en_texte(f) for f in theorie.W
    ])

    print("Défaut 1 :", d1)
    print("Défaut 2 :", d2)

    print("Avertissements :", avertissements_defaut(d1))

    theorie.enregistrer("theorie_test.json")

    copie = Theorie.charger("theorie_test.json")

    print(
        "Rechargement réussi :",
        len(copie.W), "formules et",
        len(copie.D), "défauts"
    )
