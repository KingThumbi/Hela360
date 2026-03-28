# app/config.py
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hela360")
    SQLALCHEMY_TRACK_MODIFICATIONS = False