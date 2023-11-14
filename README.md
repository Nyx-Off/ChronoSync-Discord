# ChronoSync-Discord

## Description
L'Assistant de Gestion de l'Emploi du Temps Discord est un programme Python conçu pour automatiser la récupération, le suivi et la notification des changements d'emploi du temps. Il utilise un calendrier iCal pour obtenir les horaires de cours, les compare à une version précédemment enregistrée, et envoie des mises à jour via un webhook Discord. Cet outil est particulièrement utile pour les étudiants ou les administrateurs d'établissements éducatifs qui souhaitent maintenir leur communauté informée des changements d'emploi du temps en temps réel.

## Fonctionnalités
- Récupération automatique de l'emploi du temps depuis un calendrier iCal.
- Comparaison de l'emploi du temps actuel avec la version précédente pour détecter les modifications.
- Envoi de notifications sur Discord pour informer des changements d'emploi du temps.
- Prise en compte des modifications à venir au-delà de deux semaines.
- Gestion des envois uniques le samedi pour une vue d'ensemble de la semaine à venir.

## Prérequis
Pour exécuter ce programme, vous aurez besoin de :

- Python 3.x
- Bibliothèques Python : `datetime, json, pytz, requests, icalendar`

## Installation
Clonez ce dépôt ou téléchargez les fichiers du programme.
Installez les dépendances nécessaires via pip :
`pip install pytz requests icalendar`

## Configuration
Modifiez les constantes ICAL_URL et WEBHOOK_URL dans le script pour correspondre à votre calendrier iCal et à votre webhook Discord.
Ajustez les autres constantes au besoin.

## Utilisation
Exécutez le script avec Python :

`python script.py`

Le programme récupérera l'emploi du temps, détectera les modifications et enverra les notifications sur Discord.

vous pouvez l'executer automatiquement a l'aide de tache cron.

## Contribution
Les contributions à ce projet sont les bienvenues. Vous pouvez proposer des améliorations ou des corrections en ouvrant une issue ou une pull request sur le dépôt GitHub.

## Licence
Ce projet est distribué sous la licence MIT.
