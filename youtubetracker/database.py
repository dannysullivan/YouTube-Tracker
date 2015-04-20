from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('postgresql://@localhost/my_database')
Session = sessionmaker(bind=engine)
session = Session()
