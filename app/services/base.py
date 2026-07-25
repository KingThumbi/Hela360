"""
Base Authentication Service

Provides shared infrastructure for all authentication services.

This class centralizes common database operations and transaction
management while keeping business logic inside concrete services.

Responsibilities
----------------
- SQLAlchemy session access
- Transaction helpers
- UTC timestamp helper
- Object persistence helpers
- Logging

Hela360 Enterprise Pharmacy POS & ERP
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Iterator

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db


class BaseService:
    """
    Base class for authentication services.
    """

    #: SQLAlchemy scoped session
    db = db.session

    #: Service logger
    logger = logging.getLogger("hela360.auth")

    # ------------------------------------------------------------------
    # Time Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def utcnow() -> datetime:
        """
        Return the current UTC timestamp.
        """

        return datetime.now(UTC)

    # ------------------------------------------------------------------
    # Persistence Helpers
    # ------------------------------------------------------------------

    def add(self, instance) -> None:
        """
        Add an object to the current transaction.
        """

        self.db.add(instance)

    def add_all(
        self,
        instances,
    ) -> None:
        """
        Add multiple objects.
        """

        self.db.add_all(instances)

    def delete(
        self,
        instance,
    ) -> None:
        """
        Delete an object.
        """

        self.db.delete(instance)

    def flush(self) -> None:
        """
        Flush pending SQL without committing.
        """

        self.db.flush()

    def refresh(
        self,
        instance,
    ) -> None:
        """
        Refresh an ORM instance.
        """

        self.db.refresh(instance)

    def commit(self) -> None:
        """
        Commit the current transaction.
        """

        self.db.commit()

    def rollback(self) -> None:
        """
        Roll back the current transaction.
        """

        self.db.rollback()

    # ------------------------------------------------------------------
    # Transaction Helper
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """
        Execute operations inside a database transaction.

        Example
        -------
        with self.transaction():
            ...
        """

        try:
            yield
            self.commit()

        except SQLAlchemyError:
            self.rollback()
            self.logger.exception("Database transaction failed.")
            raise

        except Exception:
            self.rollback()
            self.logger.exception("Unexpected transaction failure.")
            raise

    # ------------------------------------------------------------------
    # Convenience Helpers
    # ------------------------------------------------------------------

    def save(
        self,
        instance,
        *,
        commit: bool = True,
    ):
        """
        Persist an object.

        Returns
        -------
        The saved instance.
        """

        self.add(instance)

        if commit:
            self.commit()

        return instance

    def remove(
        self,
        instance,
        *,
        commit: bool = True,
    ) -> None:
        """
        Delete an object.
        """

        self.delete(instance)

        if commit:
            self.commit()


__all__ = [
    "BaseService",
]