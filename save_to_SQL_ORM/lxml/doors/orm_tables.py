from sqlalchemy import create_engine, Column, BigInteger, String, Text, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values


config = dotenv_values(".env")
pg_username = config.get("PG_USERNAME")
pg_password = config.get("PG_PASSWORD")
pg_host = config.get("PG_HOST")
pg_port = config.get("PG_PORT")
database = 'citilink'

pg_engine = create_engine(f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{database}", echo=False)
Session = sessionmaker(bind=pg_engine)
session = Session()
Base = declarative_base()


class Categories(Base):
    __tablename__ = "categories"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    parent_id = Column(String(32))


class ItemsInfo(Base):
    __tablename__ = "items_info"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    item_name = Column(String(256), nullable=False)
    item_code = Column(String(16))
    item_url = Column(Text)
    price = Column(Float)
    currency = Column(String(16))
    category_id = Column(BigInteger, nullable=False)


class ItemsPictures(Base):
    __tablename__ = "items_pictures"

    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    item_id = Column(BigInteger, nullable=False)
    picture_url = Column(Text)
    picture_path = Column(String(512))


class ItemsAttributes(Base):
    __tablename__ = "items_attributes"

    id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    attribute_name = Column(String(512), nullable=False)
    attribute_value = Column(String(1024))
    item_id = Column(BigInteger, nullable=False)

Base.metadata.create_all(pg_engine)
