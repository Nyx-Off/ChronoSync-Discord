import datetime
import json
import pytz
import requests
from icalendar import Calendar

# Constantes
ICAL_URL = ""
WEBHOOK_URL = ""
FICHIER_EMPLOI_DU_TEMPS = "emploi_du_temps.json"
FICHIER_DERNIER_ENVOI = "dernier_envoi.json"

def verifier_et_envoyer_samedi(nouvel_emploi):
    try:
        with open(FICHIER_DERNIER_ENVOI, 'r') as fichier:
            dernier_envoi = json.load(fichier)
    except FileNotFoundError:
        dernier_envoi = {"date": None}

    aujourd_hui = datetime.datetime.today().strftime("%d-%m-%Y")
    if dernier_envoi["date"] != aujourd_hui:
        date_debut, date_fin = calculer_periode_suivante()
        messages_embed = formater_message_pour_discord(nouvel_emploi, date_debut, date_fin)
        notifier_discord(messages_embed)

        with open(FICHIER_DERNIER_ENVOI, 'w') as fichier:
            json.dump({"date": aujourd_hui}, fichier)

def obtenir_emploi_du_temps():
    reponse = requests.get(ICAL_URL)
    calendrier = Calendar.from_ical(reponse.text)
    timezone = pytz.timezone("Europe/Paris") 

    maintenant = datetime.datetime.now(pytz.utc)
    aujourd_hui = maintenant.astimezone(timezone)
    fin_periode = aujourd_hui + datetime.timedelta(weeks=4)

    emploi_du_temps = {}
    for composant in calendrier.walk():
        if composant.name == "VEVENT":
            date_debut = composant.get('dtstart').dt
            date_fin = composant.get('dtend').dt

            if date_debut.tzinfo is not None:
                date_debut = date_debut.astimezone(timezone)
            if date_fin.tzinfo is not None:
                date_fin = date_fin.astimezone(timezone)

            # Filtre pour les 4 semaines à venir
            if not (aujourd_hui <= date_debut <= fin_periode):
                continue

            jour = date_debut.strftime("%d-%m-%Y")
            resume = composant.get('summary')
            salle = composant.get('location')

            if jour not in emploi_du_temps:
                emploi_du_temps[jour] = []
            emploi_du_temps[jour].append({
                "matière": resume,
                "horaire": f"{date_debut.strftime('%H:%M')} - {date_fin.strftime('%H:%M')}",
                "salle": salle
            })

    return emploi_du_temps


def comparer_emploi_du_temps(nouvel_emploi):
    modifications = False
    details_modifications = []

    # Charger l'ancien emploi du temps depuis un fichier
    try:
        with open(FICHIER_EMPLOI_DU_TEMPS, 'r') as fichier:
            ancien_emploi = json.load(fichier)
    except FileNotFoundError:
        ancien_emploi = {}

    for jour, nouveaux_cours in nouvel_emploi.items():
        cours_anciens = ancien_emploi.get(jour, [])
        
        # Comparer les cours pour chaque jour
        for cours in nouveaux_cours:
            if cours not in cours_anciens:
                modifications = True
                details_modifications.append((jour, "Ajouté", cours))

        for cours in cours_anciens:
            if cours not in nouveaux_cours:
                modifications = True
                details_modifications.append((jour, "Supprimé", cours))

    # Gestion des modifications futures (plus de deux semaines plus tard)
    maintenant = datetime.datetime.now(pytz.utc)
    timezone = pytz.timezone("Europe/Paris")
    dans_deux_semaines = maintenant + datetime.timedelta(weeks=2)
    modifications_futures = [(jour, type_modif, cours) for jour, type_modif, cours in details_modifications if datetime.datetime.strptime(jour, "%d-%m-%Y").astimezone(timezone) > dans_deux_semaines]

    return modifications, details_modifications, modifications_futures


def calculer_periode_suivante():
    aujourd_hui = datetime.datetime.now()
    prochain_lundi = aujourd_hui + datetime.timedelta(days=(7 - aujourd_hui.weekday()))
    fin_semaine = prochain_lundi + datetime.timedelta(days=6)
    return prochain_lundi.strftime("%d-%m-%Y"), fin_semaine.strftime("%d-%m-%Y")

def notifier_discord(messages):
    headers = {"Content-Type": "application/json"}
    for message in messages:
        data = {"embeds": [message]}
        print("Données envoyées à Discord:", json.dumps(data, indent=4))  # Ajout d'une instruction d'impression
        response = requests.post(WEBHOOK_URL, json=data, headers=headers)
        if response.status_code != 204:
            print("Erreur lors de l'envoi du message à Discord")
            print("Statut de la réponse : ", response.status_code)
            print("Corps de la réponse : ", response.text)

def formater_message_pour_discord(emploi_du_temps, date_debut, date_fin):
    messages = []
    jours_de_la_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    date_debut_obj = datetime.datetime.strptime(date_debut, "%d-%m-%Y")
    date_fin_obj = datetime.datetime.strptime(date_fin, "%d-%m-%Y")

    for jour_str, cours_du_jour in emploi_du_temps.items():
        jour_date = datetime.datetime.strptime(jour_str, "%d-%m-%Y")
        if jour_date < date_debut_obj or jour_date > date_fin_obj:
            continue  # Ignorer les jours en dehors de la semaine à venir

        nom_jour = jours_de_la_semaine[jour_date.weekday()]
        embed = {"title": f"{nom_jour} {jour_str}", "color": 0x0000FF, "fields": []}  # Bleu

        if not cours_du_jour:
            embed["fields"].append({
                "name": "Pas de cours",
                "value": "Aucun cours programmé pour ce jour.",
                "inline": False
            })
        else:
            for cours in cours_du_jour:
                embed["fields"].append({
                    "name": cours["matière"],
                    "value": f"Salle : {cours.get('salle', 'Non spécifiée')}\nHoraire : {cours['horaire']}",
                    "inline": False
                })

        messages.append(embed)
    return messages

def main():
    nouvel_emploi = obtenir_emploi_du_temps()
    aujourd_hui = datetime.datetime.today()
    est_samedi = aujourd_hui.weekday() == 5  # Samedi est le 6ème jour (commençant à 0)

    modifications, details_modifications, modifications_futures = comparer_emploi_du_temps(nouvel_emploi)

    # Gestion des envois uniques le samedi
    if est_samedi:
        verifier_et_envoyer_samedi(nouvel_emploi)

    # Gestion des modifications
    if modifications:
        for jour, type_modif, cours in details_modifications:
            couleur_embed = 0xFF0000 if type_modif == "Supprimé" else 0x00FF00  # Rouge pour suppression, Vert pour ajout
            titre_modif = "Modification de l'emploi du temps: " + ("Supprimé" if type_modif == "Supprimé" else "Ajouté")
            embed = {
                "title": titre_modif,
                "color": couleur_embed,
                "fields": [
                    {"name": cours["matière"], "value": f"Jour : {jour}\nHoraire : {cours['horaire']}\nSalle : {cours.get('salle', 'Non spécifiée')}", "inline": False}
                ]
            }
            notifier_discord([embed])

        # Renouveler l'envoi de l'emploi du temps mis à jour
        date_debut, date_fin = calculer_periode_suivante()
        messages_embed = formater_message_pour_discord(nouvel_emploi, date_debut, date_fin)
        notifier_discord(messages_embed)

    # Gestion des modifications futures (plus de deux semaines plus tard)
    for jour, type_modif, cours in modifications_futures:
        couleur_embed = 0x00FF00  # Vert pour ajout
        embed = {
            "title": f"Modification future de l'emploi du temps: {type_modif}",
            "color": couleur_embed,
            "fields": [
                {"name": cours["matière"], "value": f"Jour : {jour}\nHoraire : {cours['horaire']}\nSalle : {cours.get('salle', 'Non spécifiée')}", "inline": False}
            ]
        }
        notifier_discord([embed])

    # Sauvegarder le nouvel emploi du temps
    with open(FICHIER_EMPLOI_DU_TEMPS, 'w') as fichier:
        json.dump(nouvel_emploi, fichier)

if __name__ == "__main__":
    main()
