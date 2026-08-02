import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def unblock_cards():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    # Supabase uses Postgres, replace postgres:// with postgresql:// if needed
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(db_url)
    with engine.begin() as conn:
        result = conn.execute(text("UPDATE cards SET status = 'Active'"))
        print(f"Unblocked {result.rowcount} cards in Supabase.")

if __name__ == '__main__':
    unblock_cards()
