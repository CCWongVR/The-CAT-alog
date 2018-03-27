
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Breed(Base):
    __tablename__ = 'breed'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    cat = relationship('Cat', cascade='all, delete-orphan')

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
        }


class Cat(Base):
    __tablename__ = 'cat'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    bio = Column(String(250))
    breed_id = Column(Integer, ForeignKey('breed.id'))
    breed = relationship(Breed)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'bio': self.bio
        }


engine = create_engine('sqlite:///cats.db')
Base.metadata.create_all(engine)
