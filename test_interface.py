import sys, os, tempfile
sys.path.insert(0, ".")
from tkinter import messagebox
import interface
from interface import Application

msgs = []
for nom in ("showerror", "showwarning", "showinfo"):
    setattr(messagebox, nom, lambda t, m, _n=nom: msgs.append((_n, t, m)))
messagebox.askyesno = lambda *a, **k: True

app = Application()
def res(): return app.resultats.get("1.0", "end").strip()
def ok(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond: print("   ->", res(), msgs[-1:] )

# 1. exemple de l'énoncé : 1 extension, littéraux o, v, ¬p
app.charger_exemple("Exemple de l'énoncé"); app.generer()
ok("1 extension" in res() and "littéraux : o, ¬p, v" in res() and "d1" in res(), "exemple énoncé")
print(res(), "\n")

# 2. slide 18 : 2 extensions ; C crédule oui, sceptique non
app.charger_exemple("Cours - slide 18"); app.generer()
ok("2 extensions" in res(), "slide 18 : 2 extensions")
app.entree_phi.insert(0, "C"); app.tester_credule()
ok("OUI" in res(), "C crédule")
app.tester_sceptique(); ok("NON" in res(), "C sceptique = non")
app.entree_phi.delete(0, "end")

# 3. aucune extension
app.charger_exemple("Aucune extension"); app.generer()
ok("Aucune extension" in res(), "aucune extension")
app.entree_phi.insert(0, "A"); app.tester_sceptique()
ok("pas définie" in res(), "sceptique sans extension géré")
app.entree_phi.delete(0, "end")

# 4. Nixon & pingouin
app.charger_exemple("Diamant de Nixon"); app.generer(); ok("2 extensions" in res(), "Nixon 2 ext")
app.charger_exemple("Pingouin (exception)"); app.generer(); ok("1 extension" in res() and "¬Vole(tweety)" in res(), "pingouin")

# 5. erreurs de saisie
msgs.clear()
app.nouveau()
app.entree_formule.insert(0, "P & (Q"); app.ajouter_formule()
ok(msgs and msgs[-1][0] == "showerror" and not app.theorie.W, "formule incorrecte refusée")
msgs.clear(); app.entree_formule.delete(0, "end"); app.ajouter_formule()
ok(msgs and msgs[-1][0] == "showerror", "formule vide refusée")
msgs.clear()
app.entree_just.insert(0, "A"); app.ajouter_defaut()
ok(msgs and msgs[-1][0] == "showerror" and not app.theorie.D, "défaut sans conséquent refusé")
for e in (app.entree_pre, app.entree_just, app.entree_cons): e.delete(0, "end")
msgs.clear()
app.entree_just.insert(0, "x & ~x"); app.entree_cons.insert(0, "y"); app.ajouter_defaut()
ok(msgs and msgs[-1][0] == "showwarning" and len(app.theorie.D) == 1, "justification incohérente : avertissement + ajouté")
msgs.clear(); app.entree_phi.insert(0, "(("); app.tester_credule()
ok(msgs and msgs[-1][0] == "showerror", "φ incorrect")
app.entree_phi.delete(0, "end")

# 6. cohérence de W + surlignage
app.nouveau()
for t in ["P", "P -> Q", "~Q", "R"]:
    app.entree_formule.insert(0, t); app.ajouter_formule()
app.verifier_coherence()
rouges = [i for i in range(4) if app.liste_w.itemcget(i, "bg") == "#f5b7b1"]
ok("incohérent" in res() and rouges == [0, 1, 2], f"incohérence surlignée {rouges}")
app.liste_w.selection_set(3); app.supprimer_formule(); ok(len(app.theorie.W) == 3, "suppression")
app.supprimer_formule(); app.liste_w.selection_clear(0, "end"); msgs.clear(); app.supprimer_formule()
ok(msgs and msgs[-1][0] == "showinfo", "suppression sans sélection")

# 7. enregistrer / ouvrir
chemin = os.path.join(tempfile.mkdtemp(), "t.json")
interface.filedialog.asksaveasfilename = lambda **k: chemin
interface.filedialog.askopenfilename = lambda **k: chemin
app.charger_exemple("Cours - slide 18"); app.enregistrer()
app.nouveau(); app.ouvrir()
ok(len(app.theorie.W) == 1 and len(app.theorie.D) == 2, "JSON aller-retour")
open(chemin, "w").write("{pas du json"); msgs.clear(); app.ouvrir()
ok(msgs and msgs[-1][0] == "showerror", "JSON corrompu géré")

# 8. tous les exemples se chargent
for nom in interface.EXEMPLES:
    app.charger_exemple(nom); app.generer()
ok(True, "tous les exemples")

app.destroy()
print("Tests termines.")
