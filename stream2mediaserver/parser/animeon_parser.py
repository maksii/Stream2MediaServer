import random
import requests
import sqlite3
import time

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("SQLite DB connected")
    except Exception as e:
        print(e)
    return conn

#bad data quality, map duplicates to master records
FUNDUB_ID_MAPPING = {
    1483: 1482, 1488: 1482, 1348: 1229, 1366: 1195, 1373: 1134, 1384: 1175, 1359: 1105,
    1425: 1220, 1432: 1431, 1190: 1398, 1455: 1406, 1349: 1141, 1147: 1142, 1379: 1335,
    1356: 1115, 1347: 1170, 1367: 1414, 1409: 1137, 1444: 1388, 1167: 1388, 1376: 1140,
    1466: 1185, 1382: 1185, 1362: 1163, 1396: 1116, 1371: 1184, 1178: 1100, 1368: 1434,
    1126: 1143, 1166: 1446, 1172: 1179
}

def get_master_fundub_id(fundub_id):
    return FUNDUB_ID_MAPPING.get(fundub_id, fundub_id)

def setup_database(connection):
    cursor = connection.cursor()

    # Create the 'type' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    
    # Create the 'type' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS type (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')

    # Create the 'franchise' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS franchise (
            id INTEGER PRIMARY KEY,
            weight INTEGER
        )
    ''')

    # Create the 'anime' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY,
            titleUa TEXT,
            titleEn TEXT,
            description TEXT,
            releaseDate TEXT,
            episodeTime TEXT,
            moonId TEXT,
            episodesAired INTEGER,
            ashdiId TEXT,
            malId TEXT,
            season INTEGER,
            type_id INTEGER,
            status_id INTEGER,
            franchise_id INTEGER,
            FOREIGN KEY (type_id) REFERENCES type(id),
            FOREIGN KEY (status_id) REFERENCES status(id),
            FOREIGN KEY (franchise_id) REFERENCES franchise(id)
        )
    ''')

    # Create the 'related_anime' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS related_anime (
            anime_id1 INTEGER,
            anime_id2 INTEGER,
            franchise_id INTEGER,
            FOREIGN KEY (anime_id1) REFERENCES anime(id),
            FOREIGN KEY (anime_id2) REFERENCES anime(id),
            FOREIGN KEY (franchise_id) REFERENCES franchise(id),
            PRIMARY KEY (anime_id1, anime_id2)
        )
    ''')

    # Create the 'fundub' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fundub (
            id INTEGER PRIMARY KEY,
            name TEXT,
            telegram TEXT
        )
    ''')

    # Create the 'fundub_synonym' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fundub_synonym (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fundub_id INTEGER,
            synonym TEXT,
            FOREIGN KEY(fundub_id) REFERENCES fundub(id)
        )
    ''')

    # Create the 'anime_fundub' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime_fundub (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER,
            fundub_id INTEGER,
            FOREIGN KEY(anime_id) REFERENCES anime(id),
            FOREIGN KEY(fundub_id) REFERENCES fundub(id)
        )
    ''')

    # Create the 'episode' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS episode (
            id INTEGER PRIMARY KEY,
            episode INTEGER,
            subtitles BOOLEAN,
            player INTEGER,
            anime_id INTEGER,
            videoUrl TEXT,
            FOREIGN KEY(anime_id) REFERENCES anime(id)
        )
    ''')

    # Create the 'fundub_episode' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fundub_episode (
            fundub_id INTEGER,
            episode_id INTEGER,
            FOREIGN KEY(fundub_id) REFERENCES fundub(id),
            FOREIGN KEY(episode_id) REFERENCES episode(id)
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS last_index (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        last_index INTEGER
    );
    ''')
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_anime_ids (
            id INTEGER PRIMARY KEY
        )
    """)
    
    connection.commit()
    
def fetch_api(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    }
    max_retries = 3
    for attempt in range(max_retries):
        time.sleep(random.uniform(0.1, 0.3))  # Sleep randomly
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    return None

def safe_get(d, keys, default=None):
    for key in keys:
        if d is not None and key in d:
            d = d[key]
        else:
            return default
    return d

def insert_unique_synonym(cursor, fundub_id, synonym):
    # Check if the synonym already exists for the fundub
    cursor.execute("SELECT 1 FROM fundub_synonym WHERE fundub_id = ? AND synonym = ?", (fundub_id, synonym))
    if not cursor.fetchone():
        # If it does not exist, insert it
        cursor.execute("INSERT INTO fundub_synonym (fundub_id, synonym) VALUES (?, ?)", (fundub_id, synonym))

def insert_if_not_exists(cursor, table, column, value):
    cursor.execute(f"SELECT id FROM {table} WHERE {column} = ?", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
        return cursor.lastrowid

def insert_or_update(cursor, table, unique_column, data, update_columns):
    cursor.execute(f"SELECT id FROM {table} WHERE {unique_column} = ?", (data[unique_column],))
    result = cursor.fetchone()
    if result:
        id = result[0]
        # Generate update statement only for fields that are in update_columns and are provided in data
        updates = ", ".join(f"{col} = ?" for col in update_columns if col in data)
        if updates:
            cursor.execute(f"UPDATE {table} SET {updates} WHERE id = ?", (*[data[col] for col in update_columns if col in data], id))
        return id
    else:
        # Prepare columns and placeholders for insertion
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' for _ in data)
        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(data.values()))
        return cursor.lastrowid

def insert_anime_into_db(data, conn):
    cursor = conn.cursor()
    type_id = insert_or_update(cursor, 'type', 'name', {'name': data['type']['name']}, [])
    status_id = insert_or_update(cursor, 'status', 'name', {'name': data['status']['name']}, [])

    anime_data = {
        'id': data['id'], 'titleUa': data['titleUa'], 'titleEn': data['titleEn'], 'description': data['description'],
        'releaseDate': data['releaseDate'], 'episodeTime': data['episodeTime'], 'moonId': data['moonId'],
        'episodesAired': data['episodesAired'], 'ashdiId': data['ashdiId'], 'malId': data['malId'],
        'season': data['season'], 'type_id': type_id, 'franchise_id': data['franchise']['id'], 'status_id': status_id
    }
    anime_update_columns = ['titleUa', 'titleEn', 'description', 'releaseDate', 'episodeTime', 'episodesAired', 'season', 'type_id', 'status_id']
    insert_or_update(cursor, 'anime', 'id', anime_data, anime_update_columns)

    for fundub in data.get('fundubs', []):
        fundub_id = insert_or_update(cursor, 'fundub', 'name', {'name': fundub['name']}, ['telegram'])
        cursor.execute("INSERT OR IGNORE INTO anime_fundub (anime_id, fundub_id) VALUES (?, ?)", (data['id'], fundub_id))
        #Insert fundub synonyms if they exist
        if fundub.get('synonyms'):
            for synonym in fundub['synonyms']:
                insert_unique_synonym(cursor, fundub_id, synonym)

    cursor.connection.commit()

def insert_franchise_data(data, conn):
    cursor = conn.cursor()
    anime_ids = []
    for franchise in data:
        franchise_id = insert_or_update(cursor, 'franchise', 'id', {'id': franchise['id'], 'weight': franchise['weight']}, ['weight'])
        anime_data = {
            'id': franchise['animes']['id'],
            'titleUa': franchise['animes']['titleUa'],
            'releaseDate': franchise['animes']['releaseDate'],
            'type_id': insert_or_update(cursor, 'type', 'name', {'name': franchise['animes']['type']['name']}, []),
            'franchise_id': franchise_id
        }
        anime_update_columns = ['titleUa', 'releaseDate', 'type_id']
        insert_or_update(cursor, 'anime', 'id', anime_data, anime_update_columns)
        anime_ids.append(franchise['animes']['id'])

    for i in range(len(anime_ids)):
        for j in range(i + 1, len(anime_ids)):
            cursor.execute("INSERT OR IGNORE INTO related_anime (anime_id1, anime_id2, franchise_id) VALUES (?, ?, ?)", (anime_ids[i], anime_ids[j], franchise_id))
            cursor.execute("INSERT OR IGNORE INTO related_anime (anime_id1, anime_id2, franchise_id) VALUES (?, ?, ?)", (anime_ids[j], anime_ids[i], franchise_id))

    cursor.connection.commit()

def insert_fundub_and_episodes(anime_id, fundub_data, episode, video_url, conn):
    cursor = conn.cursor()
    player_id = fundub_data['player'][0]['id']
    fundub = fundub_data['fundub']

    # Get master fundub_id
    master_fundub_id = get_master_fundub_id(fundub['id'])

    # Insert or update fundub
    fundub_columns = {
        'id': master_fundub_id,
        'name': fundub['name'],
        'telegram': fundub.get('telegram', None)
    }
    insert_or_update(cursor, 'fundub', 'id', fundub_columns, ['name', 'telegram'])

    #Insert fundub synonyms if they exist
    if fundub.get('synonyms'):
        for synonym in fundub['synonyms']:
            insert_unique_synonym(cursor, master_fundub_id, synonym)

    # If the original fundub ID does not match the master fundub ID, add the original name as a synonym
    if fundub['id'] != master_fundub_id:
        insert_unique_synonym(cursor, master_fundub_id, fundub['name'])

    # Insert or update episode
    episode_data = {
        'id': episode['id'],
        'episode': episode['episode'],
        'subtitles': episode['subtitles'],
        'videoUrl': video_url['videoUrl'],
        'player': player_id,
        'anime_id': anime_id
    }
    insert_or_update(cursor, 'episode', 'id', episode_data, ['episode', 'subtitles', 'videoUrl', 'player', 'anime_id'])

    # Link fundub with episode
    cursor.execute("INSERT OR IGNORE INTO fundub_episode (fundub_id, episode_id) VALUES (?, ?)", (master_fundub_id, episode['id']))

    # Commit changes
    cursor.connection.commit()

def insert_or_update_index(conn, index):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO last_index (id, last_index) 
        VALUES (1, ?)
    ''', (index,))
    conn.commit()

def get_last_index(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT last_index FROM last_index WHERE id = 1')
    result = cursor.fetchone()
    return result[0] if result else 0

def initiate_scrap(conn):
    last_index = get_last_index(conn)
    index = last_index + 1  # Start from the next index after the last processed one
    while True:
        retry_count = 0
        while retry_count < 5: # changed to 400 from 5, as there a skip for 100+ id's
            anime_data = fetch_api(f'https://animeon.club/api/anime/{index}')
            if anime_data is not None:
                break
            retry_count += 1
            index += 1  # Move to the next index if data is None

        if retry_count == 5 and anime_data is None:
            print("No data found after 5 attempts. Stopping.")
            break
        
        add_new_anime(anime_data, conn)           
                                
        insert_or_update_index(conn, index)  # Update the last processed index in the database
        index += 1

def add_new_anime(anime_data, conn):
        insert_anime_into_db(anime_data, conn)
        
        if anime_data['franchise'] is not None:
            franchise_data = fetch_api(f"https://animeon.club/api/franchise/{anime_data['franchise']['id']}")
            if franchise_data:
                insert_franchise_data(franchise_data, conn)
            
        print(f"Processing and saving anime: {anime_data['titleEn']} (ID: {anime_data['id']})")
        for fundub in anime_data['fundubs']:
            fundub_data = fetch_api(f'https://animeon.club/api/anime/player/fundubs/{fundub["id"]}')
            if fundub_data:
                for fd in fundub_data:
                    for player in fd['player']:
                        episodes = fetch_api(f'https://animeon.club/api/anime/player/episodes/{player['id']}/{fd['fundub']['id']}')
                        for episode in episodes:
                            video_url = fetch_api(f'https://animeon.club/api/anime/player/episode/{episode["id"]}')
                            
                            if video_url is None:
                                video_url = "Blocked"
                            insert_fundub_and_episodes(anime_data['id'], fd, episode, video_url, conn)
        

def populate_new_anime_ids(anime_list, conn):
    cursor = conn.cursor()
    for anime in anime_list:
        cursor.execute("SELECT id FROM anime WHERE id = ?", (anime['id'],))
        if not cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO new_anime_ids (id) VALUES (?)", (anime['id'],))
    conn.commit()

def process_new_anime_ids(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM new_anime_ids")
    ids = cursor.fetchall()
    
    for id_tuple in ids:
        anime_id = id_tuple[0]
        anime_data = fetch_api(f'https://animeon.club/api/anime/{anime_id}')
        add_new_anime(anime_data, conn)

def clear_processed_ids(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM new_anime_ids")
    conn.commit()

def check_new_animes(conn):
    anime_data = fetch_api("https://animeon.club/api/anime")
    populate_new_anime_ids(anime_data['results'], conn)

def delta(conn):
    check_new_animes(conn)
    process_new_anime_ids(conn)
    clear_processed_ids(conn)
