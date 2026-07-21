from sqlalchemy import MetaData 
from sqlalchemy.orm import DeclarativeBase 

"""
%(table_name)s → table name
%(column_0_name)s → first column name
%(column_0_label)s → first column’s full label
%(referred_table_name)s → table referenced by a foreign key
%(constraint_name)s → constraint name you provided
"""


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": (
        "fk_%(table_name)s_"
        "%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
    "pk": "pk_%(table_name)s",
}



class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention=NAMING_CONVENTION
    )