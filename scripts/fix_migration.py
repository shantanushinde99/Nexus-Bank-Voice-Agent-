import os
import hashlib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()

INDIAN_CUSTOMERS = [
    {"name": "Aarav Sharma", "phone": "+919876543210", "dob": "1999-08-14", "pin": "1234", "question": "What is the name of your first childhood pet?", "answer": "Fluffy"},
    {"name": "Priya Patel", "phone": "+919876543211", "dob": "1995-03-22", "pin": "5678", "question": "What is your mother's maiden name?", "answer": "Desai"},
    {"name": "Rajesh Kumar", "phone": "+919876543212", "dob": "1988-11-05", "pin": "4321", "question": "In what city were you born?", "answer": "Mumbai"},
    {"name": "Ananya Iyer", "phone": "+919876543213", "dob": "2001-01-30", "pin": "8765", "question": "What is your favorite color?", "answer": "Blue"},
    {"name": "Vikram Singh", "phone": "+919876543214", "dob": "1992-07-19", "pin": "9999", "question": "What was the name of your elementary school?", "answer": "St. Xavier"},
    {"name": "Deepika Rao", "phone": "+919876543215", "dob": "1997-12-10", "pin": "1111", "question": "What was your favorite food as a child?", "answer": "Biryani"},
    {"name": "Rohan Gupta", "phone": "+919876543216", "dob": "1990-05-25", "pin": "2222", "question": "What is the name of your favorite uncle?", "answer": "Anil"},
    {"name": "Kavya Reddy", "phone": "+919876543217", "dob": "1998-09-08", "pin": "3333", "question": "What is your paternal grandmother's first name?", "answer": "Lakshmi"},
    {"name": "Aditya Joshi", "phone": "+919876543218", "dob": "1985-04-12", "pin": "4444", "question": "What was your childhood nickname?", "answer": "Chintu"},
    {"name": "Meera Nair", "phone": "+919876543219", "dob": "1996-06-17", "pin": "5555", "question": "What street did you live on in third grade?", "answer": "MG Road"},
]

def fix_migration():
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print("Connecting to database...")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        for cust in INDIAN_CUSTOMERS:
            phone = cust["phone"]
            question = cust["question"]
            # Ensure we hash the lowercased answer as expected by auth_tools
            answer_hash = hash_pin(cust["answer"].lower())
            
            conn.execute(
                text("UPDATE customers SET security_question = :q, code_word_hash = :h WHERE phone_number = :p"),
                {"q": question, "h": answer_hash, "p": phone}
            )
            print(f"Updated {cust['name']} with their unique question and answer.")
        
    print("Fix migration completed successfully!")

if __name__ == "__main__":
    fix_migration()
