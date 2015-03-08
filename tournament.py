"""Implementation of a Swiss-system tournament."""

import psycopg2

WIN = 1
LOSS = 2
TIE = 3
BYE = 4


def connect():
    """Connect to the PostgreSQL tournament database.
    :returns: tournament database connection
    :rtype: psycopg2.connection
    """
    return psycopg2.connect("dbname=tournament")


def run_query(query, query_args=(), query_type='SELECT'):
    """Run a query against the tournament database.
    The query result will depend on the query type, although the result will
    always be contained in a dict or None. The scope of this project is small
    enough that opening and closing connections per query is acceptable.
    param str query: query string to run
    param tuple query_args: query args to pass to execute
    param query_type: query type to run (SELECT | UPDATE | DELETE | INSERT)
    :returns: query result; result type depends on query type
    :rtype: dict | None
    """
    query_type = query_type.upper()

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, query_args)

            if query_type == 'SELECT':
                result = cursor.fetchall()
            elif query_type == 'INSERT' and 'RETURNING' in query:
                try:
                    # Requires RETURNING be used
                    result, = cursor.fetchone()
                except psycopg2.ProgrammingError:
                    result = None
            elif query_type in ('UPDATE', 'DELETE', 'INSERT'):
                result = cursor.rowcount
            else:
                raise ValueError(
                    "Query type %s is not supported." % query_type)

    return {'result': result}


def delete_all_from_table(table):
    """Delete all rows from a table.
    :param str table: name of the table to delete all rows from
    :returns: count of rows deleted
    :rtype: int
    """
    query = "DELETE FROM %s;" % table
    deleted = run_query(query, query_type='DELETE')
    return deleted['result']


def delete_matches():
    """Delete all the match records from the database.
    :returns: count of rows deleted from match table
    :rtype: int
    """
    return delete_all_from_table('match')


def delete_players():
    """Delete all the player records from the database.
    :returns: count of rows deleted from player table
    :rtype: int
    """
    return delete_all_from_table('player')


def count_players():
    """Count of all players currently registered.
    :returns: count of all registered players
    :rtype: int
    """
    query = "SELECT count(id) FROM player;"
    players = run_query(query)
    return players['result'][0][0]


def register_player(name):
    """Add a player to the tournament database.
    :param str name: name of player to register
    :returns: id of the registered player
    :rtype: int
    """
    query = "INSERT INTO player (name) VALUES (%s) RETURNING id;"
    inserted = run_query(query, query_args=(name,), query_type='INSERT')
    return inserted['result']


def register_tournament(name, players):
    """Add a tournament to the tournament database.
    :param str name: name of tournament to register
    :param int players: number of tournament entrants
    :returns: id of the registered tournament
    :rtype: int
    """
    query = ("INSERT INTO tournament (name, players) "
             "VALUES (%s, %s) "
             "RETURNING id;")
    inserted = run_query(
        query, query_args=(name, players), query_type='INSERT')
    return inserted['result']


def register_player_in_tournament(player, tournament):
    """Register a player in a tournament as an entrant.
    :param int player: id of the player to register
    :param int tournament: id of the tournament to register player in
    :returns: rowcount of the player inserted, 0 | 1
    :rtype: int
    """
    query = ("INSERT INTO entrant (player_id, tournament_id) "
             "VALUES (%s, %s);")
    inserted = run_query(
        query, query_args=(player, tournament), query_type='INSERT')
    return inserted['result']


def player_standings():
    """Get a list of the players and their win records, sorted by wins.
    :returns: list of players and win records
    :rtype: list
    Return format:
        [(15, 'Bruno Walton', 2, 0), (16, "Boots O'Neal", 1, 0), ...]
    """
    query = ("SELECT id, name, wins, matches "
             "FROM player "
             "ORDER BY wins DESC;")
    standings = run_query(query)
    return standings['result']


def player_opponents(player, tournament):
    """Get a list of the played opponents for a player in a tournament.
    :param int player: id of the player to get played opponents for
    :param int tournament: id of the tournament
    :returns: list of opponents that specified player has played
    :rtype: list
    """
    subquery = ("(SELECT id "
                "FROM match "
                "WHERE player_id = %s "
                "AND tournament_id = %s)")
    query = ("SELECT player_id "
             "FROM match "
             "WHERE id IN (%s) "
             "AND player_id != %s;") % (subquery, '%s')
    opponents = run_query(
        query, query_args=(player, tournament, player))
    return [result[0] for result in opponents['result']]


def player_opponents_match_wins(player, tournament):
    """Get a sum of the played opponents match wins.
    :param int player: id of the player
    :param int tournament: id of the tournament
    :returns: sum of opponent wins for a specified player
    :rtype: int
    """
    opponents = player_opponents(player, tournament)

    opponents_count = len(opponents)
    if opponents_count == 0:
        return 0
    elif opponents_count == 1:
        placeholder = "%s"
    else:
        placeholder = ("%s, " * opponents_count)[:-2]

    query = ("SELECT sum(wins) "
             "FROM player "
             "WHERE id IN (%s);") % placeholder
    opponents_match_wins = run_query(
        query, query_args=([o for o in opponents]))

    return opponents_match_wins['result'][0][0]


def player_standings_by_tournament(tournament):
    """Get a list of the players and their win records by tournament.
    :param int tournament: id of tournament to get standings for
    :returns: list of players and win records
    :rtype: list
    Return format:
        [(15, 'Bruno Walton', 2, 0), (16, "Boots O'Neal", 1, 0), ...]
    """
    query = ("SELECT id, name, wins, matches "
             "FROM player p, entrant e "
             "WHERE p.id = e.player_id "
             "AND tournament_id = %s "
             "ORDER BY wins DESC;")
    standings = run_query(query, query_args=(tournament,))
    return standings['result']


def player_has_received_bye(player, tournament):
    """Get whether or not a player has received a bye for a tournament.
    :param int player: id of the player to check
    :param int tournament: id of tournament to check
    :returns: whether a player received a bye in a tournament; True | False
    :rtype: boolean
    """
    query = ("SELECT bye "
             "FROM entrant "
             "WHERE player_id = %s "
             "AND tournament_id = %s;")
    bye = run_query(query, query_args=(player, tournament,))

    return bye['result'][0][0]


def update_match_wins(player):
    """Update match wins in standings for a player.
    :param int player: id of the winning player
    :returns: count of the rows updated; 0 | 1
    :rtype: int
    """
    query = ("UPDATE player "
             "SET wins = wins + 1 "
             "WHERE id = %s;")
    updated = run_query(query, query_args=(player,), query_type='UPDATE')
    return updated['result']


def update_matches_played(players):
    """Update matches played in standings for a player or players.
    :param list players: id of the winning player(s)
    :returns: count of the row(s) updated
    :rtype: int
    """
    players_count = len(players)
    if players_count == 1:
        placeholder = "%s"
    else:
        placeholder = ("%s, " * players_count)[:-2]

    query = ("UPDATE player "
             "SET matches = matches + 1 "
             "WHERE id IN (%s);") % placeholder
    updated = run_query(
        query, query_args=tuple(p for p in players), query_type='UPDATE')

    return updated['result']


def report_match(winner, loser, tournament, tie=False):
    """Report the outcome of a single match between two players.
    Both win-lose and tie matches are reported by report_match. In the event
    of a tie both players are considered winners.
    :param int winner: id of the winner
    :param int loser: id of the loser
    :param int tournament: id of the tournament the match was played in
    :param bool tie: whether match was a tie; True | False
    :returns: id of the reported match
    :rtype: int
    """
    # Add winner or tie
    result_type = TIE if tie else WIN
    query = ("INSERT INTO match "
             "(player_id, tournament_id, result_id) "
             "VALUES (%s, %s, %s) "
             "RETURNING id;")
    inserted = run_query(
        query,
        query_args=(winner, tournament, result_type), query_type='INSERT')

    match_id = inserted['result']

    # Add loser or tie
    result_type = TIE if tie else LOSS
    query = ("INSERT INTO match "
             "(id, player_id, tournament_id, result_id) "
             "VALUES (%s, %s, %s, %s);")
    run_query(
        query,
        query_args=(match_id, loser, tournament, result_type),
        query_type='INSERT')

    # Update matches played and wins
    update_matches_played([winner, loser])
    update_match_wins(winner)

    # Ties count as wins
    if tie:
        update_match_wins(loser)

    return match_id


def report_match_bye(player, tournament):
    """Report a bye for a player in a tournament.
    :param int player: id of the player to report a bye for
    :param int tournament: id of the tournament to report the bye in
    :returns: rowcount of the player updated; 0 | 1
    :rtype: int
    """
    query = ("UPDATE entrant "
             "SET bye = TRUE "
             "WHERE player_id = %s "
             "AND tournament_id = %s;")
    updated = run_query(
        query, query_args=(player, tournament), query_type='UPDATE')

    # Add bye match to match table
    query = ("INSERT INTO match "
             "(player_id, tournament_id, result_id) "
             "VALUES (%s, %s, %s);")
    run_query(
        query, query_args=(player, tournament, BYE), query_type='INSERT')

    # Update matches played and wins
    update_matches_played([player])
    update_match_wins(player)

    return updated['result']


def rank_by_opponent_match_wins(standings, tournament):
    """Rank like players using opponent match wins.
    Players that have equal match wins should be ranked according to the
    strength of the opponents beaten.
    :param list standings: standings for a tournament
    :param int tournament: standings for a tournament
    :returns: standings sorted by opponent match wins
    :rtype: list
    """
    def omw_sort(player1, player2):
        if player1[2] == player2[2]:
            player1_omw = player_opponents_match_wins(player1[0], tournament)
            player2_omw = player_opponents_match_wins(player2[0], tournament)
            if player1_omw > player2_omw:
                return -1
        return 1

    return sorted(standings, cmp=omw_sort)


def swiss_pairings(tournament):
    """Pair players for the next round in a swiss-style tournament.
    Players are paired with an opponent with a equal or nearly-equal win
    record. A player cannot play the same opponent twice.
    :param int tournament: id of the tournament to pair the next round for
    :returns: tuples containing pairings in the format --
        (id1, name1, id2, name2)
    :rtype: list
    """
    standings = player_standings_by_tournament(tournament)
    standings = rank_by_opponent_match_wins(standings, tournament)
    standings = [standing[:2] for standing in standings]

    # Player receives a bye if odd number of players
    if len(standings) % 2 != 0:
        for standing in reversed(standings):
            player, _ = standing
            if not player_has_received_bye(player, tournament):
                report_match_bye(player, tournament)
                standings.pop(standings.index(standing))
                break

    players, opponents = [], []
    while standings:
        # Add the player we are going to find a match for
        player = standings.pop(0)
        players.append(player)

        opponents_played = player_opponents(player[0], tournament)
        # Iterate over the remaining opponents (standings after pop)
        for index, opponent in enumerate(iter(standings)):
            opponent_id, _ = opponent
            # Never play the same opponent twice
            if opponent_id not in opponents_played:
                # Match found; move to next player in standings
                opponents.append(standings.pop(index))
                break

    # Pair players with their respective opponents (determined above)
    pairings = []
    for matchup in zip(players, opponents):
        player, opponent = matchup
        pairings.append(player + opponent)

    return pairings