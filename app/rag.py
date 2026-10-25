"""Moteur RAG : recherche des fiches, construction du prompt, réponse du LLM."""
import re
import time
from dataclasses import dataclass, field

from . import config, ollama_client
from .index import ouvrir

ACTIONS = ("repondre", "escalader", "refuser", "hors_perimetre")

CONSIGNES = f"""Tu es l'assistant du support informatique d'une académie (prototype de démonstration). \
Tu aides les personnels des établissements scolaires.

Règles :
1. Réponds uniquement à partir des fiches fournies dans le contexte. N'invente jamais de procédure, \
d'adresse, de numéro de téléphone ou de délai.
2. Réponds en français, simplement, comme à l'oral : une phrase d'introduction puis au plus 5 étapes \
numérotées et courtes. 120 mots maximum. Garde les informations précises des fiches (chiffres, délais, \
noms de menus).
3. Si aucune fiche ne répond à la question, dis-le franchement et propose d'ouvrir un ticket ou \
d'appeler l'assistance.
4. Urgence ou sécurité (matériel volé ou perdu, mot de passe saisi sur un site frauduleux, danger \
physique comme de la fumée ou une odeur de brûlé) : donne d'abord les gestes immédiats de la fiche, \
puis demande d'appeler l'assistance par téléphone tout de suite.
5. Si on te demande le mot de passe d'une autre personne ou de contourner une règle de sécurité, \
refuse clairement : rappelle qu'un mot de passe est personnel et ne se communique jamais, puis \
explique la démarche officielle prévue par les fiches.
6. Si la question ne concerne pas l'informatique (congés, salaire, ressources humaines...), dis \
poliment que ce n'est pas ton domaine et oriente vers le service compétent.

Coordonnées du support : {config.CONTACT_SUPPORT}

Après ta réponse, ajoute toujours exactement ces deux lignes :
SOURCES: <identifiants des fiches utilisées, séparés par des virgules, par exemple KB-004, KB-002 ; ou aucune>
ACTION: <une seule valeur parmi la liste ci-dessous>

Valeurs de ACTION :
- repondre : tu donnes une procédure que la personne peut suivre elle-même. C'est le cas le plus \
fréquent, même si la fiche dit d'ouvrir un ticket quand le problème persiste.
- escalader : seulement pour une urgence ou un incident de sécurité (vol, mot de passe saisi sur un \
site frauduleux, danger physique), ou si aucune fiche ne couvre le problème.
- refuser : seulement quand on te demande le mot de passe d'une autre personne ou de contourner \
une règle de sécurité. Une demande qu'une fiche réserve à certains cas (augmentation de quota, \
installation de logiciel, droits supplémentaires) n'est pas un refus : explique la règle et la \
démarche prévue, avec ACTION repondre.
- hors_perimetre : la question ne concerne pas l'informatique."""

_RE_META = re.compile(r"^\s*[*_`]*\s*(ACTION|SOURCES?)\s*[*_`]*\s*:[^\n]*$", re.I | re.M)
_RE_ACTION = re.compile(r"^\s*[*_`]*\s*ACTION\s*[*_`]*\s*:\s*[*_`]*\s*([a-zé_]+)", re.I | re.M)

# Sur une relance courte (« et si ça marche toujours pas ? »), le modèle recopie sa réponse précédente :
# une consigne dans la question elle-même l'amène à donner la suite de la fiche.
_RE_RELANCE = re.compile(r"toujours pas|marche pas|fonctionne pas|encore|persiste|pareil|rien ne|même problème", re.I)
NOTE_RELANCE = ("(Relance : la personne a déjà suivi les étapes de ta réponse précédente et le problème persiste. "
                "Ne répète pas ces étapes. Donne seulement la suite prévue par la section « Si le problème "
                "persiste » de la fiche, puis propose d'ouvrir un ticket ou d'appeler l'assistance.)")


def est_relance(question, historique):
    return bool(historique) and len(question.split()) <= 12 and bool(_RE_RELANCE.search(question))


@dataclass
class Source:
    id: str
    titre: str
    score: float


@dataclass
class Reponse:
    texte: str
    action: str
    sources: list = field(default_factory=list)
    citees: list = field(default_factory=list)
    duree_recherche_ms: int = 0
    duree_totale_ms: int = 0


def extraire_action(texte):
    """Sépare les lignes « SOURCES: » et « ACTION: » du texte affiché ou lu à voix haute."""
    trouve = _RE_ACTION.findall(texte)
    action = trouve[-1].lower() if trouve else "repondre"
    action = {"répondre": "repondre", "hors": "hors_perimetre"}.get(action, action)
    if action not in ACTIONS:
        action = "repondre"
    propre = _RE_META.sub("", texte).strip()
    return propre, action


def fiches_citees(texte):
    """Fiches citées dans le texte ou sur la ligne SOURCES (texte brut du LLM)."""
    return sorted(set(re.findall(r"KB-\d{3}", texte)))


def _peut_etre_meta(debut_ligne):
    """Vrai si une ligne en cours d'écriture pourrait devenir une ligne SOURCES ou ACTION."""
    tete = debut_ligne.lstrip("*_` ").upper()
    return any(mot.startswith(tete[: len(mot)]) for mot in ("ACTION", "SOURCES", "SOURCE"))


class MoteurRAG:
    def __init__(self):
        self.collection, self.fiches = ouvrir()

    def rechercher(self, requete):
        vecteur = ollama_client.embed([requete])[0]
        res = self.collection.query(query_embeddings=[vecteur], n_results=config.TOP_K_CHUNKS)
        meilleures = {}
        for meta, distance in zip(res["metadatas"][0], res["distances"][0]):
            score = 1 - distance
            fid = meta["fiche"]
            if score > meilleures.get(fid, -1):
                meilleures[fid] = score
        classees = sorted(meilleures.items(), key=lambda x: -x[1])[: config.TOP_FICHES]
        return [Source(fid, self.fiches[fid].titre, round(s, 3)) for fid, s in classees]

    def _messages(self, question, sources, historique):
        retenues = [s for s in sources if s.score >= config.SEUIL_PERTINENCE]
        if retenues:
            contexte = "\n\n".join(
                f'<fiche id="{s.id}">\n[{s.id}] {self.fiches[s.id].corps.lstrip("# ")}\n</fiche>'
                for s in retenues
            )
        else:
            contexte = "(aucune fiche pertinente trouvée)"
        if est_relance(question, historique):
            question = f"{question}\n\n{NOTE_RELANCE}"
        messages = [{"role": "system", "content": CONSIGNES}]
        for tour in historique[-4:]:
            messages.append({"role": tour["role"], "content": tour["content"]})
        messages.append({"role": "user", "content": f"Contexte :\n{contexte}\n\nQuestion : {question}"})
        return messages

    def prechauffer(self):
        """Charge les deux modèles en VRAM pour que la première vraie question soit rapide."""
        ollama_client.embed(["préchauffage"])
        ollama_client.chat([{"role": "user", "content": "Réponds OK."}])

    def _requete(self, question, historique):
        # Pour une relance (« et si ça marche pas ? »), la question précédente aide la recherche.
        precedentes = [t["content"] for t in historique if t["role"] == "user"]
        return f"{precedentes[-1]}\n{question}" if precedentes else question

    def preparer(self, question, historique=()):
        historique = list(historique)
        debut = time.time()
        sources = self.rechercher(self._requete(question, historique))
        duree = int((time.time() - debut) * 1000)
        return sources, self._messages(question, sources, historique), duree

    def repondre(self, question, historique=()):
        debut = time.time()
        sources, messages, duree_recherche = self.preparer(question, historique)
        brut = ollama_client.chat(messages)
        texte, action = extraire_action(brut)
        return Reponse(texte, action, sources, self._citees(brut), duree_recherche,
                       int((time.time() - debut) * 1000))

    def _citees(self, brut):
        return [fid for fid in fiches_citees(brut) if fid in self.fiches]

    def repondre_flux(self, question, historique=()):
        """Générateur d'événements : sources, morceaux de texte, puis fin (action, durées).

        Les lignes « SOURCES: » et « ACTION: » sont retenues pour ne jamais être affichées ni lues.
        """
        debut = time.time()
        sources, messages, duree_recherche = self.preparer(question, historique)
        yield {"type": "sources", "sources": [s.__dict__ for s in sources],
               "duree_recherche_ms": duree_recherche}
        # `ligne` est la ligne en cours, dont `emis` caractères ont déjà été envoyés. Une ligne
        # n'est retenue que si elle commence comme une ligne SOURCES ou ACTION.
        complet, ligne, emis, premier = "", "", 0, None
        for morceau in ollama_client.chat_stream(messages):
            if premier is None:
                premier = int((time.time() - debut) * 1000)
            complet += morceau
            ligne += morceau
            a_emettre = ""
            while "\n" in ligne:
                finie, ligne = ligne.split("\n", 1)
                if emis or not _RE_META.match(finie):
                    a_emettre += finie[emis:] + "\n"
                emis = 0
            if ligne and (emis or not _peut_etre_meta(ligne)):
                a_emettre += ligne[emis:]
                emis = len(ligne)
            if a_emettre:
                yield {"type": "texte", "texte": a_emettre}
        if ligne[emis:] and (emis or not _RE_META.match(ligne)):
            yield {"type": "texte", "texte": ligne[emis:]}
        _, action = extraire_action(complet)
        yield {"type": "fin", "action": action, "citees": self._citees(complet),
               "premier_token_ms": premier, "duree_totale_ms": int((time.time() - debut) * 1000)}
