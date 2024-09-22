from database import Database

def subscribe_user(email, threshold):
    db = Database()
    db.add_user(email, threshold)
    db.close()

def get_subscribed_users():
    db = Database()
    users = db.get_users()
    db.close()
    return users