### Server app ###
LOOP_TIME_SECONDS = 30 # Bucle de scan
LOOP_TIME_BUFFER = 2
N_REQUEST_BUFFER = 2 # número de peticiones API a saltar
SLEEP_TIME = 0.001 # Sleep time in seconds
UPDATE_DB_INTERVAL = 1800  # in seconds (30 minutes)
HANDLE_DANGLING_FIXTURES_INTERVAL = 50 # dangling features will be handled every number of iterations
UPDATE_FIXTURES_INTERVAL = 200 # dangling features will be handled every number of iterations


### Client app ###
BANK_NAME = "LaLiga"


### Scraper ###
FANTASY_MAIN_URL = "https://www.futbolfantasy.com/analytics/laliga-fantasy/puntos"
FANTASY_PLAYER_URL = "https://www.futbolfantasy.com/jugadores/"
FANTASY_PLAYER_MARKET_URL = "https://www.futbolfantasy.com/analytics/laliga-fantasy/mercado/detalle/"
FANTASY_FIXTURE_URL = "https://www.futbolfantasy.com/laliga/posibles-alineaciones/"
FOOTBALLER_NAME_DICT = {
    'toni martinez': 'antonio martinez',
    'alex baena': 'lex baena',
    'julian alvarez': 'julian lvarez',
    'joseda alvarez': 'joseda lvarez',
    'angel ortiz': 'ngel ortiz',
    'chimy avila': 'ezequiel avila',
    'oscar mingueza': 'scar mingueza',
    'alex sancris': 'lex sancris',
    'mihailo ristic': 'mihailo risti',
    'oscar ureña': 'scar urena',
    'ionut radu': 'andrei radu',
    'angel fortuño': 'ngel fortuno',
    'miguel angel rubio': 'miguel ngel rubio',
    'ramon terrats': 'terrats',
    'luca koleosho': 'luca warrick',
    'alex sancris': 'lex sancris',
    'mathew ryan': 'mat ryan',
    'samu costa': 'samu almeida',
    'oscar valentin': 'scar valentin',
    'andrei ratiu': 'andrei florin',
    'alemao': 'alemo',
    'eder militao': 'der milito',
    'arda guler': 'arda gler',
    'manuel angel': 'manuel ngel',
    'alvaro f. carreras': 'lvaro fernandez 1',
    'orri steinn oskarsson': 'orri steinn skarsson',
    'tanguy nianzou': 'tanguy kouassi',
    'Örjan nyland': 'rjan nyland',
    'jose angel carmona': 'jose ngel carmona',
    'eray comert': 'eray cmert',
    'josan ferrandez': 'josan',
    'john chetauya': 'john nwankwo',
    'alvaro nuñez': 'lvaro nunez',
    'eric bailly': 'eric bertrand bailly',
    'hugo alvarez ': 'hugo lvarez ',
    'carlos alvarez': 'carlos lvarez',
    'karl etta eyong': 'etta-eyong',
    'alvaro fidalgo': 'lvaro fidalgo',
    'justin kalumba': 'jastin-kalumba',
    'zito luvumbo': 'zito-luvumbo-1',
    "etienne eto'o": "etienne-etoo",
    'fran gonzalez': 'fran-gonzalez-2',
}
COMPETITION_NAME = 'LaLiga 2025/26'
FOOTBALLER_POSITIONS = {
    'def': 'DF',
    'med': 'MD',
    'del': 'FW',
    'por': 'GK',
}

# Game
LINEUP_POSITIONS = ['GK', 'DF', 'MD', 'FW']
POSITION_ORDER = {'GK': 0, 'DF': 1, 'MD': 2, 'FW': 3}
DANGLING_FIXTURE_THRESHOLD = 5 # days without updates to consider a fixture dangling
CLOSING_TIME_FIXTURE = 60*4 # minutes to close fixture after it finishes
COINS_PER_POINT = 100_000 # money awarded per point scored


### Market ####
N_NEW_FOOTBALLERS_INTO_MARKET = 15 # number of new players to be added into new market
RELEASE_CLAUSE_DAYS = 14 # number of days until a footballer can be released again after being bought
