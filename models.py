import datetime
import sys
import logging
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import SQLAlchemyError
from db import Base, engine

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="MODELS %(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log"),
    ]
)
logger = logging.getLogger(__name__)

# --- Schema Reset (Dev Only) ---
try:
    logger.warning("Dropping all tables (dev-only action).")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped successfully.")
except SQLAlchemyError as e:
    logger.exception("Failed to drop tables.")
    raise

try:
    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully.")
except SQLAlchemyError as e:
    logger.exception("Failed to create tables.")
    raise

# --- Models ---
class Subscription(Base):
    __tablename__ = 'Subscriptions'
    id = Column(String, primary_key=True)


class Receipt(Base):
    __tablename__ = 'Receipts'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    payment_status = Column(String(50))
    status = Column(String(50))
    amount_total = Column(Integer)
    currency = Column(String(10))
    email = Column(String(120))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Receipt {self.session_id}>"
