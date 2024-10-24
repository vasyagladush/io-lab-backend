from sqlalchemy.orm import declarative_base

Base = declarative_base()

from models.user import User
from  models.grades import Grades
from  models.surveys import Surveys