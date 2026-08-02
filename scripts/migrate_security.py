import os
import hashlib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()

def migrate():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print("Connecting to database...")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        print("Adding columns to 'customers' table...")
        try:
            conn.execute(text("ALTER TABLE customers ADD COLUMN security_question VARCHAR(255);"))
            print("Added 'security_question' column.")
        except Exception as e:
            print(f"'security_question' column might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE customers ADD COLUMN code_word_hash VARCHAR(256);"))
            print("Added 'code_word_hash' column.")
        except Exception as e:
            print(f"'code_word_hash' column might already exist: {e}")
            
        print("Updating existing customers with default security question and answer...")
        default_question = "What is the name of your first childhood pet?"
        default_answer_hash = hash_pin("Fluffy")
        
        result = conn.execute(
            text("UPDATE customers SET security_question = :q, code_word_hash = :h WHERE security_question IS NULL"),
            {"q": default_question, "h": default_answer_hash}
        )
        print(f"Updated {result.rowcount} customers.")
        
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
