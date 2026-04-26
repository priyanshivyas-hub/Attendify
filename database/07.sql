CREATE TABLE special_class_days (
    id INT IDENTITY PRIMARY KEY,
    class_date DATE NOT NULL,
    follow_day VARCHAR(10) NOT NULL,
    approved BIT DEFAULT 0,
    created_by INT,
    note VARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);  