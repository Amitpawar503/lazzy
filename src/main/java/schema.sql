create schema IF NOT EXISTS WIAPI;
use WIAPI;
CREATE TABLE  IF NOT EXISTS  GAME_TRANSACTIONS(
id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
gameround_id INTEGER,
amount double,
bonus_bet double,
end_time DATE,
realbet double,
start_time DATE,
trans_id INTEGER,
trans_type boolean
);