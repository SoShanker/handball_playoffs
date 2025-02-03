from bs4 import BeautifulSoup
import os
import requests
import json
import pandas as pd

FFHB_URL = "https://www.ffhandball.fr/competitions/saison-2024-2025-20/regional/prenationale-masculine-25813"
HEADERS = {
    'User-agent':
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
}
PROXIES = {
    'http': os.getenv('HTTP_PROXY')
}

def check_if_win(team, team1, score1, score2):
    score1 = int(score1)
    score2 = int(score2)
    if score1 > score2:
        if team == team1:
            diff_buts = score1-score2
            points = 3
        else:
            diff_buts = score2-score1
            points = 1
    elif score1 == score2:
        return 2, 0
    else:
        if team == team1:
            diff_buts = (score1-score2)
            points = 1
        else:
            points = 3
            diff_buts = score2-score1

    return points, diff_buts

team_ids = {
    "CSM PUTEAUX":"1757723",
    "HBC LIVRY-GARGAN 1B":"1757724",
    "ENT. BOURGET / AULNAY":"1757725",
    "ES MONTGERON":"1757726",
    "ASV CHATENAY-MALABRY":"1757727",
    "US ALFORTVILLE":"1757728",
    "ES SUCY":"1757729",
    "US PALAISEAU":"1757730",
    "ENT. ST-MAUR / MAISONS-ALFORT 1B":"1757731",
    "ST-DENIS HB":"1757732",
    "COURBEVOIE HB":"1757733",
    "ES BRUNOY":"1757734",
    "ASNIERES HBC":"1757735",
    "PLAISIR –\xa0LES CLAYES HB":"1757736",
    "MONTREUIL HB":"1757737",
    "AS BONDY":"1757738",
}

poules = ["147553", "147554"]


teams = {}
for poule in poules:
    html = requests.get(
        f'{FFHB_URL}/poule-{poule}/', headers=HEADERS, proxies=PROXIES).text

    soup = BeautifulSoup(html, "html.parser")
    # print(soup)
    # Get ranking
    div = soup.find('div', class_='competition-right-col')
    smartfire_component = div.find('smartfire-component')
    json_data = smartfire_component["attributes"]
    data = json.loads(json_data)
    classement = data.get("classements", [])

    ids = []
    for team in classement:
        print(team)
        if int(team["place"]) > 4:
            continue
        teams[team["equipe_libelle"]] = {
            "place": team["place"],
            "id": team["id"],
            "diff_buts": 0,
            "playoff_points": 0,
            "games": 0
        }
        ids.append([team_ids[team["equipe_libelle"]], team["equipe_libelle"]])

    names_top4 = [x[1] for x in ids]
    # Compute classement in the next round
    for id in ids:
        print(
            id[1], f"{FFHB_URL}/equipe-{id[0]}")
        html = requests.get(
            f'{FFHB_URL}/equipe-{id[0]}/', headers=HEADERS, proxies=PROXIES).text
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", class_='competition competition-cols-layout')
        smartfire_component = div.find('smartfire-component')
        json_data = smartfire_component["attributes"]
        data = json.loads(json_data)
        for rencontre in data["rencontres"]:
            equipe1, equipe2 = rencontre["equipe1Libelle"], rencontre["equipe2Libelle"]
            if equipe1 in names_top4 and equipe2 in names_top4:
                score1, score2 = rencontre["equipe1Score"], rencontre["equipe2Score"]
                if not score1:
                    break
                points, diff = check_if_win(id[1], equipe1, score1, score2)
                teams[id[1]]["playoff_points"] += points
                teams[id[1]]["games"] += 1
                teams[id[1]]["diff_buts"] += diff

# Build a table of the teams
classement_playoffs = []
for team in teams:
    classement_playoffs.append(
        [team, teams[team]["playoff_points"], teams[team]["games"], teams[team]["diff_buts"]])

classement_playoffs_df = pd.DataFrame(classement_playoffs, columns=[
                                      "Equipe", "Points", "Games", "Goal average"])
classement_playoffs_df = classement_playoffs_df.sort_values(
    ["Points", "Goal average"], ascending=False, ignore_index=True)

classement_playoffs_df.to_csv("E:/nosave/Classement Playoff.csv")
