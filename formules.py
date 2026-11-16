
import re
from sympy import Symbol, true, false
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent


# Expressions régulières pour reconnaître les mots
MOT = re.compile(r"[A-Za-z][A-Za-z0-9_]*$")
ARGUMENT = re.compile(r"[a-z][A-Za-z0-9_]*$")
TOKEN = re.compile(r"\s*(<->|->|[()~&|,]|[A-Za-z][A-Za-z0-9_]*)")


class Analyseur:
    def __init__(self, jetons):
        self.jetons = jetons
        self.position = 0

    def courant(self):
        if self.position < len(self.jetons):
            return self.jetons[self.position]
        return None

    def accepter(self, symbole):
        if self.courant() == symbole:
            self.position += 1
            return True
        return False

    def attendre(self, symbole):
        if not self.accepter(symbole):
            raise ValueError(
                f"Symbole '{symbole}' attendu ; trouvé : {self.courant()!r}"
            )

    # Équivalence : <->
    def equivalence(self):
        gauche = self.implication()

        while self.accepter("<->"):
            droite = self.implication()
            gauche = Equivalent(gauche, droite, evaluate=False)

        return gauche

    # Implication : ->
    def implication(self):
        gauche = self.ou()

        if self.accepter("->"):
            droite = self.implication()
            return Implies(gauche, droite, evaluate=False)

        return gauche

    # Disjonction : OU
    def ou(self):
        gauche = self.et()

        while self.accepter("|"):
            droite = self.et()
            gauche = Or(gauche, droite, evaluate=False)

        return gauche

    # Conjonction : ET
    def et(self):
        gauche = self.non()

        while self.accepter("&"):
            droite = self.non()
            gauche = And(gauche, droite, evaluate=False)

        return gauche

    # Négation : NON
    def non(self):
        if self.accepter("~"):
            return Not(self.non(), evaluate=False)

        return self.atome()

    # Proposition, prédicat ou parenthèses
    def atome(self):
        if self.accepter("("):
            formule = self.equivalence()
            self.attendre(")")
            return formule

        nom = self.courant()

        if nom is None or not MOT.fullmatch(nom):
            raise ValueError(
                f"Proposition ou prédicat attendu : {nom!r}"
            )

        self.position += 1

        # Cas des prédicats comme P(x) ou R(x,y)
        if self.accepter("("):
            arguments = []

            while True:
                arg = self.courant()

                if arg is None or not ARGUMENT.fullmatch(arg):
                    raise ValueError("Argument de prédicat incorrect.")

                arguments.append(arg)
                self.position += 1

                if not self.accepter(","):
                    break

            self.attendre(")")

            return Symbol(f"{nom}({','.join(arguments)})")

        # Constantes logiques
        if nom == "true":
            return true

        if nom == "false":
            return false

        return Symbol(nom)


# Fonction 1 : lire une formule
def lire_formule(texte):
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("La formule est vide.")

    texte = texte.strip()
    jetons = []
    position = 0

    # Découper le texte en jetons
    while position < len(texte):
        trouve = TOKEN.match(texte, position)

        if trouve is None:
            raise ValueError(
                f"Caractère inconnu près de : {texte[position:]!r}"
            )

        jetons.append(trouve.group(1))
        position = trouve.end()

    # Analyser les jetons
    analyseur = Analyseur(jetons)
    formule = analyseur.equivalence()

    if analyseur.courant() is not None:
        raise ValueError(
            f"Texte inattendu : {analyseur.courant()!r}"
        )

    return formule


# Fonction 2 : afficher une formule
def afficher_formule(formule):
    if formule is true:
        return "Vrai"

    if formule is false:
        return "Faux"

    if isinstance(formule, Symbol):
        return str(formule)

    if formule.func == Not:
        return "¬" + afficher_formule(formule.args[0])

    connecteurs = {
        And: " ∧ ",
        Or: " ∨ ",
        Implies: " → ",
        Equivalent: " ↔ "
    }

    if formule.func in connecteurs:
        symbole = connecteurs[formule.func]

        parties = [
            afficher_formule(arg)
            for arg in formule.args
        ]

        return "(" + symbole.join(parties) + ")"

    raise TypeError("Type de formule non reconnu.")


# Fonction 3 : extraire les variables
def variables(formules):
    resultat = set()

    for formule in formules:
        for symbole in formule.free_symbols:
            resultat.add(str(symbole))

    return sorted(resultat)


# Tests
if __name__ == "__main__":
    exemples = [
        "P",
        "~P",
        "P & Q",
        "P | Q",
        "P -> Q",
        "P <-> Q",
        "(P & Q) -> R",
        "~(P | Q)",
        "P(x) & Q(karim)",
        "true"
    ]

    formules = []

    for texte in exemples:
        formule = lire_formule(texte)
        formules.append(formule)

        print(texte, "=>", afficher_formule(formule))

    print("Variables :", variables(formules))
