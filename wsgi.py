from app import app
import database

with app.app_context():
    database.init_db()
    database.seed_database_if_empty()

if __name__ == '__main__':
    app.run()
