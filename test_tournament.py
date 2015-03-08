"""Functional testing of tournament.py using a tournament database."""

import os
import subprocess
import unittest

import tournament

SQL_FILE_PATH = os.path.realpath(
    os.path.join(
        os.path.abspath(__file__),
        os.pardir, os.pardir, os.pardir,
        os.pardir, 'tournament.sql'))


class TestTournament(unittest.TestCase):

    """Functional tests for tournament.py."""

    def setUp(self):
        """Create a fresh tournament database."""
        try:
            subprocess.check_call(
                ['psql', '-f', SQL_FILE_PATH],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                "SQL file %s could not be executed: %s" % (
                    SQL_FILE_PATH, error))

    def tearDown(self):
        """Destroy the tournament database."""
        try:
            # DROP cannot run in a transaction block, so use psql
            subprocess.check_call(
                ['psql', '-c', "DROP DATABASE tournament;"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                "The tournament database could not be dropped: %s" % (error))

    def test_delete_matches(self):
        """Test matches can be deleted."""
        tournament_id = tournament.register_tournament(
            "Test Delete Matches", 2)

        player1_id = tournament.register_player("Twilight Sparkle")
        player2_id = tournament.register_player("Fluttershy")

        tournament.register_player_in_tournament(player1_id, tournament_id)
        tournament.register_player_in_tournament(player2_id, tournament_id)

        tournament.report_match(player1_id, player2_id, tournament_id)

        matches_deleted = tournament.delete_matches()
        self.assertEqual(matches_deleted, 2)
        print "* Old matches can be deleted."

    def test_delete_players(self):
        """Test players can be deleted."""
        tournament.register_player("Twilight Sparkle")
        tournament.register_player("Fluttershy")

        players_deleted = tournament.delete_players()
        self.assertEqual(players_deleted, 2)
        print "* Player records can be deleted."

    def test_count(self):
        """Test players can be counted."""
        tournament.register_player("Twilight Sparkle")
        tournament.register_player("Fluttershy")
        counted_players = tournament.count_players()

        # We should have two players that we just registered
        self.assertEqual(counted_players, 2)

        tournament.delete_players()
        counted_players = tournament.count_players()

        # count_players() should return numeric zero, not string '0'
        self.assertNotIsInstance(counted_players, str)

        # After deleting, count_players should return zero
        self.assertEqual(counted_players, 0)
        print "* After deleting, count_players() returns zero."

    def test_register(self):
        """Test players can be registered."""
        tournament.register_player("Chandra Nalaar")
        counted_players = tournament.count_players()

        # After one player registers, count_players() should be 1
        self.assertEqual(counted_players, 1)
        print "* After registering a player, count_players() returns 1."

    def test_register_tournament(self):
        """Test tournaments can be registered."""
        tournament_id = tournament.register_tournament('Test Tournament', 4)

        self.assertIsInstance(tournament_id, int)
        print "* Tournament registered."

    def test_register_player_in_tournament(self):
        """Test players can be registered in tournaments."""
        player_id = tournament.register_player("Chandra Nalaar")
        tournament_id = tournament.register_tournament('My Tournament', 4)
        registered = tournament.register_player_in_tournament(
            player_id, tournament_id)

        self.assertEqual(registered, 1)
        print "* Player registered in tournament."

    def test_register_count_delete(self):
        """Test players can be registered and deleted."""
        tournament.register_player("Markov Chaney")
        tournament.register_player("Joe Malik")
        tournament.register_player("Mao Tsu-hsi")
        tournament.register_player("Atlanta Hope")

        counted_players = tournament.count_players()
        # After registering four players, count_players should be 4
        self.assertEqual(counted_players, 4)

        tournament.delete_players()
        counted_players = tournament.count_players()
        # After deleting, count_players should return zero
        self.assertEqual(counted_players, 0)
        print "* Players can be registered and deleted."

    def test_standings_before_matches(self):
        """Test players standings before matches."""
        tournament.register_player("Melpomene Murray")
        tournament.register_player("Randy Schwartz")
        standings = tournament.player_standings()

        # Players should appear in player_standings before playing in matches
        # Only registered players should appear in standings
        self.assertEqual(len(standings), 2)

        # Each player_standings row should have four columns
        self.assertEqual(len(standings[0]), 4)

        # Newly registered players should have no matches or wins
        [(id1, name1, wins1, match1), (id2, name2, wins2, match2)] = standings
        for standing in (match1, match2, wins1, wins2):
            self.assertEqual(standing, 0)

        # Registered players' names should appear in standings even when
        # no matches have been played.
        self.assertEqual(
            set([name1, name2]), set(["Melpomene Murray", "Randy Schwartz"]))
        print ("* Newly registered players appear in the "
               "standings with no matches.")

    def test_report_matches(self):
        """Test reporting matches."""
        tournament_id = tournament.register_tournament(
            "Test Matches Tournament", 4)
        player_names = (
            "Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant")
        for player_name in player_names:
            tournament.register_player_in_tournament(
                tournament.register_player(player_name), tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        player1, player2, player3, player4 = [row[0] for row in standings]
        tournament.report_match(player1, player2, tournament_id)
        tournament.report_match(player3, player4, tournament_id)

        standings = tournament.player_standings()
        for id, name, wins, matches in standings:
            # Each player should have one match recorded
            self.assertEqual(matches, 1)
            # Each match winner should have one win recorded
            if id in (player1, player3):
                self.assertEqual(wins, 1)
            # Each match loser should have zero wins recorded
            elif id in (player2, player4):
                self.assertEqual(wins, 0)
        print "* After a match, players have updated standings."

    def test_report_match_with_tie(self):
        """Test reporting a match tie."""
        tournament_id = tournament.register_tournament(
            "Test Matches With Tie Tournament", 2)
        player_names = ("Bruno Walton", "Boots O'Neal")
        for player_name in player_names:
            tournament.register_player_in_tournament(
                tournament.register_player(player_name), tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        player1, player2 = [row[0] for row in standings]
        tournament.report_match(player1, player2, tournament_id, tie=True)

        standings = tournament.player_standings()
        for id, name, wins, matches in standings:
            # Each player should have one match recorded
            self.assertEqual(matches, 1)
            # Each match winner should have one win recorded
            self.assertEqual(wins, 1)
        print "* After a match tie, tied players both have wins."

    def test_rank_by_opponent_match_wins(self):
        """Test ranking standings by opponent match wins."""
        tournament_id = tournament.register_tournament(
            "Test OMW Tournament", 4)
        player_names = (
            "Bruno Walton", "Boots O'Neal", "Cathy Burton", "Diane Grant")
        for player_name in player_names:
            tournament.register_player_in_tournament(
                tournament.register_player(player_name), tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        player1, player2, player3, player4 = [row[0] for row in standings]
        tournament.report_match(player1, player2, tournament_id)
        tournament.report_match(player3, player4, tournament_id)
        # Give player a bye to force re-ordering by omw
        tournament.report_match_bye(player1, tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        omw_standings = tournament.rank_by_opponent_match_wins(
            standings, tournament_id)
        # Standings should be re-ordered (Boots and Diane); Boots lost to
        # Bruno, who has more wins than Cathy (who Diane lost to)
        self.assertEqual(
            omw_standings,
            [(1, 'Bruno Walton', 2, 2), (3, 'Cathy Burton', 1, 1),
             (2, "Boots O'Neal", 0, 1), (4, 'Diane Grant', 0, 1)])
        print "* Matches are ranked by opponent match wins."

    def test_pairings(self):
        """Test pairing players."""
        tournament_id = tournament.register_tournament(
            "Test Pairings Tournament", 4)
        player_names = (
            "Twilight Sparkle", "Fluttershy", "Applejack", "Pinkie Pie")
        for player_name in player_names:
            tournament.register_player_in_tournament(
                tournament.register_player(player_name), tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        player1, player2, player3, player4 = [row[0] for row in standings]
        tournament.report_match(player1, player2, tournament_id)
        tournament.report_match(player3, player4, tournament_id)
        pairings = tournament.swiss_pairings(tournament_id)

        # For four players, swiss_pairings should return two pairs
        self.assertEqual(len(pairings), 2)
        # After one match, players with one win should be paired
        [(id1, name1, id2, name2), (id3, name3, id4, name4)] = pairings
        correct_pairs = set([
            frozenset([player1, player3]), frozenset([player2, player4])])
        actual_pairs = set([frozenset([id1, id2]), frozenset([id3, id4])])
        self.assertEqual(actual_pairs, correct_pairs)
        print "* After one match, players with one win are paired."

    def test_pairings_with_bye(self):
        """Test pairing players with an odd number of players."""
        tournament_id = tournament.register_tournament(
            "Test Pairings With Bye Tournament", 5)
        player_names = (
            "Twilight Sparkle", "Fluttershy", "Applejack",
            "Pinkie Pie", "Brandy Ruby")
        for player_name in player_names:
            tournament.register_player_in_tournament(
                tournament.register_player(player_name), tournament_id)

        standings = tournament.player_standings_by_tournament(tournament_id)
        player1, player2, player3, player4, player5 = [
            row[0] for row in standings]
        tournament.report_match(player1, player2, tournament_id)
        tournament.report_match(player3, player4, tournament_id)
        # Report a match bye for player 5 to test
        tournament.report_match_bye(player5, tournament_id)

        pairings = tournament.swiss_pairings(tournament_id)
        [(id1, name1, id2, name2), (id3, name3, id4, name4)] = pairings
        correct_pairs = set([
            frozenset([player1, player3]), frozenset([player5, player2])])
        actual_pairs = set([frozenset([id1, id2]), frozenset([id3, id4])])
        self.assertEqual(actual_pairs, correct_pairs)
        # Ensure player5 did not receive another bye
        self.assertIn(player5, (id1, id2, id3, id4))
        print (
            "* After one match where one player was granted a bye, "
            "players with one win are paired.")


if __name__ == '__main__':
    unittest.main()