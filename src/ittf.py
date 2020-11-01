import json
import csv
import re
import numpy as np


class MyJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Tournament):
            return o.__dict__
        if isinstance(o, Player):
            return o.__dict__
        if isinstance(o, Match):
            return o.__dict__
        if isinstance(o, PlayerEx):
            return o.__dict__
        if isinstance(o, MatchEx):
            return o.__dict__
        return json.JSONEncoder.default(self, o)


class ListBase:
    def __init__(self):
        self.items = []

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, val):
        self.items[key] = val

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self):
            self.n += 1
            return self.items[self.n - 1]
        else:
            raise StopIteration

    def __contains__(self, val):
        return True if val in self.items else False

    def append(self, val):
        self.items.append(val)


class Tournament:
    def __init__(self):
        self.name = ''
        self.id = ''
        self.year = ''
        self.type = ''
        self.fm = ''
        self.to = ''

    def __repr__(self):
        return "%s: %s (%s - %s)" % (self.id, self.name, self.fm, self.to)

    def __eq__(self, other):
        if not isinstance(other, Tournament):
            return NotImplemented
        return self.id == other.id


class Tournaments(ListBase):
    def from_json(self, filename, log=True):
        with open(filename, 'r') as f:
            json_data = json.load(f)
        for content in json_data:
            o = Tournament()
            o.__dict__ = content
            self.items.append(o)
        if log:
            print('Loaded #{} tournaments from {}'.format(len(self), filename))

    def to_json(self, filename, log=True):
        with open(filename, 'w') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
        if log:
            print('Saved tournaments to {}'.format(filename))

    def tournament_by_id(self, index, log=True):
        result_list = [x for x in self.items if x.id == index]
        if not result_list:
            if log:
                print('Error: Tournament #{} was not registered.'.format(index))
            return None
        return result_list[0]


class Player:
    def __init__(self):
        self.name = ''
        self.nameJa = ''
        self.id = ''
        self.country = ''
        self.rank = 0
        self.points = 0
        self.points_EMA = -1
        self.rating = 1500
        self.rating_EMA = -1
        self.wins = 0
        self.loses = 0
        self.rating_china = 1500
        self.rating_china_EMA = -1
        self.wins_china = 0
        self.loses_china = 0
        self.tournaments = {}
        self.tournaments_last_update = '2000-01-01'

    def __repr__(self):
        return "%s: %s %s (%s) -> %d (%d), W%d - L%d" % (
            self.id, self.name, self.nameJa, self.country, self.rank, self.rating, self.wins, self.loses)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self.id == other.id

    def clear(self):
        self.points_EMA = -1
        self.rating = 1500
        self.rating_EMA = -1
        self.rating_china = 1500
        self.rating_china_EMA = -1
        self.wins = 0
        self.loses = 0
        self.wins_china = 0
        self.loses_china = 0

    def is_valid_rating(self):
        return self.wins + self.loses >= 10

    def is_valid_rating_china(self):
        return self.wins_china + self.loses_china >= 5

    def is_empty(self):
        return self.id == ''

    def is_same_name(self, name):
        return (self.nameJa == name) or (re.sub(r'\s*\^+', '', self.name) == re.sub(r'\s*\^+', '', name))

    def is_naturalized(self):
        return '^' in self.name

    def calc_ema(self):
        ema_rate = 0.4
        self.points_EMA = self.points * ema_rate + self.points_EMA * (1 - ema_rate) \
            if self.points_EMA >= 0 else self.points
        self.rating_EMA = self.rating * ema_rate + self.rating_EMA * (1 - ema_rate) \
            if self.rating_EMA >= 0 else self.rating
        self.rating_china_EMA = self.rating_china * ema_rate + self.rating_china_EMA * (1 - ema_rate) \
            if self.rating_china_EMA >= 0 else self.rating_china


class Players(ListBase):
    def from_json(self, filename, log=True):
        with open(filename, 'r') as f:
            json_data = json.load(f)
        for content in json_data:
            o = Player()
            o.__dict__ = content
            self.items.append(o)
        if log:
            print('Loaded #{} players from {}'.format(len(self), filename))

    def to_json(self, filename, log=True):
        with open(filename, 'w') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
        if log:
            print('Saved players to {}'.format(filename))

    def clear(self):
        for content in self.items:
            content.clear()

    def merge_from_csv(self, filename, append=True, log=True):
        csv_file = open(filename, "r", encoding="utf_8", errors="", newline="")
        csv_data = list(csv.DictReader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"',
                                       skipinitialspace=True))
        for content in self.items:
            content.rank = 9999  # max_player_rank
        for content in csv_data:
            result_list = [x for x in self.items if x.id == content['ID']]
            assert (len(result_list) <= 1)
            if not result_list:
                player = Player()
                player.name = content['Name']
                player.id = content['ID']
                player.country = content['Assoc']
                player.rank = int(content['Rank'])
                player.points = int(content['Points'])
                if (player not in self.items) and append:
                    self.items.append(player)
            else:
                player = result_list[0]
                player.rank = int(content['Rank'])
                player.points = int(content['Points'])
        if log:
            print('Loaded #{} players from {} -> Total #{} players'.format(len(csv_data), filename, len(self)))

    def apply_name_ja(self, filename):
        with open(filename, 'r') as f:
            player_name_ja = json.load(f)
        for content in self.items:
            content.nameJa = player_name_ja.get(content.name, content.name)

    def player_by_id(self, index, log=True):
        result_list = [x for x in self.items if x.id == index]
        if not result_list:
            if log:
                print('Error: Player #{} was not registered.'.format(index))
            assert False
        return result_list[0]

    def is_valid(self, index):
        result_list = [x for x in self.items if x.id == index]
        if len(result_list) > 1:
            print('Error: Duplicate player id {}', index)
            assert False
        return len(result_list) == 1

    def player_by_name(self, name):
        result_list = [x for x in self.items if x.is_same_name(name)]
        if len(result_list) > 1:
            print('Warning: Duplicate player name {}'.format(name))
        elif len(result_list) == 0:
            print('Warning: Not found player name {}'.format(name))
        assert(len(result_list) == 1)
        return result_list[0]

    def calc_ema(self):
        for content in self.items:
            content.calc_ema()


class Match:
    def __init__(self):
        self.tournamentID = ''
        self.type = ''
        self.players_name = ['', '']
        self.players_id = ['', '']
        self.round = ''
        self.result = ['', '']  # number or 'WO'
        self.valid = True

    def __repr__(self):
        return "%s(%s - %s), %s %s vs %s %s" % (self.tournamentID, self.type, self.round, self.players_name[0],
                                                self.result[0], self.result[1], self.players_name[1])

    def __eq__(self, other):
        if not isinstance(other, Match):
            return NotImplemented
        return ((self.tournamentID == other.tournamentID) and
                (self.type == other.type) and
                (self.round == other.round) and
                (((self.players_name[0] == other.players_name[0]) and (self.players_name[1] == other.players_name[1]))
                 or
                 ((self.players_name[1] == other.players_name[0]) and (self.players_name[0] == other.players_name[1]))))

    def win(self):
        assert (str.isdecimal(self.result[0]) and str.isdecimal(self.result[1]))
        if int(self.result[0]) > int(self.result[1]):
            return 1, 0
        elif int(self.result[1]) > int(self.result[0]):
            return 0, 1
        assert False

    def set_valid(self, players):
        self.valid = players.is_valid(self.players_id[0]) and players.is_valid(self.players_id[1]) \
                     and str.isdecimal(self.result[0]) and str.isdecimal(self.result[1]) \
                     and (int(self.result[0]) != int(self.result[1]))

    def set_player_id(self, players):
        for index in range(2):
            if self.players_id[index] == '':
                try:
                    self.players_id[index] = players.player_by_name(self.players_name[index]).id
                except AssertionError:
                    pass

    def fit_player_stats(self, players):
        match_players = [Players(), Players()]
        win_rating = [0, 0]
        win_rating_china = [0, 0]
        for index in range(2):
            try:
                match_players[index] = players.player_by_id(self.players_id[index])
            except AssertionError:
                print('Skip this match.')
                return
        for index in range(2):
            win_rating[index] = 1 / (10 ** ((match_players[1-index].rating - match_players[index].rating) / 400) + 1)
            match_players[index].wins += self.win()[index]
            match_players[index].loses += self.win()[1-index]
            if match_players[1-index].country == 'CHN':
                win_rating_china[index] = 1 / (10 ** ((match_players[1-index].rating -
                                                       match_players[index].rating_china) / 400) + 1)
                match_players[index].wins_china += self.win()[index]
                match_players[index].loses_china += self.win()[1-index]
        K = [32, 32]
        K_china = [128, 128]
        for index in range(2):
            if (not match_players[index].is_valid_rating()) and match_players[1-index].is_valid_rating():
                K[index], K[1-index] = 128, 0
                K_china[1 - index] = 0
            if not match_players[index].is_valid_rating_china():
                K_china[index] = 512
        for index in range(2):
            match_players[index].rating += K[index] * (self.win()[index] - win_rating[index])
            if match_players[1-index].country == 'CHN':
                match_players[index].rating_china += K_china[index] * (self.win()[index] - win_rating_china[index])

    def sort_key(self):
        result = ''
        if 'MAIN' in self.round:
            result += '1'
        else:
            result += '0'
        if 'Round of 128' in self.round:
            result += '1'
        elif 'Round of 64' in self.round:
            result += '2'
        elif 'Round of 32' in self.round:
            result += '3'
        elif 'Round of 16' in self.round:
            result += '4'
        elif 'Quarterfinals' in self.round:
            result += '5'
        elif 'Semifinals' in self.round:
            result += '6'
        elif 'Finals' in self.round:
            result += '7'
        else:
            result += '0'
        return result


class Matches(ListBase):
    def from_json(self, filename, log=True):
        with open(filename, 'r') as f:
            json_data = json.load(f)
        for content in json_data:
            o = Match()
            o.__dict__ = content
            self.items.append(o)
        if log:
            print('Loaded #{} (#{} valid) matches from {}'.format(len(self), self.count_valid(), filename))

    def to_json(self, filename, log=True):
        with open(filename, 'w') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
        if log:
            print('Saved matches to {}'.format(filename))

    def set_valid(self, players, log=True):
        for match in self:
            match.set_valid(players)
        if log:
            print('Filtered #{} valid matches.'.format(self.count_valid()))

    def set_player_id(self, players):
        for match in self:
            match.set_player_id(players)

    def count_valid(self):
        result_list = [x for x in self if x.valid]
        return len(result_list)

    def sort(self, tournaments):
        self.items.sort(key=lambda x: tournaments.tournament_by_id(x.tournamentID).to + x.sort_key())


class PlayerEx:
    def __init__(self):
        self.name = ''
        self.id = ''
        self.country = ''
        self.rank = 0
        self.points = 0
        self.points_EMA = -1
        self.rating = 1500
        self.rating_EMA = -1
        self.rating_china = 1500
        self.rating_china_EMA = -1
        self.is_valid_rating = False
        self.is_valid_rating_china = False
        self.res = 0
        self.win = 0
        self.wins_of_match = 0   # この対戦での過去2年以内の勝利数
        self.res_of_match = 0   # この対戦での過去2年以内の得セット数
        self.count = 0   # 過去2年以内の試合数
        self.count_great = 0   # 過去2年以内のワールドツアー本戦試合数
        self.wins = 0   # 過去2年以内の勝利数

    def __eq__(self, other):
        if not isinstance(other, PlayerEx):
            return NotImplemented
        return self.id == other.id

    def from_player(self, player):
        self.name = player.name
        self.id = player.id
        self.country = player.country
        self.rank = player.rank
        self.points = player.points
        self.points_EMA = player.points_EMA
        self.rating = player.rating
        self.rating_EMA = player.rating_EMA
        self.rating_china = player.rating_china
        self.rating_china_EMA = player.rating_china_EMA
        self.is_valid_rating = player.is_valid_rating()
        self.is_valid_rating_china = player.is_valid_rating_china()


class MatchEx:
    def __init__(self):
        self.month = 0
        self.tournamentID = ''
        self.tournament_type = ''
        self.round = ''
        self.result = PlayerEx(), PlayerEx()

    def is_great(self):
        return ('World Tour' in self.tournament_type) and ('MAIN' in self.round)

    def is_win(self, player_result):
        return ((self.result[0] == player_result) and self.result[0].win) or \
               ((self.result[1] == player_result) and self.result[1].win)

    def res(self, player_result):
        if self.result[0] == player_result:
            return self.result[0].res
        elif self.result[1] == player_result:
            return self.result[1].res
        return 0


class MatchesEx(ListBase):
    def from_json(self, filename, log=True):
        with open(filename, 'r') as f:
            json_data = json.load(f)
        for content in json_data:
            o = MatchEx()
            o.__dict__ = content
            o1, o2 = PlayerEx(), PlayerEx()
            o1.__dict__, o2.__dict__ = content['result']
            o.result = o1, o2
            self.items.append(o)
        if log:
            print('Loaded #{} matches_ex from {}'.format(len(self.items), filename))

    def to_json(self, filename, log=True):
        with open(filename, 'w') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4, cls=MyJSONEncoder)
        if log:
            print('Saved players to {}'.format(filename))

    def remain_valid(self):
        self.filter(lambda x: x.month >= -24 and x.result[0].is_valid_rating and x.result[1].is_valid_rating and
                    x.result[0].rank < 9999 and x.result[1].rank < 9999)

    def filter(self, func):
        self.items = [x for x in self.items if func(x)]

    def data_set(self):
        match_features = []
        match_labels = []
        for match_ex in self.items:
            A, X = match_ex.result
            rating_a, rating_x = A.rating, X.rating
            china_a, china_x = int(A.country == 'CHN'), int(X.country == 'CHN')
            if A.is_valid_rating_china and china_x == 1:
                rating_a = A.rating_china
                china_x = 0
            if X.is_valid_rating_china and china_a == 1:
                rating_x = X.rating_china
                china_a = 0
            match_features.append([rating_a, rating_x, china_a, china_x,
                                   A.points, X.points,
                                   ])
            match_labels.append(A.win)
        return np.array(match_features), np.array(match_labels)
