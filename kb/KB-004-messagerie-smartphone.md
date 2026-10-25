---
id: KB-004
titre: Configurer la messagerie académique sur smartphone
categorie: Messagerie
public: [personnels]
mots_cles: [messagerie, courriel, mail, smartphone, téléphone, android, iphone, IMAP, application]
escalade: N1
---

# Configurer la messagerie académique sur smartphone

## Symptômes
- Vous voulez lire vos courriels professionnels sur votre téléphone.
- Votre téléphone ne reçoit plus les courriels depuis un changement de mot de passe.

## Procédure
1. Méthode recommandée : utilisez le **webmail** depuis le navigateur du téléphone : https://webmail.academie-exemple.fr (aucune configuration, rien n'est stocké sur l'appareil).
2. Pour une application de messagerie (Gmail, Mail d'Apple, Outlook), créez un compte de type **IMAP** avec :
   - serveur entrant : `imap.academie-exemple.fr`, port 993, SSL/TLS ;
   - serveur sortant : `smtp.academie-exemple.fr`, port 465, SSL/TLS, authentification obligatoire ;
   - identifiant : votre identifiant académique (pas l'adresse complète) ;
   - mot de passe : votre mot de passe académique.
3. Après un changement de mot de passe, mettez-le à jour dans l'application, sinon votre compte risque d'être bloqué (voir KB-002).

## Si le problème persiste
- Vérifiez d'abord que vous arrivez à vous connecter au webmail depuis un ordinateur. Si le webmail fonctionne mais pas l'application, supprimez le compte de l'application et recréez-le.
- Le support ne prend pas en charge le dépannage des téléphones personnels au-delà de ces paramètres.

_Fiche fictive de démonstration. Les adresses et noms de services sont des exemples._
