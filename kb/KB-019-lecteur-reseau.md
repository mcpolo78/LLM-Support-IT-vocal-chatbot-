---
id: KB-019
titre: Lecteur réseau ou dossier partagé inaccessible
categorie: Réseau
public: [personnels]
mots_cles: [lecteur réseau, partage, dossier partagé, serveur, P:, S:, accès refusé, fichiers, croix rouge]
escalade: N1
---

# Lecteur réseau ou dossier partagé inaccessible

## Symptômes
- Le lecteur personnel `P:` ou le lecteur commun `S:` apparaît avec une croix rouge.
- Message « accès refusé » sur un dossier partagé.

## Procédure
1. Vérifiez que le poste est connecté au réseau de l'établissement (un lecteur réseau n'est pas accessible depuis chez soi sans VPN, voir KB-006).
2. Double-cliquez sur le lecteur : la croix rouge disparaît souvent à la première ouverture.
3. Si le lecteur n'apparaît pas, fermez la session et rouvrez-la : les lecteurs sont connectés automatiquement à l'ouverture de session.
4. Pour reconnecter manuellement, tapez `\\fichiers\partage` dans la barre d'adresse de l'Explorateur.
5. **Accès refusé** sur un dossier : les droits sont attribués par service ou par équipe. Demandez au responsable du dossier (souvent le secrétariat ou le chef de service) d'en faire la demande.

## Accéder aux fichiers d'un collègue absent
- Ne demandez **jamais** le mot de passe d'un collègue, et ne donnez jamais le vôtre : il est personnel, et même le support ne le communique pas.
- Si des fichiers d'un collègue absent sont indispensables, votre **chef de service** fait la demande au support (KB-018). Le support ouvre alors un accès temporaire au dossier concerné, de façon tracée.
- Pour éviter ce cas, rangez les documents de travail partagés dans le lecteur commun `S:` plutôt que dans votre lecteur personnel.

## Si le problème persiste
- Si tous les postes de l'établissement perdent l'accès en même temps, il s'agit d'un incident serveur : ouvrez un ticket prioritaire ou appelez l'assistance (KB-018).
- Fichier supprimé par erreur : le support peut restaurer une version jusqu'à 30 jours en arrière. Ouvrez un ticket avec le chemin exact du fichier.

_Fiche fictive de démonstration. Les adresses et noms de services sont des exemples._
