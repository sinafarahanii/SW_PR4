import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="DB %(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log"),
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Load and validate the database URL
try:
    database_url = os.environ["DATABASE_URL"]
    logger.info("DATABASE_URL loaded successfully.")
except KeyError:
    logger.critical("DATABASE_URL environment variable not set.")
    raise RuntimeError("DATABASE_URL environment variable not set") from None

# Create engine
try:
    engine = create_engine(database_url, future=True)
    logger.info("Database engine created successfully.")
except SQLAlchemyError as e:
    logger.exception("Failed to create database engine.")
    raise

# Configure session
try:
    db_session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    ))
    logger.info("Database session configured successfully.")
except SQLAlchemyError as e:
    logger.exception("Failed to configure database session.")
    raise

# Declare base
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized and tables created successfully.")
    except ImportError as e:
        logger.exception("Failed to import models.")
        raise
    except SQLAlchemyError as e:
        logger.exception("Database initialization failed.")
        raise
