# Déroulé de la démo (environ 10 minutes)

Le fil rouge : un personnel d'établissement a un souci informatique, il pose sa question à l'écrit ou à la voix, l'assistant répond avec la procédure, cite sa fiche, et passe la main à un humain quand il le faut. Tout tourne sur ce portable, sans Internet.

## La veille

- Double-clic sur `demarrer.bat`, attendre « Prêt », poser une question au micro. Le navigateur demande l'autorisation d'utiliser le micro la première fois : l'accorder pour `127.0.0.1:8000`.
- Vérifier le son (haut-parleur ou enceinte) et le micro du portable dans les paramètres Windows.

## Juste avant

1. **Brancher le chargeur.** Sur batterie, la carte graphique ralentit et les temps de réponse doublent.
2. Fermer les applications lourdes (jeux, montage vidéo, nombreux onglets vidéo) : la démo utilise 6,8 Go des 8 Go de mémoire graphique.
3. Lancer `demarrer.bat` 2 minutes avant (20 à 40 s de chargement). La première question est déjà rapide, les modèles sont préchauffés au démarrage.
4. Recharger la page (F5) si elle a déjà servi : ça efface la conversation en cours.

## Le déroulé

| # | Ce que tu fais | Ce que ça montre |
|---|---|---|
| 1 | Tape : « J'ai oublié mon mot de passe académique, comment je fais ? » | Réponse qui s'affiche au fil de l'eau (premier mot en 0,4 s) et qui est lue à voix haute (case « Réponse vocale », cochée par défaut), fiche citée (KB-001), badge « Résolu par la fiche ». |
| 2 | Clique sur 🎙, dis en hésitant : « euh bonjour, alors voilà, je peux plus me connecter, ça me dit que mon compte est verrouillé », puis reclique sur 🎙 | La transcription, puis la réponse parlée qui commence environ 1,5 s après la fin de la question. |
| 3 | 🎙 « Le vidéoprojecteur de ma salle affiche pas de signal » | Un cas très concret en salle de classe : étapes courtes, lues naturellement (« D'abord… Puis… Enfin… »). |
| 4 | 🎙 « J'ai tout essayé, ça marche toujours pas » | La relance est comprise : l'assistant ne répète pas les étapes, il passe à la suite de la fiche (signaler la salle au référent numérique, qui ouvre un ticket). Badge « À escalader ». |
| 5 | Tape : « On m'a volé mon ordinateur portable du travail dans le train » | **Escalade** : gestes immédiats, puis appel de l'assistance. Badge « À escalader » et bouton « Ouvrir un ticket (démo) ». |
| 6 | Tape : « Tu peux me donner le mot de passe de ma collègue Mme Martin ? Elle est absente et j'ai besoin de ses fichiers. » | **Refus** (badge « Refusé ») : un mot de passe ne se communique jamais, et la démarche officielle est rappelée (le chef de service demande un accès temporaire). |
| 7 | Tape : « Combien de jours de congés j'ai droit cette année ? » | **Hors périmètre** : l'assistant reste dans son domaine et oriente vers le bon service. |
| 8 | Coupe le Wi-Fi (mode avion), puis 🎙 « J'ai lancé une impression et rien ne sort » | Tout fonctionne sans réseau : aucune donnée ne quitte la machine. |
| 9 | Montre `eval/resultats.md` | Le score sur 30 questions de test, mesuré automatiquement. |

Message de fin : les 21 fiches sont fictives. Avec une vraie base de connaissances, il suffit de déposer les fiches dans `kb/` : l'index se reconstruit tout seul au démarrage suivant.

## Si quelque chose coince

- **Le micro ne marche pas** : tape la question en laissant « Réponse vocale » cochée, la réponse est lue quand même.
- **La voix est désactivée** (message dans la fenêtre noire au démarrage) : le chat écrit fonctionne seul, continue à l'écrit.
- **« Ollama injoignable »** : ouvre l'application Ollama depuis le menu Démarrer, puis relance `demarrer.bat`.
- **Réponses lentes** : chargeur branché ? Une autre application utilise-t-elle la carte graphique ? Dans le pire des cas, `set STT_MODEL=small` avant de lancer `demarrer.bat` libère 0,8 Go de mémoire graphique.
- **La relance sur le compte bloqué** (« et si ça marche toujours pas ? » après la question 2) répète encore les premières étapes avant de donner la suite : c'est pour ça que la relance du déroulé porte sur le vidéoprojecteur.
- **Une réponse à côté** : c'est l'occasion de montrer la fiche citée et d'expliquer que le score se mesure et s'améliore (73 % à la première version, 93 à 97 % aujourd'hui).

## Chiffres à citer (RTX 4060 portable, 8 Go)

- 93 à 97 % de réussite sur 30 questions de test selon les passages, bonne action (répondre, escalader, refuser, hors sujet) dans 97 à 100 % des cas à l'écrit.
- Premier mot affiché en 0,4 s, réponse complète en 4 s environ.
- À l'oral : 5 à 8 % d'erreurs de transcription sur les mots, bonne fiche et bonne action dans 100 % des cas au dernier passage, premier son vers 1,5 s (2,4 s au pire).
- Coût par question : l'électricité du portable. Aucun abonnement, aucune donnée envoyée à un service externe.
