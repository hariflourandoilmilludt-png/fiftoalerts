from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Use SQLite for simplicity, can be swapped for Postgres on Railway
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tradingview_alerts.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    timeframe = Column(String)
    active = Column(Boolean, default=True)
    quantman_buy_url = Column(String, nullable=True)
    quantman_sell_url = Column(String, nullable=True)
    quantman_close_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TradeState(Base):
    __tablename__ = "trade_states"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    current_status = Column(String, default="NONE")  # NONE, LONG, SHORT
    last_action_time = Column(DateTime, default=datetime.utcnow)
    last_candle_timestamp = Column(String, nullable=True) # ISO Format or Timestamp from TV
    last_signal_price = Column(String, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
