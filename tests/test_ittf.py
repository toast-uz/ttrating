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
from src import ittf


@pytest.fixture()
def cleanup():
    yield
    for file in glob.glob('./tests/data/temp*'):
        os.remove(file)


def test_Tornaments(cleanup):
    filename_input = './tests/data/test_tournaments1.json'
    tournaments = ittf.Tournaments.read_json(filename_input)
    assert len(tournaments) == 3
    assert tournaments[0].id == '2909'
    assert tournaments.by_id('5139').fm == "2020-01-28"
    assert tournaments.by_name(
        '2020 - Olympic Games, Tokyo (JPN)').id == "2909"
    filename_temp = './tests/data/temp_test_tournaments1.json'
    tournaments.to_json(filename_temp)
    tournaments2 = ittf.Tournaments.read_json(filename_temp)
    assert len(tournaments2) == 3
    assert tournaments[0] == tournaments2[0]
    assert tournaments[1] == tournaments2[1]
    assert tournaments[2] == tournaments2[2]


if __name__ == '__main__':
    pytest.main(['-v', __file__])
