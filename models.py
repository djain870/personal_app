from sqlalchemy import Column, Integer, Float, String, Date
from database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    category = Column(String)
    note = Column(String)
    date = Column(Date)
    user = Column(String) 

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True)
    month = Column(Date)
    account = Column(String)
    type = Column(String)
    balance = Column(Float)
    volatility = Column(String)
    growth = Column(Float)
    user = Column(String)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    file_path = Column(String)
    uploaded_date = Column(Date)
    user = Column(String)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(String)
    bot_reply = Column(String)
    user = Column(String)

from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)


class Wealth(Base):
    __tablename__ = "wealth"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Date)
    account = Column(String)
    type = Column(String)
    balance = Column(Float)
    volatility = Column(String)
    user = Column(String)

class Cashflow(Base):
    __tablename__ = "cashflow"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(Date)
    type1 = Column(String)
    type = Column(String)
    amount = Column(Float)
    flag = Column(String)
    user = Column(String)