import copy
import ittf

# tournaments.jsonを読み込む
tournaments = ittf.Tournaments()
tournaments.from_json('./tournaments.json')
# players.jsonを読み込む
players_filename = './players.json'
players = ittf.Players()
players.from_json(players_filename)
players.clear()
# matches.jsonを読み込む
matches = ittf.Matches()
matches.from_json('./matches.json')
# calc rating by match
print('Calculating elo ratings ...')

previous_month = '2000-01'
previous_players = []
previous2_players = []

count = 0
correct = 0
for match in [x for x in matches if x.valid]:
    month = tournaments.tournament_by_id(match.tournamentID).fm[:-3]
    if previous_month < month:
        print('{}'.format(previous_month))
        previous_month = month
        previous2_players = copy.deepcopy(previous_players)
        previous_players = copy.deepcopy(players)
    match.fit_player_stats(players)

# players.jsonを書き出す
players.to_json(players_filename)

# playersの一覧表示
print('')
players.items = [x for x in players.items if x.rank < 9999]
players.items.sort(key=lambda x: x.rating, reverse=True)
count = 0
for player in players:
    count += 1
    result_list = [x for x in previous_players if x.id == player.id]
    assert(len(result_list) == 1)
    output = "%d,%s,%s,%s,%d,%d,%d" % (count, player.name, player.nameJa, player.country, player.rank,
                                       player.rating, player.rating - result_list[0].rating)
    output += ',' if player.is_valid_rating() else ',*'  # 試合数が規程未満の印
    output += ",%d,%d" % (player.rating_china, player.rating_china - result_list[0].rating_china)
    output += ',' if player.is_valid_rating_china() else ',*'  # 中国試合数が規程未満の印
    print(output)
