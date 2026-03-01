USE attendify;
GO

/* =========================================================
   DROP OLD TABLES IF THEY EXIST (SAFE RESET)
========================================================= */

IF OBJECT_ID('professor_location_history', 'U') IS NOT NULL
    DROP TABLE professor_location_history;

IF OBJECT_ID('professor_current_location', 'U') IS NOT NULL
    DROP TABLE professor_current_location;

IF OBJECT_ID('campus_locations', 'U') IS NOT NULL
    DROP TABLE campus_locations;

GO


/* =========================================================
   1️⃣ CAMPUS LOCATIONS MASTER TABLE
========================================================= */

CREATE TABLE campus_locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    building NVARCHAR(100) NOT NULL,
    room NVARCHAR(50) NOT NULL,
    floor NVARCHAR(20),
    description NVARCHAR(255)
);

GO


/* =========================================================
   2️⃣ PROFESSOR CURRENT LIVE LOCATION
   (ONLY ONE ROW PER PROFESSOR)
========================================================= */

CREATE TABLE professor_current_location (
    professor_id INT PRIMARY KEY,
    location_type NVARCHAR(50),      -- Office / Lab / Class / Meeting / Leave
    building NVARCHAR(100),
    room NVARCHAR(50),
    status NVARCHAR(50),             -- Free / Busy / In Class / Available Soon
    notes NVARCHAR(255),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (professor_id) REFERENCES users(user_id)
);

GO


/* =========================================================
   3️⃣ PROFESSOR LOCATION HISTORY TABLE
========================================================= */

CREATE TABLE professor_location_history (
    history_id INT IDENTITY(1,1) PRIMARY KEY,
    professor_id INT NOT NULL,
    location_type NVARCHAR(50),
    building NVARCHAR(100),
    room NVARCHAR(50),
    status NVARCHAR(50),
    notes NVARCHAR(255),
    recorded_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (professor_id) REFERENCES users(user_id)
);

GO


/* =========================================================
   4️⃣ SAMPLE CAMPUS ROOMS (EDIT AS NEEDED)
========================================================= */

INSERT INTO campus_locations (building, room, floor, description) VALUES
('IT Block', '101', '1st Floor', 'Data Structures Lab'),
('IT Block', '102', '1st Floor', 'Programming Lab'),
('IT Block', '201', '2nd Floor', 'Faculty Office'),
('Admin Block', '301', '3rd Floor', 'Meeting Room'),
('Main Building', 'Auditorium', 'Ground Floor', 'Seminar Hall');

GO


/* =========================================================
   5️⃣ VIEW FOR STUDENT DASHBOARD (LIVE VIEW)
========================================================= */

CREATE OR ALTER VIEW vw_professor_live_status AS
SELECT 
    u.user_id,
    u.full_name,
    u.department,
    pcl.location_type,
    pcl.building,
    pcl.room,
    pcl.status,
    pcl.notes,
    pcl.updated_at,
    DATEDIFF(minute, pcl.updated_at, GETDATE()) AS minutes_since_update
FROM users u
LEFT JOIN professor_current_location pcl
    ON u.user_id = pcl.professor_id
WHERE u.role = 'professor';

GO