# CONFIGURATION FILE

# ---------------------------------------------------------------------------
# IMPORT LIBRARIES
import os

from dotenv import load_dotenv

from database.database_config import DatabaseConfig

# ---------------------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES


load_dotenv()

# ---------------------------------------------------------------------------
# CONFIGURATION VARIABLES
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'default_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_PORT = int(os.getenv('DB_PORT', '5432'))

# ---------------------------------------------------------------------------
# DATABASE


DATABASE_INFO = {
    'default': {
        'database': DB_NAME,
        'host': DB_HOST,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'port': DB_PORT
    }
}

database: DatabaseConfig = DatabaseConfig(database_info=DATABASE_INFO)
