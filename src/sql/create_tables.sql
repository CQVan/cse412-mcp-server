CREATE TABLE GAME    ( G_GID INTEGER NOT NULL,
                            G_NAME       VARCHAR(100) NOT NULL,
                            G_OSLIST     VARCHAR(10) [],
                            G_LANGUAGES  VARCHAR(25) [],
                            G_LASTPLAYED TIMESTAMP,
                            G_HOURSPLAYED REAL NOT NULL,
                            G_REVIEWSCORE INTEGER);

CREATE TABLE GENRE   ( GN_ID INTEGER NOT NULL,
                            GN_NAME VARCHAR(100) NOT NULL);

CREATE TABLE GENREFOR ( GF_ID INTEGER NOT NULL,
                            GF_GID INTEGER NOT NULL);

CREATE TABLE DLC     ( DLC_ID INTEGER NOT NULL,
                            DLC_NAME VARCHAR(100) NOT NULL,
                            DLC_GID  INTEGER NOT NULL);

CREATE TABLE CREATOR ( C_CID INTEGER NOT NULL,
                            C_NAME VARCHAR(100) NOT NULL);

CREATE TABLE DEVELOPER ( D_CID INTEGER NOT NULL);

CREATE TABLE MADE ( M_CID INTEGER NOT NULL,
                            M_GID INTEGER NOT NULL);

CREATE TABLE PUBLISHER ( P_CID INTEGER NOT NULL);

CREATE TABLE PUBLISHED ( PB_CID INTEGER NOT NULL,
                            PB_GID INTEGER NOT NULL);