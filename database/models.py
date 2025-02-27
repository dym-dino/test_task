# MODELS

# ---------------------------------------------------------------------------------------------------------------------
# IMPORT LIBRARIES


from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine, Engine, inspect
from sqlalchemy.dialects.postgresql import JSONB

from config.variables import database
from database.base_model import BaseModel
from database.data_filler import make_data, make_documents
from database.database_config import DatabaseConfig


# ---------------------------------------------------------------------------------------------------------------------
# MODELS

class Data(BaseModel):
    __tablename__ = 'data'
    __database__: DatabaseConfig = database

    object = Column(String(50), primary_key=True)
    status = Column(Integer)
    level = Column(Integer)
    parent = Column(String)
    owner = Column(String(14))


class Documents(BaseModel):
    __tablename__ = 'documents'
    __database__: DatabaseConfig = database

    doc_id = Column(String, primary_key=True)
    recieved_at = Column(DateTime)
    document_type = Column(String)
    document_data = Column(JSONB)
    processed_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------------------------------------------------
# CREATE AND FILL TABLES

def fill_tables(model, data_tbl, documents_tbl):
    if model.__tablename__ == 'data':
        model.add_all([Data(**i) for i in data_tbl])
    elif model.__tablename__ == 'documents':
        model.add_all([Documents(**i) for i in documents_tbl])


def create_tables():
    data = make_data()
    data_tbl = list(data.values())
    documents_tbl = make_documents(data)

    for model in BaseModel.__subclasses__():
        engine: Engine = create_engine(model.__database__.get_engine_url(), pool_pre_ping=True)
        inspector = inspect(engine)
        table_name = model.__tablename__

        if not inspector.has_table(table_name):
            if input(f'Создать таблицу {table_name}? [Y/N] ').upper() == 'Y':
                model.__table__.create(bind=engine, checkfirst=True)
                print(f'Таблица {table_name} создана!')

                fill_tables(model, data_tbl, documents_tbl)
                print(f'Таблица {table_name} заполнена данными.')

        else:
            if model.count() == 0:
                fill_tables(model, data_tbl, documents_tbl)
                print(f'Таблица {table_name} существует, но была пуста. Теперь она заполнена данными.')


if __name__ == '__main__':
    create_tables()
