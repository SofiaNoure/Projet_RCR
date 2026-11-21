
# re fournit les expressions régulières utilisées pour reconnaître le texte saisi.
import re
# SymPy fournit les symboles, les constantes et les connecteurs avec lesquels
# on construit les objets logiques transmis au moteur de raisonnement.
from sympy import Symbol, true, false
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent


# Expressions régulières pour reconnaître les mots
# MOT valide un identifiant entier qui commence par une lettre.
MOT = re.compile(r"[A-Za-z][A-Za-z0-9_]*$")
# ARGUMENT impose une minuscule initiale, comme dans x ou karim.
# Cette règle de saisie laisse ouverte la nature logique de l'argument.
ARGUMENT = re.compile(r"[a-z][A-Za-z0-9_]*$")
# TOKEN reconnaît un morceau de texte à la fois. Il saute les espaces avant
# le jeton et capture un connecteur, un signe de ponctuation ou un identifiant.
# P | Q & R donne les cinq jetons P, |, Q, & et R.
TOKEN = re.compile(r"\s*(<->|->|[()~&|,]|[A-Za-z][A-Za-z0-9_]*)")


# L'analyseur parcourt les jetons dans l'ordre et construit une formule SymPy.
class Analyseur:
    # La liste contient les jetons et la position désigne le prochain à lire.
    def __init__(self, jetons):
        self.jetons = jetons
        self.position = 0

    # Consulter le prochain jeton laisse le curseur en place. None indique la fin.
    def courant(self):
        if self.position < len(self.jetons):
            return self.jetons[self.position]
        return None

    # Si le jeton correspond au symbole attendu, on le consomme en avançant.
    # Sinon, le curseur reste en place pour que l'analyse puisse se poursuivre.
    def accepter(self, symbole):
        if self.courant() == symbole:
            self.position += 1
            return True
        return False

    # Ici, le jeton est obligatoire, par exemple pour fermer une parenthèse.
    # Une absence ou un autre jeton déclenche une erreur de syntaxe.
    def attendre(self, symbole):
        if not self.accepter(symbole):
            raise ValueError(
                f"Symbole '{symbole}' attendu ; trouvé : {self.courant()!r}"
            )

    # Chaque méthode commence par lire une expression du niveau plus prioritaire.
    # De la priorité la plus faible à la plus forte, on lit <->, ->, |, &, puis ~.
    # Les atomes servent de base et les parenthèses permettent de recommencer
    # l'analyse complète à l'intérieur d'un groupe.
    # evaluate=False demande à SymPy de limiter l'évaluation à la construction.
    # Équivalence : <->
    def equivalence(self):
        gauche = self.implication()

        # while absorbe toute la chaîne de <-> en combinant les deux côtés.
        while self.accepter("<->"):
            droite = self.implication()
            gauche = Equivalent(gauche, droite, evaluate=False)

        return gauche

    # Implication : ->
    def implication(self):
        gauche = self.ou()

        # if teste la présence d'une flèche à ce niveau. L'appel récursif
        # analyse toute la partie droite, donc P -> Q -> R se lit P -> (Q -> R).
        if self.accepter("->"):
            droite = self.implication()
            return Implies(gauche, droite, evaluate=False)

        return gauche

    # Disjonction : OU
    def ou(self):
        # On lit d'abord les conjonctions. Dans P | Q & R, le côté droit
        # du OU est donc Q & R.
        gauche = self.et()

        # Chaque tour de boucle ajoute à Or le terme qui suit le |.
        while self.accepter("|"):
            droite = self.et()
            gauche = Or(gauche, droite, evaluate=False)

        return gauche

    # Conjonction : ET
    def et(self):
        # La négation est prioritaire. On la traite avant de construire le ET.
        gauche = self.non()

        # Tant qu'il reste un &, la boucle lit le terme suivant et construit And.
        while self.accepter("&"):
            droite = self.non()
            gauche = And(gauche, droite, evaluate=False)

        return gauche

    # Négation : NON
    def non(self):
        # L'appel récursif lit ce que ~ doit nier. Cela permet de lire ~~P.
        if self.accepter("~"):
            return Not(self.non(), evaluate=False)

        # Quand il n'y a plus de ~, la récursion se termine en lisant un atome.
        return self.atome()

    # Proposition, prédicat ou parenthèses
    def atome(self):
        # Après une parenthèse ouvrante, on repart de l'équivalence pour
        # autoriser tous les connecteurs dans le groupe.
        if self.accepter("("):
            formule = self.equivalence()
            self.attendre(")")
            return formule

        # À cette position, un identifiant est attendu. On le valide avant d'avancer.
        nom = self.courant()

        if nom is None or not MOT.fullmatch(nom):
            raise ValueError(
                f"Proposition ou prédicat attendu : {nom!r}"
            )

        self.position += 1

        # Cas des prédicats comme P(x) ou R(x,y)
        # Après un nom, une parenthèse ouvrante introduit une liste d'arguments.
        if self.accepter("("):
            arguments = []

            # Il faut au moins un argument. Chaque virgule annonce un autre
            # argument et la parenthèse fermante termine la liste.
            while True:
                arg = self.courant()

                if arg is None or not ARGUMENT.fullmatch(arg):
                    raise ValueError("Argument de prédicat incorrect.")

                arguments.append(arg)
                self.position += 1

                if not self.accepter(","):
                    break

            self.attendre(")")

            # Le nom et la liste sont réunis dans un seul Symbol, comme R(x,y).
            # Le moteur peut ainsi traiter l'expression entière comme un atome.
            return Symbol(f"{nom}({','.join(arguments)})")

        # Constantes logiques
        # Les noms réservés true et false seuls désignent les constantes SymPy.
        if nom == "true":
            return true

        if nom == "false":
            return false

        # Un autre nom seul représente une proposition, par exemple P.
        return Symbol(nom)


# Fonction 1 : lire une formule
def lire_formule(texte):
    # strip permet de repérer une saisie composée uniquement d'espaces.
    # Le test du type vient en premier pour garantir que strip s'applique à du texte.
    if not isinstance(texte, str) or not texte.strip():
        raise ValueError("La formule est vide.")

    # Retirer les espaces aux extrémités évite de chercher un jeton après
    # le dernier caractère utile. La liste et le curseur servent au découpage.
    texte = texte.strip()
    jetons = []
    position = 0

    # Découper le texte en jetons
    while position < len(texte):
        # match cherche le prochain jeton exactement à la position donnée.
        trouve = TOKEN.match(texte, position)

        # Si rien ne correspond, on signale l'endroit où la lecture s'arrête.
        if trouve is None:
            raise ValueError(
                f"Caractère inconnu près de : {texte[position:]!r}"
            )

        # Le groupe 1 contient le jeton seul. end donne la position où reprendre.
        jetons.append(trouve.group(1))
        position = trouve.end()

    # Analyser les jetons
    # L'analyseur prend la liste de chaînes et construit un objet SymPy
    # en partant du niveau le moins prioritaire.
    analyseur = Analyseur(jetons)
    formule = analyseur.equivalence()

    # Un jeton restant signale que seule une partie de la saisie était valide,
    # comme dans P Q, où Q suit la proposition déjà lue.
    if analyseur.courant() is not None:
        raise ValueError(
            f"Texte inattendu : {analyseur.courant()!r}"
        )

    return formule


# Fonction 2 : afficher une formule
# Cette fonction parcourt l'objet SymPy produit par la lecture.
def afficher_formule(formule, mode="affichage"):
    # Deux formats possibles :
    # affichage : symboles mathématiques pour l'utilisateur
    # sauvegarde : symboles compatibles avec lire_formule()
    if mode not in ("affichage", "sauvegarde"):
        raise ValueError("Mode d'affichage inconnu.")

    if formule is true:
        return "true" if mode == "sauvegarde" else "Vrai"

    if formule is false:
        return "false" if mode == "sauvegarde" else "Faux"

    if isinstance(formule, Symbol):
        return str(formule)

    # Traiter la négation en conservant le mode choisi.
    if formule.func == Not:
        contenu = afficher_formule(formule.args[0], mode)

        if mode == "sauvegarde":
            return "~(" + contenu + ")"

        return "¬" + contenu

    # Sélectionner les connecteurs selon le mode.
    if mode == "sauvegarde":
        connecteurs = {
            And: " & ",
            Or: " | ",
            Implies: " -> ",
            Equivalent: " <-> "
        }
    else:
        connecteurs = {
            And: " ∧ ",
            Or: " ∨ ",
            Implies: " → ",
            Equivalent: " ↔ "
        }

    if formule.func in connecteurs:
        symbole = connecteurs[formule.func]

        # Conversion récursive des arguments.
        parties = [
            afficher_formule(arg, mode)
            for arg in formule.args
        ]

        return "(" + symbole.join(parties) + ")"

    raise TypeError("Type de formule non reconnu.")



def variables(formules):
    """Renvoie les noms complets des symboles propositionnels, triés et uniques."""
    # Un ensemble ne garde qu'une fois un même nom présent dans plusieurs formules.
    resultat = set()

    for formule in formules:
        # free_symbols récupère les Symbol présents, même sous un connecteur.
        # P(x) est un symbole propositionnel entier et x fait partie de son nom.
        for symbole in formule.free_symbols:
            resultat.add(str(symbole))

    # sorted rend la liste de noms prévisible quel que soit l'ordre de collecte.
    return sorted(resultat)


def variables_detaillees(formules):
    """Décrit les symboles présents dans les formules SymPy.

    Les listes « propositions » et « arguments » sont triées et sans doublons.
    « predicats » associe chaque nom à la liste triée de ses tuples d'arguments.
    Chaque tuple conserve l'ordre et les répétitions de l'occurrence analysée.
    Les arguments sont des identifiants dont la nature reste indéterminée.
    """
    # Cette fonction décrit les noms symboliques pour l'inspection.
    # Le moteur continue de raisonner sur les Symbol entiers.
    propositions = []
    predicats = {}
    arguments = set()

    for symbole in variables(formules):
        # La première parenthèse sépare le nom du reste du symbole.
        nom, _, suite = symbole.partition("(")
        if suite.endswith(")") and MOT.fullmatch(nom):
            # Les virgules séparent les arguments, dont on garde l'ordre.
            args = tuple(suite[:-1].split(","))
            if all(ARGUMENT.fullmatch(arg) for arg in args):
                predicats.setdefault(nom, []).append(args)
                arguments.update(args)
                continue

        # Le nom est rangé parmi les propositions si la forme d'un prédicat
        # complet n'a pas été reconnue.
        propositions.append(symbole)

    for occurrences in predicats.values():
        occurrences.sort()

    return {
        "propositions": propositions,
        "predicats": predicats,
        "arguments": sorted(arguments),
    }


if __name__ == "__main__":
    # Ces saisies illustrent les formes que l'analyseur sait lire.
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
        # On conserve l'objet SymPy pour extraire ensuite l'ensemble des noms.
        formule = lire_formule(texte)
        formules.append(formule)

        # La saisie et son affichage apparaissent côte à côte pour les comparer.
        print(texte, "=>", afficher_formule(formule))

    print("Variables :", variables(formules))
