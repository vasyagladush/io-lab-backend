from sqlalchemy.orm import declarative_base

Base = declarative_base()

from models.grades import Grade
from models.surveys import Survey
from models.user import User
