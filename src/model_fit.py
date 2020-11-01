import tensorflow as tf
import numpy as np
from tensorflow_core.python.keras.metrics import binary_accuracy
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

import copy
import ittf

# MatchExの作成
matches_ex = ittf.MatchesEx()
filename = './matches_ex.json'
try:
    matches_ex.from_json(filename)
except FileNotFoundError:
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
    previous_month = -1000
    month_str = '2020-04'
    current_month = int(month_str[:4]) * 12 + int(month_str[5:]) - 1
    previous_players = []
    previous_24months_matches_ex = []
    for match in [x for x in matches if x.valid]:
        tournament = tournaments.tournament_by_id(match.tournamentID)
        month_str = tournament.fm[:-3]
        month = (int(month_str[:4]) * 12 + int(month_str[5:]) - 1) - current_month  # current == 0, before == -1, ...
        if previous_month < month:
            players_csv_filename = './ranking/Women Singles_Y{}_{:0>2}.csv'.format(month_str[:4], month_str[5:])
            try:
                players.merge_from_csv(players_csv_filename, append=True)
            except FileNotFoundError:
                print('{} is not found.'.format(players_csv_filename))
            previous_month = month
            players.calc_ema()
            previous_players = copy.deepcopy(players)
            previous_24months_matches_ex = [x for x in matches_ex if (x.month < month) and (x.month >= month - 24)]
        try:
            match_players = players.player_by_id(match.players_id[0]), players.player_by_id(match.players_id[1])
            match_players_pre = previous_players.player_by_id(match.players_id[0]), \
                                previous_players.player_by_id(match.players_id[1])
        except AssertionError:
            print('Skip this match.')
            continue
        match.fit_player_stats(players)
        match_ex = ittf.MatchEx()
        for index in range(2):
            match_ex.result[index].from_player(match_players[index])
            match_ex.result[index].rating = match_players_pre[index].rating
            match_ex.result[index].rating_china = match_players_pre[index].rating_china
            match_ex.result[index].is_valid_rating = match_players_pre[index].is_valid_rating()
            match_ex.result[index].res = int(match.result[index])
            match_ex.result[index].win = match.win()[index]
        match_ex.month = month
        match_ex.tournamentID = tournament.id
        match_ex.tournament_type = tournament.type
        match_ex.round = match.round
        match_history = [x for x in previous_24months_matches_ex
                         if match_ex.result[0] in x.result and match_ex.result[1] in x.result]
        for player_ex in match_ex.result:
            player_ex.wins_of_match = len([x for x in match_history if x.is_win(ittf.PlayerEx)])
            player_ex.res_of_match = sum(x.res(ittf.PlayerEx) for x in match_history)
            player_ex.count = len([x for x in previous_24months_matches_ex if player_ex in x.result])
            player_ex.count_great = len([x for x in previous_24months_matches_ex
                                         if x.is_great() and player_ex in x.result])
            player_ex.wins = len([x for x in previous_24months_matches_ex if x.is_win(ittf.PlayerEx)])
        matches_ex.append(match_ex)
    print('done. Total #{} of matches.'.format(len(matches_ex)))
    players.to_json(players_filename)
    matches_ex.to_json(filename)

# データセットの前処理
matches_ex.remain_valid()
ds_features, ds_labels = matches_ex.data_set()
ms = MinMaxScaler()
ds_features = ms.fit_transform(ds_features)  # 正規化

# データセットを訓練用と検証用に分割
while True:
    training_features, validation_features, training_labels, validation_labels \
        = train_test_split(ds_features, ds_labels)
    training_score = sum(((training_features[:, 0] > training_features[:, 1]).astype(np.int)
                          == training_labels).astype(np.int)) / len(training_labels)
    validation_score = sum(((validation_features[:, 0] > validation_features[:, 1]).astype(np.int)
                            == validation_labels).astype(np.int)) / len(validation_labels)
    if np.abs(training_score - validation_score) < 0.001:
        print('Training score: {}, validation score: {}'.format(training_score, validation_score))
        break

# モデル準備 （正則化項を追加）
INPUT_FEATURES = ds_features.shape[1]  # 特徴量の次元
LAYER_NEURONS = INPUT_FEATURES * 2  # 入力次元より少し広げる
OUTPUT_RESULTS = 1  # 出力は一次元
ACTIVATION = 'tanh'
model = tf.keras.models.Sequential([
#    tf.keras.layers.Dense(input_shape=(INPUT_FEATURES,), units=OUTPUT_RESULTS, activation='sigmoid',
#                          kernel_regularizer=tf.keras.regularizers.l2(0.001)),
# 隠れ層を有効にする際は下記のコードを使う
    tf.keras.layers.Dense(input_shape=(INPUT_FEATURES,), units=LAYER_NEURONS, activation=ACTIVATION,
                          kernel_regularizer=tf.keras.regularizers.l2(0.001)),
    tf.keras.layers.Dense(units=OUTPUT_RESULTS, activation='sigmoid'),
])
LOSS = 'binary_crossentropy'
OPTIMIZER = tf.keras.optimizers.Adam  # 典型的な最適化手法
LEARNING_RATE = 0.03  # 学習係数のよくある初期値
model.compile(optimizer=OPTIMIZER(lr=LEARNING_RATE), loss=LOSS, metrics=[binary_accuracy])

# 学習（アーリーストッピングを行い、それまでの最良のモデルをセーブする）
BATCH_SIZE = 1024
EPOCHS = 200
model_path = './model'
es_cb = EarlyStopping(monitor='val_loss', patience=20, verbose=1, mode='auto')
cp_cb = ModelCheckpoint(filepath=model_path, monitor='val_loss', verbose=1,
                        save_best_only=True, save_weights_only=False, mode='auto')
result = model.fit(x=training_features, y=training_labels,
                   validation_data=(validation_features, validation_labels),
                   batch_size=BATCH_SIZE, epochs=EPOCHS, verbose=1, callbacks=[es_cb, cp_cb], shuffle=True)

model = tf.keras.models.load_model(model_path)
score = model.evaluate(validation_features, validation_labels, verbose=1)
print(score)

# 表示
number_of_epochs_it_ran = len(result.history['loss'])
plt.plot(range(1, number_of_epochs_it_ran + 1), result.history['binary_accuracy'], label="training")
plt.plot(range(1, number_of_epochs_it_ran + 1), result.history['val_binary_accuracy'], label="validation")
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()
