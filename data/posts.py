import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Posts(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, nullable=True)
    post_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    views_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    id_group = sqlalchemy.Column(sqlalchemy.Text, nullable=True)


