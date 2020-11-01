import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

import random
import ittf

# トーナメント表
tournament_entries = [
    ('CHEN Meng', 'ITO Mima'),
    ('DING Ning', 'ITO Mima')
]

print('\nTournament prediction ...')
random.seed(0)

# players.jsonを読み込む
players = ittf.Players()
players.from_json('./players.json')
# 10試合未満の新規playerを削除する ** 削除より後にplayers.jsonを書き出さないこと
players.items = [x for x in players.items if x.is_valid_rating()]
print('#{} of valid players.'.format(len(players)))
# AIモデルを読み込む
matches_ex = ittf.MatchesEx()
matches_ex.from_json('./matches_ex.json')
matches_ex.remain_valid()
ds_features, _ = matches_ex.data_set()
ms = MinMaxScaler()
ms.fit(ds_features)
model = tf.keras.models.load_model('./model')


class PredictMatch:
    def __init__(self, rating_method='elo'):
        self.rating_method = rating_method
        self.playerA = ittf.Player()
        self.playerX = ittf.Player()
        self.round = 0
        self.result = 0  # 1: Winner is playerA, 0: Winner is playerX

    def __repr__(self):
        return "%r vs %r (%d)->%d" % (self.playerA, self.playerX, self.round, self.result)

    def rating_a(self):
        if self.playerA.is_empty():
            return 0
        elif self.playerX.is_empty():
            return 1
        else:
            if self.rating_method == 'elo':
                return 1 / (10 ** ((self.playerX.rating - self.playerA.rating) / 400) + 1)
            elif self.rating_method == 'ai':
                player_ex_A = ittf.PlayerEx()
                player_ex_A.from_player(self.playerA)
                player_ex_X = ittf.PlayerEx()
                player_ex_X.from_player(self.playerX)
                match_ex = ittf.MatchEx()
                match_ex.result = player_ex_A, player_ex_X
                matches_ex = ittf.MatchesEx()
                matches_ex.append(match_ex)
                ds_features, _ = matches_ex.data_set()
                ds_features = ms.transform(ds_features)
                result = model.predict(ds_features).tolist()
                return result[0][0]
            else:
                assert False

    def eval(self):
        rating = random.random()
        if rating < self.rating_a():
            self.result = 1

    def winner(self):
        if self.result == 0:
            return self.playerX
        else:
            return self.playerA


class PredictTournament:
    def __init__(self, rating_method='elo'):
        self.rating_method = rating_method
        self.size = len(tournament_entries) * 2
        self.matches = []
        for match_pair in tournament_entries:
            match = PredictMatch(rating_method)
            try:
                match.playerA = players.player_by_name(match_pair[0])
                match.playerX = players.player_by_name(match_pair[1])
            except AssertionError:
                pass
            match.round = self.size
            self.matches.append(match)

    def __repr__(self):
        return "%r" % self.matches

    def eval(self, match_round):
        new_match = PredictMatch(self.rating_method)
        new_match_is_setting = False
        for match in [x for x in self.matches if x.round == match_round]:
            match.eval()
            if not new_match_is_setting:
                new_match.playerA = match.winner()
                new_match.round = match.round // 2
                self.matches.append(new_match)
                new_match_is_setting = True
            else:
                self.matches[-1].playerX = match.winner()
                new_match = PredictMatch(self.rating_method)
                new_match_is_setting = False

    def play_out(self):
        match_round = self.size
        while match_round > 1:
            self.eval(match_round)
            match_round = match_round // 2


print('\nMatch rating ...')
tournament_elo = PredictTournament()
tournament_ai = PredictTournament('ai')
for i in range(len(tournament_elo.matches)):
    match = tournament_elo.matches[i]
    A = match.playerA
    X = match.playerX
    elo = match.rating_a()
    ai = tournament_ai.matches[i].rating_a()
    print('{},{},{},{},{},{},{},{},{},{},{},{}'.format(
        A.nameJa, A.country, A.rank, round(A.rating), X.nameJa, X.country, X.rank, round(X.rating),
        elo, A.nameJa if elo > 0.5 else X.nameJa, ai, A.nameJa if ai > 0.5 else X.nameJa))

for rating_method in ['elo', 'ai']:
    print('\nWinner odds with {} ...'.format(rating_method))
    winners_count = {}
    trial_count = 1000
    for i in range(trial_count):
        tournament = PredictTournament(rating_method)
        tournament.play_out()
        winner = tournament.matches[-1].playerA  # Get the next of the last match (playerA == winner)
        if winner.id in winners_count:
            winners_count[winner.id] += 1
        else:
            winners_count[winner.id] = 1
        if i % (trial_count // 100) == 0:  # Show progress indicator
            if i % (trial_count // 10) == 0:
                print('*', end='')
            else:
                print('.', end='')
    print('')

    # Type of winner_count changing from dict to list of tuple
    winners_count = sorted(winners_count.items(), key=lambda x: x[1], reverse=True)

    for player_id, winner_count in winners_count:
        # content = {player.id : winner_count}
        player = players.player_by_id(player_id)
        print('{},{},{},{},{}'.
              format(player.nameJa, player.country, player.rank, player.rating, winner_count / trial_count))
