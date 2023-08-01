from sqlalchemy import create_engine, Column, BigInteger, String, Text,  Float
from sqlalchemy.orm import declarative_base
# from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

Base = declarative_base()


class Categories(Base):
    __tablename__ = "categories"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    parent_id = Column(String(32), nullable=True)


class ItemsInfo(Base):
    __tablename__ = "item_info"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    code = Column(String(64))
    item_url = Column(Text)
    rate = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    category_id = Column(String(32), nullable=False)


class ItemsPictures(Base):
    __tablename__ = "item_pictures"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    item_id = Column(String(32), nullable=False)
    picture_url = Column(Text)
    picture_path = Column(String(512))


class ItemsAttributes(Base):
    __tablename__ = "item_attributes"

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    attribute_name = Column(String(512), nullable=False)
    attribute_value = Column(String(1024))
    item_id = Column(String(32), nullable=False)

if __name__ == '__main__':
    config = dotenv_values(".env")
    pg_username = config.get("PG_USERNAME")
    pg_password = config.get("PG_PASSWORD")
    pg_host = config.get("PG_HOST")
    pg_port = config.get("PG_PORT")
    database = 'citilink'

    pg_engine = create_engine(f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{database}", echo=False)
    # Session = sessionmaker(bind=pg_engine)
    # session = Session()
    Base.metadata.create_all(pg_engine)
