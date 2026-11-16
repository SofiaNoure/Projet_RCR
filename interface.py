"""Interface graphique (Tkinter) de la logique des défauts.

Règle de conception : ce module ne fait AUCUN calcul logique.
Il lit ce que l'utilisateur saisit, appelle les fonctions des autres
modules (formules, raisonnement, defauts, extensions) et affiche
leurs résultats.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from sympy import Symbol

from formules import lire_formule, afficher_formule, variables
from raisonnement import est_coherent, consequence, sous_ensemble_incoherent
from defauts import Theorie, avertissements_defaut
from extensions import generer_extensions, sceptique, credule


# ----------------------------------------------------------------------
# Exemples prédéfinis : nom -> (formules de W, défauts de D)
# ----------------------------------------------------------------------
EXEMPLES = {
    "Exemple de l'énoncé": (
        ["o", "p -> o", "p -> ~v"],
        ["o : v / v", "a : c / b"],
    ),
    "Cours - slide 18": (
        ["A"],
        ["A : B / C", "A : ~C / ~B"],
    ),
    "Cours - slide 21": (
        [],
        [": A / B", ": C / ~A"],
    ),
    "Oiseau qui vole (Tweety)": (
        ["Oiseau(tweety)"],
        ["Oiseau(tweety) : Vole(tweety) / Vole(tweety)"],
    ),
    "Pingouin (exception)": (
        ["Pingouin(tweety)",
         "Pingouin(tweety) -> Oiseau(tweety)",
         "Pingouin(tweety) -> ~Vole(tweety)"],
        ["Oiseau(tweety) : Vole(tweety) / Vole(tweety)"],
    ),
    "Diamant de Nixon": (
        ["Quaker(nixon)", "Republicain(nixon)"],
        ["Quaker(nixon) : Pacifiste(nixon) / Pacifiste(nixon)",
         "Republicain(nixon) : ~Pacifiste(nixon) / ~Pacifiste(nixon)"],
    ),
    "Aucune extension": (
        [],
        [": A / ~A"],
    ),
}


def texte_defaut(defaut):
    """Écrit un défaut sous la forme « prérequis : justifs / conséquent »."""
    prerequis = "" if afficher_formule(defaut.prerequis) == "Vrai" \
        else afficher_formule(defaut.prerequis)
    justifs = ", ".join(afficher_formule(j) for j in defaut.justifications)
    return f"{prerequis} : {justifs} / {afficher_formule(defaut.consequent)}"


class Application(tk.Tk):
    """Fenêtre principale : saisie de la théorie (W, D) et résultats."""

    def __init__(self):
        super().__init__()
        self.title("Logique des défauts - Extensions de Reiter")
        self.geometry("1000x720")
        self.minsize(900, 600)

        # Seul état de l'application : la théorie en cours d'édition
        self.theorie = Theorie()

        self._creer_style()
        self._creer_barre_haut()
        self._creer_zone_saisie()
        self._creer_barre_actions()
        self._creer_zone_resultats()
        self.rafraichir()

    # ------------------------------------------------------------------
    # Construction de la fenêtre
    # ------------------------------------------------------------------
    def _creer_style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Titre.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"),
                        padding=6)
        self.configure(padx=8, pady=8)

    def _creer_barre_haut(self):
        """Boutons Nouveau / Ouvrir / Enregistrer / Exemples."""
        barre = ttk.Frame(self)
        barre.pack(fill="x", pady=(0, 8))

        ttk.Button(barre, text="Nouveau",
                   command=self.nouveau).pack(side="left", padx=2)
        ttk.Button(barre, text="Ouvrir",
                   command=self.ouvrir).pack(side="left", padx=2)
        ttk.Button(barre, text="Enregistrer",
                   command=self.enregistrer).pack(side="left", padx=2)

        menu_exemples = tk.Menu(self, tearoff=0)
        for nom in EXEMPLES:
            menu_exemples.add_command(
                label=nom, command=lambda n=nom: self.charger_exemple(n))
        bouton = ttk.Menubutton(barre, text="Exemples ▾", menu=menu_exemples)
        bouton.pack(side="left", padx=2)

    def _creer_zone_saisie(self):
        """Deux colonnes : monde W (gauche) et défauts D (droite)."""
        zone = ttk.Frame(self)
        zone.pack(fill="both", expand=True)
        zone.columnconfigure(0, weight=1, uniform="col")
        zone.columnconfigure(1, weight=1, uniform="col")
        zone.rowconfigure(0, weight=1)

        # ---------------- Colonne W ----------------
        cadre_w = ttk.LabelFrame(zone, text=" MONDE W ", padding=8)
        cadre_w.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        cadre_w.columnconfigure(1, weight=1)
        cadre_w.rowconfigure(2, weight=1)

        ttk.Label(cadre_w, text="Formule :").grid(row=0, column=0, sticky="w")
        self.entree_formule = ttk.Entry(cadre_w)
        self.entree_formule.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.entree_formule.bind("<Return>", lambda e: self.ajouter_formule())

        boutons_w = ttk.Frame(cadre_w)
        boutons_w.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Button(boutons_w, text="Ajouter formule",
                   command=self.ajouter_formule).pack(side="left", padx=2)
        ttk.Button(boutons_w, text="Supprimer",
                   command=self.supprimer_formule).pack(side="left", padx=2)

        self.liste_w = self._creer_liste(cadre_w, row=2)

        ttk.Button(cadre_w, text="Vérifier la cohérence de W",
                   command=self.verifier_coherence).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # ---------------- Colonne D ----------------
        cadre_d = ttk.LabelFrame(zone, text=" DÉFAUTS D ", padding=8)
        cadre_d.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        cadre_d.columnconfigure(1, weight=1)
        cadre_d.rowconfigure(5, weight=1)

        champs = [("Prérequis :", "entree_pre"),
                  ("Justifications :", "entree_just"),
                  ("Conséquent :", "entree_cons")]
        for ligne, (libelle, attribut) in enumerate(champs):
            ttk.Label(cadre_d, text=libelle).grid(
                row=ligne, column=0, sticky="w")
            entree = ttk.Entry(cadre_d)
            entree.grid(row=ligne, column=1, sticky="ew", padx=4, pady=2)
            entree.bind("<Return>", lambda e: self.ajouter_defaut())
            setattr(self, attribut, entree)

        ttk.Label(cadre_d, text="(justifications séparées par des virgules, "
                                "prérequis vide autorisé)",
                  foreground="gray40").grid(
            row=3, column=0, columnspan=2, sticky="w")

        boutons_d = ttk.Frame(cadre_d)
        boutons_d.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Button(boutons_d, text="Ajouter défaut",
                   command=self.ajouter_defaut).pack(side="left", padx=2)
        ttk.Button(boutons_d, text="Supprimer",
                   command=self.supprimer_defaut).pack(side="left", padx=2)

        self.liste_d = self._creer_liste(cadre_d, row=5)

    def _creer_liste(self, parent, row):
        """Crée une Listbox avec barre de défilement dans `parent`."""
        cadre = ttk.Frame(parent)
        cadre.grid(row=row, column=0, columnspan=2, sticky="nsew")
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)

        liste = tk.Listbox(cadre, font=("Consolas", 11), activestyle="none",
                           exportselection=False, height=8)
        barre = ttk.Scrollbar(cadre, orient="vertical", command=liste.yview)
        liste.configure(yscrollcommand=barre.set)
        liste.grid(row=0, column=0, sticky="nsew")
        barre.grid(row=0, column=1, sticky="ns")
        return liste

    def _creer_barre_actions(self):
        """Boutons de calcul + champ φ pour les conséquences."""
        barre = ttk.Frame(self)
        barre.pack(fill="x", pady=8)

        ttk.Button(barre, text="Générer les extensions", style="Action.TButton",
                   command=self.generer).pack(side="left", padx=2)

        ttk.Label(barre, text="   φ :").pack(side="left")
        self.entree_phi = ttk.Entry(barre, width=30)
        self.entree_phi.pack(side="left", padx=4)

        ttk.Button(barre, text="Sceptique ?", style="Action.TButton",
                   command=self.tester_sceptique).pack(side="left", padx=2)
        ttk.Button(barre, text="Crédule ?", style="Action.TButton",
                   command=self.tester_credule).pack(side="left", padx=2)

    def _creer_zone_resultats(self):
        cadre = ttk.LabelFrame(self, text=" RÉSULTATS ", padding=6)
        cadre.pack(fill="both", expand=True)
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)

        self.resultats = tk.Text(cadre, height=12, wrap="word",
                                 font=("Consolas", 11), state="disabled")
        barre = ttk.Scrollbar(cadre, orient="vertical",
                              command=self.resultats.yview)
        self.resultats.configure(yscrollcommand=barre.set)
        self.resultats.grid(row=0, column=0, sticky="nsew")
        barre.grid(row=0, column=1, sticky="ns")

        # Styles de texte pour les résultats
        self.resultats.tag_configure("titre", font=("Consolas", 11, "bold"))
        self.resultats.tag_configure("ok", foreground="#1b7f3b",
                                     font=("Consolas", 11, "bold"))
        self.resultats.tag_configure("ko", foreground="#c0392b",
                                     font=("Consolas", 11, "bold"))
        self.resultats.tag_configure("gris", foreground="#666666")

    # ------------------------------------------------------------------
    # Utilitaires d'affichage
    # ------------------------------------------------------------------
    def rafraichir(self):
        """Reconstruit les deux listes à partir de self.theorie."""
        self.liste_w.delete(0, "end")
        for i, f in enumerate(self.theorie.W, start=1):
            self.liste_w.insert("end", f"{i}. {afficher_formule(f)}")

        self.liste_d.delete(0, "end")
        for i, d in enumerate(self.theorie.D, start=1):
            self.liste_d.insert("end", f"d{i} : {texte_defaut(d)}")

    def effacer_resultats(self):
        self.resultats.configure(state="normal")
        self.resultats.delete("1.0", "end")
        self.resultats.configure(state="disabled")

    def ecrire(self, texte, tag=None):
        """Ajoute du texte à la zone des résultats."""
        self.resultats.configure(state="normal")
        if tag:
            self.resultats.insert("end", texte, tag)
        else:
            self.resultats.insert("end", texte)
        self.resultats.configure(state="disabled")
        self.resultats.see("end")

    def erreur(self, titre, message):
        messagebox.showerror(titre, message)

    def _indice_selection(self, liste, nom):
        """Renvoie l'indice sélectionné dans la liste, ou None (+ message)."""
        selection = liste.curselection()
        if not selection:
            messagebox.showinfo("Aucune sélection",
                                f"Sélectionnez d'abord {nom} dans la liste.")
            return None
        return selection[0]

    # ------------------------------------------------------------------
    # Monde W
    # ------------------------------------------------------------------
    def ajouter_formule(self):
        texte = self.entree_formule.get()
        try:
            self.theorie.ajouter_formule(texte)
        except ValueError as e:
            self.erreur("Formule incorrecte", str(e))
            return
        self.entree_formule.delete(0, "end")
        self.rafraichir()

    def supprimer_formule(self):
        i = self._indice_selection(self.liste_w, "une formule")
        if i is not None:
            del self.theorie.W[i]
            self.rafraichir()

    def verifier_coherence(self):
        self.rafraichir()  # enlève les anciens surlignages
        self.effacer_resultats()

        if est_coherent(self.theorie.W):
            self.ecrire("W est cohérent\n", "ok")
            return

        incoherentes = sous_ensemble_incoherent(self.theorie.W)
        self.ecrire("W est incohérent. ", "ko")
        self.ecrire("Sous-ensemble incohérent :\n")

        deja_pris = set()
        for formule in incoherentes:
            self.ecrire(f"   • {afficher_formule(formule)}\n")
            # On retrouve la ligne de W correspondant à cette formule
            for i, f in enumerate(self.theorie.W):
                if f is formule and i not in deja_pris:
                    deja_pris.add(i)
                    self.liste_w.itemconfig(i, bg="#f5b7b1")
                    break

    # ------------------------------------------------------------------
    # Défauts D
    # ------------------------------------------------------------------
    def ajouter_defaut(self):
        pre = self.entree_pre.get().strip()
        just = self.entree_just.get().strip()
        cons = self.entree_cons.get().strip()
        texte = f"{pre} : {just} / {cons}"

        try:
            defaut = self.theorie.ajouter_defaut(texte)
        except ValueError as e:
            self.erreur("Défaut incorrect", str(e))
            return

        # Avertissement (le défaut reste ajouté) : justification incohérente
        avertissements = avertissements_defaut(defaut)
        if avertissements:
            messagebox.showwarning(
                "Avertissement",
                "\n".join(avertissements)
                + "\n\nCe défaut ne sera jamais applicable.")

        for entree in (self.entree_pre, self.entree_just, self.entree_cons):
            entree.delete(0, "end")
        self.rafraichir()

    def supprimer_defaut(self):
        i = self._indice_selection(self.liste_d, "un défaut")
        if i is not None:
            del self.theorie.D[i]
            self.rafraichir()

    # ------------------------------------------------------------------
    # Extensions, conséquences sceptiques et crédules
    # ------------------------------------------------------------------
    def _calculer_extensions(self):
        """Appelle generer_extensions ; renvoie None en cas d'erreur."""
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            return generer_extensions(self.theorie)
        except ValueError as e:
            self.erreur("Calcul impossible", str(e))
            return None
        finally:
            self.config(cursor="")

    def _litteraux(self, base):
        """Littéraux (P ou ¬P) qui sont des conséquences de la base."""
        if not est_coherent(base):
            return ["(base incohérente)"]
        resultat = []
        for nom in variables(base):
            symbole = Symbol(nom)
            if consequence(base, symbole):
                resultat.append(nom)
            elif consequence(base, ~symbole):
                resultat.append("¬" + nom)
        return resultat

    def _noms_defauts(self, numeros):
        return ", ".join(f"d{n}" for n in numeros) if numeros else "aucun"

    def generer(self):
        self.rafraichir()
        extensions = self._calculer_extensions()
        if extensions is None:
            return

        self.effacer_resultats()
        if not extensions:
            self.ecrire("Aucune extension.\n", "ko")
            self.ecrire("Cette théorie des défauts n'a pas d'extension.\n",
                        "gris")
            return

        pluriel = "s" if len(extensions) > 1 else ""
        self.ecrire(f"{len(extensions)} extension{pluriel}\n", "titre")

        for i, ext in enumerate(extensions, start=1):
            base = ", ".join(afficher_formule(f) for f in ext.base)
            litteraux = ", ".join(self._litteraux(ext.base)) or "aucun"
            self.ecrire(f"\nE{i} ", "titre")
            self.ecrire(f"= Th({{{base}}})\n")
            self.ecrire(f"    littéraux : {litteraux}\n")
            self.ecrire("    défauts appliqués : "
                        f"{self._noms_defauts(ext.defauts_appliques)}\n")

    def _tester_consequence(self, fonction, nom):
        """Code commun aux boutons Sceptique ? et Crédule ?"""
        texte = self.entree_phi.get()
        try:
            phi = lire_formule(texte)
        except ValueError as e:
            self.erreur("Formule φ incorrecte", str(e))
            return

        extensions = self._calculer_extensions()
        if extensions is None:
            return

        self.effacer_resultats()
        phi_texte = afficher_formule(phi)
        reponse = fonction(extensions, phi)

        if reponse is None:  # aucune extension
            self.ecrire("Aucune extension : ", "ko")
            self.ecrire(f"la conséquence {nom} de {phi_texte} "
                        "n'est pas définie.\n")
            return

        self.ecrire(f"{phi_texte} est une conséquence {nom} ? ", "titre")
        self.ecrire("OUI\n" if reponse else "NON\n", "ok" if reponse else "ko")

        contenant = [i for i, e in enumerate(extensions, start=1)
                     if consequence(e.base, phi)]
        if contenant:
            liste = ", ".join(f"E{i}" for i in contenant)
            self.ecrire(f"Extensions contenant {phi_texte} : {liste} "
                        f"(sur {len(extensions)})\n")
        else:
            self.ecrire(f"Aucune des {len(extensions)} extension(s) "
                        f"ne contient {phi_texte}.\n")

    def tester_sceptique(self):
        self._tester_consequence(sceptique, "sceptique")

    def tester_credule(self):
        self._tester_consequence(credule, "crédule")

    # ------------------------------------------------------------------
    # Fichiers et exemples
    # ------------------------------------------------------------------
    def nouveau(self):
        if (self.theorie.W or self.theorie.D) and not messagebox.askyesno(
                "Nouvelle théorie",
                "Effacer la théorie actuelle ?"):
            return
        self.theorie = Theorie()
        self.effacer_resultats()
        self.rafraichir()

    def ouvrir(self):
        chemin = filedialog.askopenfilename(
            title="Ouvrir une théorie",
            filetypes=[("Théorie JSON", "*.json"), ("Tous les fichiers", "*")])
        if not chemin:
            return
        try:
            self.theorie = Theorie.charger(chemin)
        except (ValueError, json.JSONDecodeError) as e:
            self.erreur("Fichier invalide", str(e))
            return
        except OSError as e:
            self.erreur("Erreur de lecture", str(e))
            return
        self.effacer_resultats()
        self.rafraichir()
        self.ecrire(f"Théorie chargée : {len(self.theorie.W)} formule(s), "
                    f"{len(self.theorie.D)} défaut(s).\n", "gris")

    def enregistrer(self):
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer la théorie", defaultextension=".json",
            filetypes=[("Théorie JSON", "*.json")])
        if not chemin:
            return
        try:
            self.theorie.enregistrer(chemin)
        except OSError as e:
            self.erreur("Erreur d'écriture", str(e))
            return
        self.effacer_resultats()
        self.ecrire(f"Théorie enregistrée dans {chemin}\n", "gris")

    def charger_exemple(self, nom):
        formules, defauts = EXEMPLES[nom]
        theorie = Theorie()
        try:
            for f in formules:
                theorie.ajouter_formule(f)
            for d in defauts:
                theorie.ajouter_defaut(d)
        except ValueError as e:
            self.erreur("Exemple invalide", str(e))
            return
        self.theorie = theorie
        self.effacer_resultats()
        self.rafraichir()
        self.ecrire(f"Exemple chargé : {nom}\n", "gris")
