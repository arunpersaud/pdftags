from sqlalchemy import Integer, ForeignKey, String, Column, DateTime, BLOB, Float, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, remote, foreign
from sqlalchemy import create_engine, event

from datetime import datetime
import os

Base = declarative_base()

engine = create_engine('sqlite:///pdf.db')

# many to many relationship between pdfs and tags
pdftag_table = Table('pdftag', Base.metadata,
                     Column('pdf_id', Integer, ForeignKey('pdfs.id')),
                     Column('tags_id', Integer, ForeignKey('tags.id')))

# many to many relationship between pdfs and people
pdfpeople_table = Table('pdfpeople', Base.metadata,
                        Column('pdf_id', Integer, ForeignKey('pdfs.id')),
                        Column('people_id', Integer, ForeignKey('people.id')))

class Pdfs(Base):
    """Keep all the information for a single pdf"""
    __tablename__ = 'pdfs'

    # first a list of standard items
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, index=True)  # file creation date
    comment = Column(String)
    path = Column(String)
    md5 = Column(String(32), index=True)

    # we might want to keep several version of a Pdf around, so we
    # keep a linked list here
    other_versions = Column(Integer, ForeignKey('pdfs.id'))

    # what tags are related to this Pdf
    tags = relationship("Tags", secondary=pdftag_table, backref="pdfs")

    # Metadata for this Pdf
    metadata_complete = Column(Boolean)
    authors = relationship("People", secondary=pdfpeople_table, backref="pdfs")
    title = Column(String)
    doi = Column(String)
    journal_id = Column(Integer, ForeignKey('journals.id'))
    journal = relationship("Journals")
    volume = Column(String)
    number = Column(String)
    pages = Column(String)
    year = Column(Integer)

    def __repr__(self):
        return "{}->{} (tags:{})\n".format(self.id, self.path, self.tags)

    def add_tag(self, t):
        self.tags.append(t)

    def remove_tag(self, t):
        if t in self.tags:
            self.tags = [i for i in self.tags if i != t]
        else:
            print("tag '{}' not found for {} with tags: {}".format(
                t.name, self.path, ",".join([i.name for i in self.tags])))

    def bibtex(self):
        author = 'author = "{}",\n'.format("and".join([a.name for a in self.authors]))
        title = 'title = "{}",\n'.format(self.title)
        journal = 'journal = "{}",\n'.format(self.journal.name)
        number = 'number = "{}",\n'.format(self.number)
        pages = 'pages = "{}",\n'.format(self.pages)
        year = 'year = "{}",\n'.format(self.year)
        return '@article{{ xyz, \n' + author + title + number + pages + year +'}}\n'

class Tags(Base):
    """Used a materialized path pattern to generate a tag list.

    We only need to be able to move tags around and to find tags that
    are higher in the hierachy, so we can skip some of the
    functionality that is normally implemented.

    see http://docs.sqlalchemy.org/en/rel_1_0/_modules/examples/materialized_paths/materialized_paths.html

    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    icon = Column(BLOB)
    path = Column(String(500), index=True)

    # To find the descendants of this node, we look for nodes whose path
    # starts with this node's path.
    childs = relationship("Tags", viewonly=True, order_by=path,
                          primaryjoin=remote(foreign(path)).like(path.concat(".%")))

    def __repr__(self):
        return "Tag: {} ({})".format(self.name, self.id)

    def move_to(self, new_parent):
        if new_parent is not None:
            new_path = new_parent.path + "." + str(self.id)
            for n in self.childs:
                n.path = new_path + n.path[len(self.path):]
            self.path = new_path
        else:
            self.path = str(self.id)

    def all_tags(self):
        """This tag and all its childrens"""
        return self.childs+[self]


@event.listens_for(Tags, 'after_insert')
def set_default_path(mapper, connection, target):
    """Add new tags in the root of the tree"""
    if target.path is None:
        t = Tags.__table__
        connection.execute(t.update().where(t.c.id == target.id).
                           values(path=str(target.id)))


class People(Base):
    """List of authors"""
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    institute = Column(String)

    def __repr__(self):
        return "Person: {}->{} {} {}\n".format(self.id, self.name, self.email, self.institute)


class Journals(Base):
    """List of journals"""
    __tablename__ = 'journals'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return "Journal: {}->{}\n".format(self.id, self.name)

# create tables
if not os.path.exists('pdf.db'):
    Base.metadata.create_all(engine)

# create a Session
session = sessionmaker(bind=engine)
