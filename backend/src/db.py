from src.models import Base, Currency, PriceHistory, User, Asset, AssetAmountPriceHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
from dateutil.parser import parse
from src.config import settings
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from src.http_client import cmc_client



class Database:
    def __init__(self) -> None:
        self.engine = create_engine(settings.DATABASE_URL)
        self.session_factory = sessionmaker(self.engine)

    def create_db(self) -> None:
        """Create database tables from models"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> session.Session:
        """ Get a session object

        Returns:
            Session: SQLAlchemy.orm.session.Session session object
        """
        return self.session_factory()


    async def update_price_histories(self) -> None:
        """ASYNC Update price histories in the database from CoinMarketCap API"""
        self.create_db()
        #NOTE print for debugging
        print('Updating price histories...')
        try:
            with self.get_session() as session:
                with session.begin():
                    for row in await cmc_client.get_listings():
                        currency = session.query(Currency).filter_by(
                            name=row['name']).first()
                        if not currency:
                            print(f'{row["name"]=} {f'{row["symbol"]=}: {row["quote"]["USD"]["price"]=} {row['timestamp']=}' }')
                            currency = Currency(
                                name=row['name'], symbol=row['symbol'])
                            session.add(currency)
                            session.flush()
                        history = PriceHistory(
                            currency_id=currency.id, price=row['quote']['USD']['price'], timestamp=parse(row['timestamp']))
                        session.add(history)
        except (SQLAlchemyError, Exception) as e:
            print(f"Error occurred: {e}")

    def get_listings_from_db(self) -> list[dict]:
        """ Get list of cryptocurrencies from the database

        Returns:
            list[dict]: List of cryptocurrencies(dict)\
                  (keys: name, symbol, price, sync_timestamp )
        """
        with self.get_session() as session:
            currencies = session.query(Currency).all()
            result = []
            for currency in currencies:
                if currency.price_histories:
                    price = max(currency.price_histories,
                                key=lambda ph: ph.timestamp)
                    result.append({'name': currency.name, 'symbol': currency.symbol,
                                   'price': price.price, 'sync_timestamp': price.timestamp})
            return result


class UserOperations:
    def __init__(self, db: Database):
        self.db = db

    def get_user_by_username_from_db(self, username: str) -> User | None:
        """Search for a user in the database by username

        Args:
            username (str): User.username to search for in the database

        Returns:
            User | None: User object if found else None
        """
        with self.db.get_session() as session:
            return session.query(User).filter_by(username=username).first()

    def create_user(self, username: str, hashed_password: str) -> User:
        """ Create a new user in the database by username and password

        Args:
            username (str): User.username
            password (str): pass the HASHED password

        Raises:
            Exception: Database error message
            Exception: User already exists

        Returns:
            User: User object
        """
        user = self.get_user_by_username_from_db(username)
        if user:
            raise Exception('User already exists')
        with self.db.get_session() as session:
            try:
                with session.begin():
                    user = User(username=username,
                                hash_password=hashed_password)
                    session.add(user)
                    session.flush()
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception('Database error: ' + str(e))
            return user

    def get_user_assets_info(self, user: User) -> list[dict]:
        """
        Get information about the user's assets

        Args:
            user (User): object of the User

        Returns:
            list[dict]: A list of dictionaries containing information about the user's assets.\
            keys: currency, amount, current cost, current_price

        Raises:
            Exception: If a database error occurs.
        """
        
        try:
            with self.db.get_session() as session:
                result = []
                for asset in session.query(Asset).filter_by(user_id=user.id).all():
                    asset_amount = max(asset.amount_price_histories, key=lambda _:_.timestamp).amount
                    asset_price = max(asset.amount_price_histories, key=lambda _:_.timestamp).price
                    asset_info = {
                        'currency': asset.currency.name,
                        'amount': asset_amount,
                        'current cost': asset_amount * asset_price,
                        'current_price': asset_price
                    }
                    result.append(asset_info)
                return result
        except SQLAlchemyError as e:
            raise Exception('Database error: ' + str(e))
    
    def create_user_asset(self, user: User, currency: Currency) -> Asset:
        """ Create a new asset for a user in the database

        Args:
            user (User): object of the User
            currency (Currency): object of the Currency

        Raises:
            Exception: If asset already exists

        Returns:
            Asset: object of the Asset created
        """
        asset = AssetOperation(self.db).get_asset_from_db(user, currency)
        if asset:
            return asset
        with self.db.get_session() as session:
            with session.begin():
                asset = Asset(user_id=user.id, currency_id=currency.id)
                session.add(asset)
                session.flush()
                return asset
    

class CurrencyOperation:
    def __init__(self, db: Database):
        self.db = db
    
    def get_currency_by_name_from_db(self, name: str) -> Currency | None:
        """Search for a currency in the database by name

        Args:
            name (str): name of the currency

        Returns:
            Currency | None: Currency object from db if found else None
        """
        with self.db.get_session() as session:
            return session.query(Currency).filter_by(name=name).first()
    
    def get_latest_price_by_currency_from_db(self, currency: Currency) -> PriceHistory | None:
        """Get the latest price of the currency from the database

        Args:
            currency (Currency): Currency object

        Returns:
            PriceHistory | None: PriceHistory object if found else None
        """
        with self.db.get_session() as session:
            return session.query(PriceHistory).filter_by(currency_id=currency.id).order_by(PriceHistory.timestamp.desc()).first()

    

class AssetOperation:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    def get_asset_from_db(self, user: User, currency: Currency) -> Asset | None:
        """Get the asset object from the database

        Args:
            user (User): User object
            currency (Currency): Currency object

        Returns:
            Asset | None: Asset object if found else None
        """
        with self.db.get_session() as session:
            return session.query(Asset).filter_by(user_id=user.id, currency_id=currency.id).first()
    
    def add_asset_amount(self, asset: Asset, amount: float) -> AssetAmountPriceHistory:
        """Add an amount to the asset

        Args:
            asset (Asset): asset object
            amount (float): amount to add
        """
        with self.db.get_session() as session:
            with session.begin():
                # Get a fresh copy of the asset within this session
                asset = session.query(Asset).get(asset.id)
                price = CurrencyOperation(self.db).get_latest_price_by_currency_from_db(asset.currency).price
                asset_amount = AssetAmountPriceHistory(
                    asset_id=asset.id, amount=amount, timestamp=datetime.utcnow(), price=price)
                session.add(asset_amount)
                return asset_amount
            

    def get_last_asset_amount(self, asset: Asset) -> AssetAmountPriceHistory | None:
        """Get the last amount of the asset

        Args:
            asset (Asset): asset object

        Returns:
            AssetAmountPriceHistory | None: AssetAmountPriceHistory object if found else None
        """
        with self.db.get_session() as session:
            return session.query(AssetAmountPriceHistory).filter_by(asset_id=asset.id).order_by(AssetAmountPriceHistory.timestamp.desc()).first()

    




DB = Database()
user_operations = UserOperations(DB)
currency_operations = CurrencyOperation(DB)
asset_operation = AssetOperation(DB)
