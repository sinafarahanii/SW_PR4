from sqlalchemy import Column, Integer, String
from db import Base


class Subscription(Base):
    __tablename__ = 'Subscriptions'
    id = Column(String, primary_key=True)
