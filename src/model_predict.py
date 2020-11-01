import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

import ittf

tournaments = ittf.Tournaments()
tournaments.from_json('./tournaments.json')
players = ittf.Players()
players.from_json('./players.json')
matches_ex = ittf.MatchesEx()
matches_ex.from_json('./matches_ex.json')
matches_ex.remain_valid()
ds_features, _ = matches_ex.data_set()
ms = MinMaxScaler()
ms.fit(ds_features)
matches_ex.filter(lambda x: x.is_great() and x.month >= -1)
ds_features, _ = matches_ex.data_set()
ds_features = ms.transform(ds_features)

model = tf.keras.models.load_model('./model')
result = model.predict(ds_features, verbose=1).tolist()

for i in range(len(result)):
    match_ex = matches_ex[i]
    tournament = tournaments.tournament_by_id(match_ex.tournamentID)
    ai_rating = result[i][0]
    playerA_ex, playerX_ex = match_ex.result
    playerA = players.player_by_id(playerA_ex.id)
    playerX = players.player_by_id(playerX_ex.id)
    elo_rating = 1 / (10 ** ((playerX_ex.rating - playerA_ex.rating) / 400) + 1)
    print('"{}",{},{},{},{},{},{}'.
          format(tournament.name, match_ex.round,
                 playerA.nameJa, #playerA.points, playerA.points - playerA.points_EMA,
                 playerX.nameJa, #playerX.points, playerX.points - playerX.points_EMA,
                 playerA_ex.win, elo_rating, ai_rating))
