CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    hostname TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    status TEXT NOT NULL
);
