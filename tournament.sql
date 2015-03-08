-- Table definitions for the tournament results project.

DROP DATABASE tournament;
CREATE DATABASE tournament;

\connect tournament

CREATE TABLE player (
    id serial PRIMARY KEY,
    name text NOT NULL,
    wins integer NOT NULL DEFAULT 0,
    matches integer NOT NULL DEFAULT 0
);

CREATE TABLE tournament (
    id serial PRIMARY KEY,
    name text NOT NULL,
    players integer NOT NULL
);

CREATE TABLE entrant (
    player_id integer REFERENCES player (id) ON DELETE CASCADE,
    tournament_id integer REFERENCES tournament (id) ON DELETE CASCADE,
    bye boolean NOT NULL DEFAULT FALSE,
    PRIMARY KEY (player_id, tournament_id)
);

CREATE TABLE result (id, name) as
    SELECT * FROM (VALUES (1, 'Win'), (2, 'Loss'), (3, 'Tie'), (4, 'Bye')) R;
    ALTER TABLE result ADD PRIMARY KEY (id);

CREATE TABLE match (
    id serial,
    player_id integer,
    tournament_id integer,
    result_id integer REFERENCES result (id),
    FOREIGN KEY (player_id, tournament_id)
        REFERENCES entrant (player_id, tournament_id) ON DELETE CASCADE,
    PRIMARY KEY (id, player_id)
);