'''
A test module for ttrating
Copyright(c) 2020 Tatsuzo Osawa
All rights reserved. This program and the accompanying materials
are made available under the terms of the MIT License:
    https: // opensource.org/licenses/mit-license.php
'''
import os
import glob
import pytest


@pytest.fixture()
def cleanup():
    yield
    for file in glob.glob('./tests/data/temp*'):
        os.remove(file)


def test_Tornaments(cleanup):
    from src import ittf
    filename_input = './tests/data/test_tournaments.json'
    tournaments = ittf.Tournaments.read_json(filename_input)
    assert len(tournaments) == 3
    assert tournaments[0].id == '2909'
    assert tournaments.by_id('5139').fm == "2020-01-28"
    assert tournaments.by_name(
        '2020 - Olympic Games, Tokyo (JPN)').id == "2909"
    filename_temp = './tests/data/temp_test_tournaments.json'
    tournaments.to_json(filename_temp)
    tournaments2 = ittf.Tournaments.read_json(filename_temp)
    assert len(tournaments2) == 3
    assert tournaments[0] == tournaments2[0]
    assert tournaments[1] == tournaments2[1]
    assert tournaments[2] == tournaments2[2]


def test_Players(cleanup):
    from src import ittf
    filename_input = './tests/data/test_players.json'
    players = ittf.Players.read_json(filename_input)
    filename_temp = './tests/data/temp_test_players.json'
    players.to_json(filename_temp)
    players2 = ittf.Players.read_json(filename_temp)
    assert len(players) == len(players2)
    assert players.by_id('117821').country == 'JPN'
    assert players.by_id('117821').tournaments['2587']


def test_Matches(cleanup):
    from src import ittf
    filename_input = './tests/data/test_matches.json'
    matches = ittf.Matches.read_json(filename_input)
    filename_temp = './tests/data/temp_test_matches.json'
    matches.to_json(filename_temp)
    matches2 = ittf.Matches.read_json(filename_temp)
    assert len(matches) == len(matches2)
    assert matches[0] == matches2[3]


if __name__ == '__main__':
    pytest.main(['-v', __file__])
