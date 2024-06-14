"""This module provides the Database class which encapsulates all the database operations."""

from datetime import datetime

from dateutil.parser import parse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import session, sessionmaker
from uuid import UUID

from src.config import settings
from src.http_client import cmc_client
from src.models import (Asset, AssetAmountPriceHistory, Base, Currency,
                        PriceHistory, User)


class Database:
    """This class encapsulates all the database operations."""

    def __init__(self) -> None:
        """Initialize the Database class with an engine and a session factory."""
        self.engine = create_engine(settings.DATABASE_URL)
        self.session_factory = sessionmaker(self.engine)

    def create_db(self) -> None:
        """Create database tables from models."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> session.Session:
        """
        Get a session object.

        Returns:
            session.Session: SQLAlchemy.orm.session.Session session object
        """
        return self.session_factory()

    async def update_price_histories(self) -> None:
        """Asynchronously update price histories in the database from CoinMarketCap API."""
        self.create_db()
        print('Updating price histories...')
        try:
            with self.get_session() as db_session:
                with db_session.begin():
                    for row in await cmc_client.get_listings():
                        currency = db_session.query(Currency).filter_by(
                            name=row['name']).first()
                        if not currency:
                            currency = Currency(
                                name=row['name'], symbol=row['symbol'])
                            db_session.add(currency)
                            db_session.flush()
                        history = PriceHistory(
                            currency_id=currency.id,
                            price=row['quote']['USD']['price'],
                            timestamp=parse(row['timestamp']),
                        )
                        db_session.add(history)
                    db_session.flush()
                    print('Price histories updated successfully')
        except (SQLAlchemyError, Exception) as error:
            print(f'Error occurred: {error}')

    def get_listings_from_db(self) -> list[dict]:
        """
        Get list of cryptocurrencies from the database.

        Returns:
            list[dict]: List of cryptocurrencies(dict)\
                  (keys: name, symbol, price, sync_timestamp )
        """
        with self.get_session() as db_session:
            currencies = db_session.query(Currency).all()
            crypto_listings = []
            for currency in currencies:
                if currency.price_histories:
                    price = max(currency.price_histories,
                                key=lambda ph: ph.timestamp)
                    crypto_listings.append({'name': currency.name, 'symbol': currency.symbol,
                                            'price': price.price, 'sync_timestamp': price.timestamp})
            return crypto_listings


class UserOperations:
    """This class encapsulates all the user operations."""

    def __init__(self, db: Database):
        """
        Initialize the UserOperations class with a Database object.

        Args:
            db (Database): The database object to be used for user operations.
        """
        self.db = db

    def get_user_by_username_from_db(self, username: str) -> User | None:
        """
        Search for a user in the database by username.

        Args:
            username (str): User.username to search for in the database

        Returns:
            User | None: User object if found else None
        """
        with self.db.get_session() as db_session:
            return db_session.query(User).filter_by(username=username).first()

    def create_user(self, username: str, hashed_password: str) -> User:
        """
        Create a new user in the database by username and hashed password.

        Args:
            username (str): User.username
            hashed_password (str): pass the HASHED password

        Raises:
            Exception: Database error message
            Exception: User already exists

        Returns:
            User: User object
        """
        user = self.get_user_by_username_from_db(username)
        if user:
            raise Exception('User already exists')
        with self.db.get_session() as db_session:
            try:
                with db_session.begin():
                    user = User(username=username,
                                hash_password=hashed_password)
                    db_session.add(user)
                    db_session.flush()
            except SQLAlchemyError as error:
                db_session.rollback()
                raise Exception(f'Database error: {error}')
            return user

    def get_user_assets_info(self, user: User) -> list[dict]:
        """
        Get information about the user's assets.

        Args:
            user (User): object of the User

        Returns:
            list[dict]: A list of dictionaries containing information about the user's assets.\
            keys: currency, amount, current cost, current_price

        Raises:
            Exception: If a database error occurs.
        """
        try:
            with self.db.get_session() as db_session:
                asset_info_list = []
                for asset in db_session.query(Asset).filter_by(user_id=user.id).all():
                    print(asset.amount_price_histories)
                    asset_amount = max(asset.amount_price_histories, key=lambda _: _.timestamp).amount
                    asset_price = max(asset.amount_price_histories, key=lambda _: _.timestamp).price
                    asset_info = {
                        'currency': asset.currency.name,
                        'amount': asset_amount,
                        'current cost': asset_amount * asset_price,
                        'current_price': asset_price,
                    }
                    asset_info_list.append(asset_info)
                return asset_info_list
        except SQLAlchemyError as error:
            raise Exception(f'Database error: {error}')

    def create_user_asset(self, user: User, currency: Currency) -> Asset:
        """
        Create a new asset for a user in the database.

        Args:
            user (User): object of the User
            currency (Currency): object of the Currency

        Returns:
            Asset: object of the Asset created
        """
        asset = AssetOperation(self.db).get_asset_from_db(user, currency)
        if asset:
            return asset
        with self.db.get_session() as db_session:
            with db_session.begin():
                asset = Asset(user_id=user.id, currency_id=currency.id)
                db_session.add(asset)
                db_session.flush()
                asset_id = asset.id
        # Get the asset from the database in the session where it will be used
        with self.db.get_session() as db_session2:
            asset = db_session2.query(Asset).filter_by(id=asset_id).first()
        return asset


class CurrencyOperation:
    """This class encapsulates all the currency operations."""

    def __init__(self, db: Database):
        """
        Initialize the CurrencyOperation class with a Database object.

        Args:
            db (Database): The database object to be used for currency operations.
        """
        self.db = db

    def get_currency_by_name_from_db(self, name: str) -> Currency | None:
        """
        Search for a currency in the database by name.

        Args:
            name (str): name of the currency

        Returns:
            Currency | None: Currency object from db if found else None
        """
        with self.db.get_session() as db_session:
            return db_session.query(Currency).filter_by(name=name).first()

    def get_latest_price_by_currency_from_db(self, currency: Currency) -> PriceHistory | None:
        """
        Get the latest price of the currency from the database.

        Args:
            currency (Currency): Currency object

        Returns:
            PriceHistory | None: PriceHistory object if found else None
        """
        with self.db.get_session() as db_session:
            return (
                db_session.query(PriceHistory)
                .filter_by(currency_id=currency.id)
                .order_by(PriceHistory.timestamp.desc())
                .first()
            )


class AssetOperation:
    """This class encapsulates all the asset operations."""

    def __init__(self, db: Database) -> None:
        """
        Initialize the AssetOperation class with a Database object.

        Args:
            db (Database): The database object to be used for asset operations.
        """
        self.db = db

    def get_asset_from_db(self, user: User, currency: Currency) -> Asset | None:
        """
        Get the asset object from the database.

        Args:
            user (User): User object
            currency (Currency): Currency object

        Returns:
            Asset | None: Asset object if found else None
        """
        with self.db.get_session() as db_session:
            return db_session.query(Asset).filter_by(user_id=user.id, currency_id=currency.id).first()

    def add_asset_amount(self, asset_id: UUID, amount: float) -> AssetAmountPriceHistory:
        """
        Add an amount to the asset.

        Args:
            asset_id (UUID): ID of the asset
            amount (float): amount to add

        Returns:
            AssetAmountPriceHistory: The AssetAmountPriceHistory object that was added.

        Raises:
            ValueError: If no asset is found with the provided ID.
        """
        with self.db.get_session() as db_session:
            with db_session.begin():
                fresh_asset = db_session.query(Asset).filter_by(id=asset_id).first()
                if fresh_asset is None:
                    raise ValueError(f'No asset found with ID {asset_id}')
                price = CurrencyOperation(self.db).get_latest_price_by_currency_from_db(fresh_asset.currency).price
                asset_amount = AssetAmountPriceHistory(
                    asset_id=fresh_asset.id, amount=amount, timestamp=datetime.utcnow(), price=price)
                db_session.add(asset_amount)
                db_session.flush()
                return asset_amount

    def get_last_asset_amount(self, asset: Asset) -> AssetAmountPriceHistory | None:
        """
        Get the last amount of the asset.

        Args:
            asset (Asset): asset object

        Returns:
            AssetAmountPriceHistory | None: AssetAmountPriceHistory object if found else None
        """
        with self.db.get_session() as db_session:
            return (
                db_session.query(AssetAmountPriceHistory)
                .filter_by(asset_id=asset.id)
                .order_by(AssetAmountPriceHistory.timestamp.desc())
                .first()
            )


DB = Database()
user_operations = UserOperations(DB)
currency_operations = CurrencyOperation(DB)
asset_operation = AssetOperation(DB)
