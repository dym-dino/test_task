# BASE MODEL

# ---------------------------------------------------------------------------------------------------------------------
# IMPORT LIBRARIES
import ast
import json
import time
from typing import List, TypeVar, Generic, Type, Optional

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base

from database.database_config import DatabaseConfig
from logger import print_error

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURATION

T = TypeVar('T', bound='BaseModel')
Base = declarative_base()


# ---------------------------------------------------------------------------------------------------------------------
# Helper class for building query chains
class QuerySet(Generic[T]):
    def __init__(self, query, session):
        self.query = query
        self.session = session

    def filter(self, *args, **kwargs) -> "QuerySet[T]":
        self.query = self.query.filter(*args, **kwargs)
        return self

    def order_by(self, *args) -> "QuerySet[T]":
        self.query = self.query.order_by(*args)
        return self

    def all(self) -> List[T]:
        try:
            results = self.query.all()
            for instance in results:
                type(instance)._process_json_columns(instance)
            return results
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return self.all()
        except Exception as e:
            print_error(e)
            return []
        finally:
            self.session.close()

    def first(self) -> Optional[T]:
        try:
            result = self.query.first()
            if result is not None:
                type(result)._process_json_columns(result)
            return result
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return self.first()
        except Exception as e:
            print_error(e)
            return None
        finally:
            self.session.close()


# ---------------------------------------------------------------------------------------------------------------------
# MAIN LOGIC

class BaseModel(Base, Generic[T]):
    """Base model for all database objects with common methods"""
    __database__: DatabaseConfig = None
    __abstract__ = True
    __table_args__ = {'extend_existing': True, 'schema': 'public'}

    @classmethod
    def get_session(cls):
        return cls.__database__.get_session()

    @classmethod
    def get(cls: Type[T], pk: object) -> Optional[T]:
        """Retrieve an instance by primary key"""
        session = cls.get_session()
        try:
            instance: Optional[T] = session.query(cls).get(pk)
            if instance:
                cls._process_json_columns(instance)
            return instance
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return cls.get(pk)
        except Exception as e:
            print_error(e)
        finally:
            session.close()
        return None

    @classmethod
    def all(cls: Type[T]) -> List[T]:
        return cls.query_set().all()

    @classmethod
    def query_set(cls) -> QuerySet[T]:
        session = cls.get_session()
        query = session.query(cls)
        return QuerySet(query, session)

    @classmethod
    def filter(cls: Type[T], *args, **kwargs) -> QuerySet[T]:
        """Returns a query set for filtering, which can then be chained with .order_by(), .all(), or .first()"""
        return cls.query_set().filter(*args, **kwargs)

    @classmethod
    def order_by(cls: Type[T], *args) -> QuerySet[T]:
        """Returns a query set with order_by applied, allowing further calls to .all() or .first()"""
        return cls.query_set().order_by(*args)

    @classmethod
    def first(cls: Type[T], *args, **kwargs) -> Optional[T]:
        """Convenient method to immediately retrieve the first object matching the filter"""
        return cls.filter(*args, **kwargs).first()

    # Other methods remain unchanged
    @classmethod
    def values(cls: Type[T], *columns) -> List[tuple]:
        """Retrieve selected columns from the database"""
        session = cls.get_session()
        try:
            results = session.query(*columns).all()
            processed_results: List[tuple] = []
            for row in results:
                processed_row: List[object] = []
                for column, value in zip(columns, row):
                    if isinstance(column.type, JSON):
                        if isinstance(value, str):
                            try:
                                value = ast.literal_eval(value)
                            except Exception as e:
                                print_error(e)
                        elif value is None:
                            value = {}
                    processed_row.append(value)
                processed_results.append(tuple(processed_row))
            return processed_results
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return cls.values(*columns)
        except Exception as e:
            print_error(e)
        finally:
            session.close()
        return []

    def delete(self) -> None:
        """Delete the current instance from the database"""
        session = self.get_session()
        try:
            session.delete(self)
            session.commit()
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            self.delete()
        except Exception as e:
            print_error(e)
        finally:
            session.close()

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """Create a new instance of the model"""
        instance: T = cls(**kwargs)
        return instance.save()

    @classmethod
    def add_all(cls: Type[T], instances: List[T]) -> List[T]:
        """Add a list of model instances to the database in a single operation"""
        session = cls.get_session()
        try:
            session.add_all(instances)
            session.commit()
            for instance in instances:
                session.refresh(instance)
            return instances
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return cls.add_all(instances)
        except Exception as e:
            print_error(e)
            session.rollback()
            raise
        finally:
            session.close()

    def save(self) -> T:
        """Save the current instance to the database"""
        session = self.get_session()
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return self.save()
        except Exception as e:
            print_error(e)
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def count(cls: Type[T], *args, **kwargs) -> int:
        """Return the count of records matching the filter or the total number of records"""
        session = cls.get_session()
        try:
            query = session.query(cls)
            if args or kwargs:
                query = query.filter(*args, **kwargs)
            return query.count()
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return cls.count(*args, **kwargs)
        except Exception as e:
            print_error(e)
        finally:
            session.close()
        return 0

    @classmethod
    def update_all(cls, filter_condition, update_values: dict) -> int:
        session = cls.get_session()
        try:
            count = session.query(cls).filter(filter_condition).update(
                update_values, synchronize_session=False
            )
            session.commit()
            return count
        except OperationalError as e:
            print_error(e)
            time.sleep(3)
            return cls.update_all(filter_condition, update_values)
        except Exception as e:
            print_error(e)
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def _process_json_columns(cls, instance: T) -> None:
        """Process JSON and JSONB columns for one instance"""
        for column in instance.__table__.columns:
            try:
                if isinstance(column.type, JSON):
                    data = getattr(instance, column.name)
                    if isinstance(data, str):
                        setattr(instance, column.name, ast.literal_eval(data))
                    elif data is None:
                        setattr(instance, column.name, {})
            except Exception as e:
                print_error(e)

    def _convert_dicts_to_json_strings(self) -> None:
        for column in self.__table__.columns:
            if isinstance(column.type, JSON) and isinstance(getattr(self, column.name), dict):
                setattr(self, column.name, json.dumps(getattr(self, column.name)))
