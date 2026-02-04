from db.db import get_connection

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            isActive BOOLEAN DEFAULT 1
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dataset (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER NOT NULL,
            frameLimit INTEGER,
            status TEXT CHECK(status IN ('SPENDING','USED')) DEFAULT 'SPENDING',
            expiresAt DATETIME,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userID) REFERENCES User(ID)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Weight (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER NOT NULL,
            datasetID INTEGER,
            storageURL TEXT,
            isCurrentlyUse BOOLEAN DEFAULT 0,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userID) REFERENCES User(ID),
            FOREIGN KEY (datasetID) REFERENCES Dataset(ID)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Session (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID INTEGER NOT NULL,
            startTime DATETIME,
            endTime DATETIME,
            FOREIGN KEY (userID) REFERENCES User(ID)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS DrowsyVideo (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            sessionID INTEGER NOT NULL,
            startTime DATETIME,
            endTime DATETIME,
            userChoiceLabel BOOLEAN,
            FOREIGN KEY (sessionID) REFERENCES Session(ID)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Frame (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            drowsyVideoID INTEGER NOT NULL,
            confidenceScore REAL,
            modelPrediction BOOLEAN,
            imageURL TEXT,
            datasetID INTEGER,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (drowsyVideoID) REFERENCES DrowsyVideo(ID),
            FOREIGN KEY (datasetID) REFERENCES Dataset(ID)
        )
        """)

        conn.commit()
        print("✅ All tables created successfully.")
