from sqlalchemy import inspect
from database import engine

inspector = inspect(engine)
print(inspector.get_table_names())
