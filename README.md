# Project2_RelationalDatabase_Tournament
Project2 for FullStack NanoDegree

Tournament Results

#About

From Udacity:

In this project, I have written a Python module that uses the PostgreSQL database to keep track of players and matches in a game tournament. The game tournament will use the Swiss system for pairing up players in each round: players are not eliminated, and each player should be paired with another player with the same number of wins, or as close as possible
This project demonstrates familiarity with:

1. Database design and normalization

2. SQL statements (DML and DDL)

3. PostgreSQL and the Python adapter Psycopg2

4. Development of an API backed by a database

5. Use of functional tests to validate results

Tournament Rules:
1. Players compete against other players of similar rank

2. Players cannot play the same opponent more than once

3. Players can recieve byes (free win), but only once per tournament

4. Individual games in a round can result in a tie (win for both players)

5. Players with the same number of wins are ranked by Opponent Match Wins

6. Players can play in multiple tournaments

More on Swiss-style tournament system: http://en.wikipedia.org/wiki/Swiss-system_tournament

Quick Start:

1. Clone vagrant environment: git clone https://github.com/rajputss/Project2_RelationalDatabase_Tournament.git

2. Bring up vagrant VM: vagrant up

3. SSH into vagrant VM: vagrant ssh

4. Install dependencies if needed: sudo apt-get install libpq-dev python-dev

5. Upgrade psycopg2 (>= 2.5): sudo pip install -U psycopg2

6. Clone tournament repo (in VM): git clone https://github.com/rajputss.git

7. Navigate to tournament_results cd Project2_RelationalDatabase_Tournament

8. Run test suite: python tournament/functional_tests/tournament/test_tournament.py

Requirements:

1. Vagrant

2. VirtualBox

3. Python >= 2.7

4. Linux, Mac OS X

5. Grading (by Udacity)
