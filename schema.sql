-- Movies table
DROP TABLE if exists movies;
CREATE TABLE movies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  Title TEXT NULL,
  Cover TEXT NULL,
  Country TEXT NULL,
  Loaned TEXT NULL,
  LoanDate TEXT NULL,
  Length TEXT NOT NULL,
  URL TEXT NULL,
  MovieID TEXT NOT NULL,
  MPAA TEXT NULL,
  PersonalRating TEXT NULL,
  PurchaseDate TEXT NULL,
  Seen TEXT NULL,
  Rating TEXT NULL,
  Status TEXT NULL,
  Plot TEXT NULL,
  ReleaseDate TEXT NULL,
  NOTes TEXT NULL,
  Position TEXT NULL,
  Year INTEGER NULL
);

-- Media table
DROP TABLE if exists media;
CREATE TABLE media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Linkmedia table
DROP TABLE if exists linkmedia;
CREATE TABLE linkmedia (
  movie INTEGER NOT NULL,
  media INTEGER NOT NULL
);

-- Genre table
DROP TABLE if exists genre;
CREATE TABLE genre (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Linkgenre table
DROP TABLE if exists linkgenre;
CREATE TABLE linkgenre (
  movie INTEGER NOT NULL,
  genre INTEGER NOT NULL
);

-- Director table
DROP TABLE if exists director;
CREATE TABLE director (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Linkdirector table
DROP TABLE if exists linkdirector;
CREATE TABLE linkdirector (
  movie INTEGER NOT NULL,
  director INTEGER NOT NULL
);

-- Actor table
DROP TABLE if exists actor;
CREATE TABLE actor (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Linkactor table
DROP TABLE if exists linkactor;
CREATE TABLE linkactor (
  movie INTEGER NOT NULL,
  actor INTEGER NOT NULL
);
