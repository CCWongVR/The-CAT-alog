from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cat_db_setup import Base, Breed, Cat

engine = create_engine('sqlite:///cats.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

Breed_1 = Breed(name='Thunder Cat')
session.add(Breed_1)
session.commit()

Cat_1 = Cat(name='Lion-O', bio='Leader of the Thunder Cats', breed=Breed_1)
session.add(Cat_1)
session.commit()
