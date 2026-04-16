"""
Database clients for Smart City IoT Dashboard.
"""

from app.db.mongodb_client import MongoDBClient, get_mongodb_client
from app.db.oracle_client import OracleClient, get_oracle_client

__all__ = [
    "MongoDBClient",
    "get_mongodb_client",
    "OracleClient",
    "get_oracle_client",
]
