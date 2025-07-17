import datetime
from sqlalchemy import Column, Integer, String, DateTime
from db import Base, engine

# 🛑 Dev-only schema reset (comment out after use!)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


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
