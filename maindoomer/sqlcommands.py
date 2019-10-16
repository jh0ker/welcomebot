"""Storer of the sql table creation and the query running function."""

import sqlite3


def run_query(query: str, *params: tuple):
    """Run an SQL query with the database."""
    from constants import DATABASENAME
    db_con = sqlite3.connect(DATABASENAME, check_same_thread=False)
    # Use context manager to autocommit
    with db_con:
        cursor = db_con.cursor()
        data = cursor.execute(query, *params).fetchall()
    db_con.close()
    return data


def create_tables():
    """Create the database tables."""
    from constants import DATABASENAME
    db_con = sqlite3.connect(DATABASENAME, check_same_thread=False)
    # Use context manager to autocommit
    with db_con:
        cursor = db_con.cursor()
        # Create all tables
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS "userdata"
            (user_id NUMERIC,
            chat_id NUMERIC,
            firstname TEXT NOT NULL,
            lastname TEXT DEFAULT NULL,
            username TEXT DEFAULT NULL,
            chatname TEXT DEFAULT NULL,
            userlink TEXT DEFAULT NULL,
            chatlink TEXT DEFAULT NULL,
            timespidor NUMERIC DEFAULT 0,
            PRIMARY KEY (user_id, chat_id));
        CREATE TABLE IF NOT EXISTS "cooldowns"
            (user_id NUMERIC,
            chat_id NUMERIC,
            firstname TEXT DEFAULT NULL,
            lastcommandreply TEXT DEFAULT NULL,
            errorgiven NUMERIC DEFAULT 0,
            lasttextreply TEXT DEFAULT NULL,
            PRIMARY KEY (user_id, chat_id));
        CREATE TABLE IF NOT EXISTS "exceptions"
            (user_id NUMERIC,
            chat_id NUMERIC,
            firstname TEXT,
            username TEXT DEFAULT NULL,
            PRIMARY KEY (user_id, chat_id));
        INSERT OR IGNORE INTO "exceptions" (user_id, chat_id, firstname) 
            VALUES 
            (255295801, 1, "doitforricardo"),
            (205762941, 1, "dovaogedot");
        CREATE TABLE IF NOT EXISTS "duels"
            (user_id NUMERIC,
            chat_id NUMERIC,
            firstname TEXT DEFAULT NULL,
            kills NUMERIC DEFAULT 0,
            deaths NUMERIC DEFAULT 0,
            misses NUMERIC DEFAULT 0,
            duelsdone NUMERIC DEFAULT 0,
            accountingday TEXT DEFAULT NULL,
            PRIMARY KEY (user_id, chat_id));
        CREATE TABLE IF NOT EXISTS "chattable"
             (chat_id NUMERIC PRIMARY KEY,
             chat_name TEXT DEFAULT NULL,
             duelstatusonoff NUMERIC DEFAULT 1,
             duelmaximum NUMERIC DEFAULT NULL,
             duelcount NUMERIC DEFAULT 0,
             accountingday TEXT DEFAULT NULL,
             loliNSFW NUMERIC DEFAULT 0,
             lastpidorid NUMERIC DEFAULT NULL,
             lastpidorname TEXT DEFAULT NULL,
             lastpidorday TEXT DEFAULT NULL);
        ''')
    db_con.close()
