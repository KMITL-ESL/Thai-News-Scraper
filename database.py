
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm.session import sessionmaker

from config import config


db_config = config['db']

engine = create_engine(URL(drivername='postgres+psycopg2',
                           username=db_config['username'],
                           password=db_config['password'],
                           host=db_config['host'],
                           port=db_config['port'],
                           database=db_config['database']),
                       echo=db_config['echo'])
Session = sessionmaker(bind=engine)
db: Session = Session()
