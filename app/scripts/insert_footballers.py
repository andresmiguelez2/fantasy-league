import sys
sys.path.insert(0, '/workspace/app')

from aux.constants import FANTASY_MAIN_URL, FOOTBALLER_NAME_DICT, FOOTBALLER_POSITIONS
from classes.footballer import Footballer
from aux.aux_functions import scrape_page
from aux.database import pg_connect, mongo_client
import logging
import pandas as pd
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_all_players(soup):
    results = []
    elements = soup.find_all(attrs={"data-nombre": True})
    for el in elements:
        nombre = FOOTBALLER_NAME_DICT.get(el["data-nombre"], el["data-nombre"])
        
        # Get full_name and displayable_name from anchor tag with class "player-name"
        a_tag = el.find_next("a", class_="player-name")
        full_name = None
        displayable_name = None
        
        if a_tag:
            # Full name from span with class "d-none d-md-inline"
            full_name_span = a_tag.find("span", class_="d-none d-md-inline")
            if full_name_span:
                full_name = full_name_span.get_text(strip=True)
            
            # Displayable name from span with class "d-inline d-md-none"
            displayable_name_span = a_tag.find("span", class_="d-inline d-md-none")
            if displayable_name_span:
                displayable_name = displayable_name_span.get_text(strip=True)
        
        results.append((nombre, full_name, displayable_name))
    
    logger.info(f"Found {len(results)} player entries.")
    return results


def normalise_name(name):
    return_name = name[:]
    if 'alvarez' in return_name:
        return_name = return_name.replace('alvarez', 'lvarez')
    if 'toni ' in return_name:
        return_name = return_name.replace('toni ', 'antonio ')
    if return_name == 'yeray lvarez':
        return_name = 'yeray alvarez'
        
    return return_name


if __name__ == "__main__":
    # Crear conexión a bases de datos
    client = mongo_client()
    db = client["FantasyMDB"]

    conn = pg_connect()
    cursor = conn.cursor()

    # posibles ligas
    cursor.execute("SELECT DISTINCT id FROM league")
    league_ids = [row[0] for row in cursor.fetchall()]

    # futbolistas ya incluidos
    cursor.execute("SELECT DISTINCT full_name FROM footballer_data")
    existing_footballers = {row[0] for row in cursor.fetchall()}

    # Insertar futbolistas
    soup = scrape_page(FANTASY_MAIN_URL, None)
    player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    for _, row in tqdm(player_data_df.iterrows()):
        try:
            if row['full_name'] in existing_footballers:
                continue

            footballer = Footballer(obtain_data=True, name=row['name'], full_name=row['full_name'])
            footballer.name = row['displayable_name'] if row['displayable_name'] else row['name']

            if footballer.data['market_details']:
                for league_id in league_ids:
                    cursor.execute(
                        """
                        INSERT INTO footballer (url_name, league_id)
                        VALUES (%s, %s)
                        RETURNING id
                        """,
                        (footballer.url_name, league_id)
                    )
                
                footballer.id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO footballer_data (id, name, full_name, team, value, total_points, average_points, position, availability)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (footballer.id, footballer.name, footballer.full_name, footballer.team, footballer.data['market_details'][-1]['value'], footballer.data['total_points'], footballer.data['average_points'], FOOTBALLER_POSITIONS[footballer.data['position']], footballer.data['availability'])
                )

                document = dict()
                document['id'] = footballer.id
                document['market_details'] = footballer.data['market_details']
                document['fixture_breakdown'] = footballer.data['fixture_breakdown']
                document['image_binary'] = footballer.data['image_binary']

                conn.commit()
                db.footballer.insert_one(document)

        except Exception as e:
            print(f"Error processing {row['name']}: {e}")


    # Cerrar conexión
    cursor.close()
    conn.close()