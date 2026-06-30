from sqlalchemy.ext.asyncio import create_async_engine , AsyncSession 
from sqlalchemy.orm import declarative_base , sessionmaker 
import os 
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL , 
    echo=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine , 
    class_=AsyncSession , 
    expire_on_commit=True
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session