import time
import shutil
import datetime
import os
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_binary  # 削除禁止: unusedアノテーションが出るが、削除するとChromeの操作ができなくなる
from bs4 import BeautifulSoup
import ittf

today = str(datetime.date.today())
update_before = '2020-04-18'

max_player_rank = 9999

# players.json をバックアップする
origin_filename = './players.json'
backup_filename = './players{}.json'.format(today)
if os.path.exists(origin_filename) and not os.path.exists(backup_filename):
    print('Backup {} to {}'.format(origin_filename, backup_filename))
    shutil.copy(origin_filename, backup_filename)
# matches.json をバックアップする
origin_filename = './matches.json'
backup_filename = './matches{}.json'.format(today)
if os.path.exists(origin_filename) and not os.path.exists(backup_filename):
    print('Backup {} to {}'.format(origin_filename, backup_filename))
    shutil.copy(origin_filename, backup_filename)

# tournaments.json を読み込む
tournaments_filename = './tournaments.json'
tournaments = ittf.Tournaments()
try:
    tournaments.from_json(tournaments_filename)
# tournaments.jsonが存在しなければITTFからscraping
except FileNotFoundError:
    print('{} is not exist.'.format(tournaments_filename))
    for year in ['2020', '2019', '2018', '2017', '2016']:
        url = 'http://results.ittf.link/index.php?option=com_fabrik&view=list&listid=1&Itemid=111&' \
              'fab_tournaments___code[value][]={}&limit1=200'.format(year)
        print('Request tournaments in {} from ITTF web page ...'.format(year))
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            body = res.read().decode("utf-8")
        soup = BeautifulSoup(body, "lxml").find('body')
        while True:
            soup = soup.find_next(class_='fab_tournaments___tournament_id fabrik_element fabrik_list_1_group_1 integer')
            if soup is None:
                break
            tournament = ittf.Tournament()
            tournament.id = soup.get_text(strip=True)
            soup = soup.find_next(class_='fab_tournaments___code fabrik_element fabrik_list_1_group_1 integer')
            tournament.year = soup.get_text(strip=True)
            soup = soup.find_next(class_='fab_tournaments___tournament fabrik_element fabrik_list_1_group_1')
            tournament.name = soup.get_text(strip=True)
            soup = soup.find_next(class_='fab_tournaments___type fabrik_element fabrik_list_1_group_1')
            tournament.type = soup.get_text(strip=True)
            soup = soup.find_next(class_='fab_tournaments___from fabrik_element fabrik_list_1_group_1')
            tournament.fm = soup.get_text(strip=True)
            soup = soup.find_next(class_='fab_tournaments___to fabrik_element fabrik_list_1_group_1')
            tournament.to = soup.get_text(strip=True)
            print('Found:', tournament)
            tournaments.append(tournament)
        time.sleep(1)
    # tournaments.json を書き出す
    tournaments.to_json(tournaments_filename)
    pass

# players.csv を読み込んでplayersを初期設定する
players = ittf.Players()
players_filename = './players.json'
players.from_json(players_filename)
players.merge_from_csv('./players.csv')
players.apply_name_ja('./player_name_ja.json')
# players.jsonを書き出す
players.to_json(players_filename)

# ITTFからscrapingして、playerごとの出場tournamentsを最新化する
# tournamentsの試合を読み込み済かを判別するため、初期値をFalseとする
options = Options()
options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
options.add_argument('--headless')
for player in players:
    if update_before <= player.tournaments_last_update:
        continue
    if player.rank > max_player_rank:
        continue
    print('Request tournaments of player #{} {} from ITTF web page ...'.format(player.rank, player.name))
    while True:
        driver = webdriver.Chrome(options=options)
        driver.get('https://ranking.ittf.com/#/players/profile/{}/tournaments'.format(player.id))
        time.sleep(5)
        html = driver.page_source
        driver.quit()
        soup = BeautifulSoup(html, "lxml").find('body').find(class_='match-filters')
        if soup is not None:
            break
        print('Failed to get. Waiting 30 seconds to retry to get the same page ...')
        time.sleep(30)
    contents = soup.find_next(class_='match-filters').find_all('option')
    for content in contents[1:]:
        if not content['value'] in player.tournaments:
            player.tournaments[content['value']] = False
    player.tournaments_last_update = today
    print(player.tournaments)
    # players.jsonを書き出す
    players.to_json(players_filename)

matches = ittf.Matches()
matches_filename = './matches.json'
# matches.json を読み込む
try:
    matches.from_json(matches_filename)
except FileNotFoundError:
    print('{} is not exist.'.format(matches_filename))
    pass
# matches.jsonを書き出す
matches.to_json(matches_filename)

# 試合結果未反映のtournamentをITTFからscrapingして反映する
for player in players:
    keys = [k for k, v in player.tournaments.items() if not v]
    if len(keys) == 0:
        continue
    for tournament_id in keys:
        print('Request matches of tournament #{} of player #{} {} from ITTF web page ...'.
              format(tournament_id, player.rank, player.name))
        while True:
            driver = webdriver.Chrome(options=options)
            driver.get('https://ranking.ittf.com/#/players/profile/{}/matches/{}'.format(player.id, tournament_id))
            time.sleep(5)
            html = driver.page_source
            driver.quit()
            soup = BeautifulSoup(html, "lxml").find('body').find(class_='results-table')
            if soup is not None:
                break
            print('Failed to get. Waiting 30 seconds to retry to get the same page ...')
            time.sleep(30)
        while True:
            soup = soup.find_next(class_='results-item')
            if soup is None:
                break
            match = ittf.Match()
            match.tournamentID = tournament_id
            match.type = soup.find('strong').get_text(strip=True)
            if 'doubles' in match.type:
                continue
            match.round = soup.find(class_='table-name').get_text(strip=True)
            soup_name = soup.find(class_='name')
            if soup_name.find('a') is None:  # Detect 'BYE'
                continue
            match.players_name[0] = soup_name.find('a').get_text(strip=True)
            soup_name = soup_name.find_next(class_='name')
            if soup_name is None or soup_name.find('a') is None:  # Detect error or 'BYE'
                continue
            match.players_name[1] = soup_name.find('a').get_text(strip=True)
            if player.is_same_name(match.players_name[0]):
                match.players_id[0] = player.id
            elif player.is_same_name(match.players_name[1]):
                match.players_id[1] = player.id
            soup_res = soup.find(class_='score-item score-total')
            match.result[0] = soup_res.find('span').get_text(strip=True)
            soup_res = soup_res.find_next(class_='score-item score-total')
            match.result[1] = soup_res.find('span').get_text(strip=True)
            if match in matches:
                print('Found but duplicated:', match)
                index = matches.items.index(match)
                if player.is_same_name(matches.items[index].players_name[0]):
                    matches.items[index].players_id[0] = player.id
                elif player.is_same_name(matches.items[index].players_name[1]):
                    matches.items[index].players_id[1] = player.id
            else:
                print('Found and added:', match)
                matches.append(match)
        player.tournaments[tournament_id] = True
    # matches.jsonを書き出す
    matches.to_json(matches_filename)
    # players.jsonを書き出す
    players.to_json(players_filename)

print('Set valid of matches ...')
matches.set_valid(players)
matches.sort(tournaments)
matches.to_json(matches_filename)
