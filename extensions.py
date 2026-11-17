
from dataclasses import dataclass

from sympy import Symbol

from raisonnement import est_coherent, consequence
from defauts import Theorie
from formules import lire_formule, afficher_formule, variables


@dataclass
class Extension:
    base: list
    defauts_appliques: list


# Vérifier l'applicabilité d'un défaut
def applicable(defaut, base):
    prerequis_ok = consequence(base, defaut.prerequis)

    justifications_ok = all(
        est_coherent(base + [j])
        for j in defaut.justifications
    )

    return prerequis_ok and justifications_ok


# Comparer deux bases par leurs conséquences logiques
def equivalentes(base1, base2):
    return (
        all(consequence(base1, f) for f in base2)
        and all(consequence(base2, f) for f in base1)
    )


# Calculer Gamma(E) selon la définition de Reiter
def fermeture_relative(theorie, candidat):
    base = list(theorie.W)
    appliques = []
    changement = True

    while changement:
        changement = False

        for numero, defaut in enumerate(theorie.D, start=1):

            prerequis_ok = consequence(
                base, defaut.prerequis
            )

            # Les justifications sont vérifiées
            # par rapport au candidat final E
            justifications_ok = all(
                est_coherent(candidat + [j])
                for j in defaut.justifications
            )

            if prerequis_ok and justifications_ok:

                if numero not in appliques:
                    appliques.append(numero)

                if not consequence(base, defaut.consequent):
                    base.append(defaut.consequent)
                    changement = True

    return base, appliques


# Générer les extensions en explorant
# tous les ordres possibles des défauts
def generer_extensions(theorie, maximum_defauts=12):

    if len(theorie.D) > maximum_defauts:
        raise ValueError(
            "Trop de défauts pour cette version."
        )

    extensions = []

    def explorer(base, appliques):

        # Étape 2 : chercher les défauts applicables
        choix = []

        for numero, defaut in enumerate(theorie.D, start=1):
            if (
                numero not in appliques
                and applicable(defaut, base)
            ):
                choix.append(numero)

        # Étapes 3 et 5 : explorer tous les choix
        if choix:
            for numero in choix:
                defaut = theorie.D[numero - 1]
                nouvelle_base = list(base)

                if not consequence(
                    nouvelle_base, defaut.consequent
                ):
                    nouvelle_base.append(defaut.consequent)

                explorer(
                    nouvelle_base,
                    appliques + [numero]
                )

            return

        # Étape 4 : vérification finale
        for numero in appliques:
            defaut = theorie.D[numero - 1]

            if not all(
                est_coherent(base + [j])
                for j in defaut.justifications
            ):
                return

        # Vérification formelle : Gamma(E) = E
        fermeture, _ = fermeture_relative(theorie, base)

        if not equivalentes(fermeture, base):
            return

        # Éviter les extensions équivalentes
        if not any(
            equivalentes(base, e.base)
            for e in extensions
        ):
            extensions.append(
                Extension(
                    base=list(base),
                    defauts_appliques=list(appliques)
                )
            )

    # Étape 1 : E = Th(W)
    # La fermeture classique est calculée implicitement
    explorer(list(theorie.W), [])

    return extensions


# Conséquence sceptique
def sceptique(extensions, formule):
    if not extensions:
        return None

    return all(
        consequence(e.base, formule)
        for e in extensions
    )


# Conséquence crédule
def credule(extensions, formule):
    if not extensions:
        return None

    return any(
        consequence(e.base, formule)
        for e in extensions
    )


# Littéraux (P ou ¬P) qui sont des conséquences d'une extension
def litteraux(extension):
    base = extension.base

    if not est_coherent(base):
        return []

    resultat = []

    for nom in variables(base):
        symbole = Symbol(nom)

        if consequence(base, symbole):
            resultat.append(afficher_formule(symbole))
        elif consequence(base, ~symbole):
            resultat.append(afficher_formule(~symbole))

    return resultat


# Numéros (à partir de 1) des extensions dont la formule est conséquence
def extensions_contenant(extensions, formule):
    return [
        i for i, e in enumerate(extensions, start=1)
        if consequence(e.base, formule)
    ]


# Afficher les résultats
def afficher_extensions(theorie):
    resultat = generer_extensions(theorie)

    print("Nombre d'extensions :", len(resultat))

    for i, extension in enumerate(resultat, start=1):
        print(
            f"E{i} :",
            [afficher_formule(f) for f in extension.base]
        )

        print(
            "Défauts appliqués :",
            extension.defauts_appliques
        )

    return resultat


# Tests tirés du cours
if __name__ == "__main__":

    # Exemple de la page 18
    print("=== EXEMPLE SLIDE 18 ===")

    theorie1 = Theorie()
    theorie1.ajouter_formule("A")
    theorie1.ajouter_defaut("A : B / C")
    theorie1.ajouter_defaut("A : ~C / ~B")

    resultat1 = afficher_extensions(theorie1)

    print(
        "C sceptique :",
        sceptique(resultat1, lire_formule("C"))
    )
    print(
        "C crédule :",
        credule(resultat1, lire_formule("C"))
    )

    # Exemple de la page 21
    print("\n=== EXEMPLE SLIDE 21 ===")

    theorie2 = Theorie()
    theorie2.ajouter_defaut(": A / B")
    theorie2.ajouter_defaut(": C / ~A")

    resultat2 = afficher_extensions(theorie2)

    print(
        "B sceptique :",
        sceptique(resultat2, lire_formule("B"))
    )
