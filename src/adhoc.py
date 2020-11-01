import ittf

# tournaments.jsonを読み込む
tournaments = ittf.Tournaments()
tournaments.from_json('./tournaments.json')
# matches.jsonを読み込む
matches = ittf.Matches()
matches.from_json('./matches.json')

previous_month = '2000-01'
players = ittf.Players()

count = 0
correct = 0
skip_this_month = True
for match in [x for x in matches if x.valid]:
    month = tournaments.tournament_by_id(match.tournamentID).fm[:-3]
    if previous_month < month:
        if count == 0:
            print('{}, no content'.format(previous_month))
        else:
            print('{},{},{},{}'.format(previous_month, correct / count, count, correct))
        players_csv_filename = './ranking/Women Singles_Y{}_{:0>2}.csv'.format(month[0:4], month[-2:])
        players = ittf.Players()
        try:
            players.merge_from_csv(players_csv_filename, log=False)
            skip_this_month = False
        except FileNotFoundError:
            print('{} is not found.'.format(players_csv_filename))
            skip_this_month = True
        finally:
            previous_month = month
            correct = 0
            count = 0
    if skip_this_month:
        continue
    try:
        playerA = players.player_by_id(match.playerA_id, False)
        playerX = players.player_by_id(match.playerX_id, False)
        count += 1
        if ((playerA.rank < playerX.rank) and match.win_a() == 1) or \
                ((playerA.rank > playerX.rank) and match.win_x() == 1):
            correct += 1
    except AssertionError:
        pass

print('{},{},{},{}'.format(previous_month, correct / count, count, correct))
