import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.tools.auth_tools import get_security_question, verify_customer

def test():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("Testing get_security_question...")
    res = get_security_question(db, "9011", "Fifth November 1988")
    print(res)
    
    print("\nTesting verify_customer...")
    res2 = verify_customer(db, "9011", "Fifth November 1988", "4321", "Mumbai")
    print(res2)

if __name__ == "__main__":
    test()
