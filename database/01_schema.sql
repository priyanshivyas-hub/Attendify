-- ==========================================
-- CREATE DATABASE
-- ==========================================
IF DB_ID('attendify') IS NULL
CREATE DATABASE attendify;
GO

USE attendify;
GO

-- USERS
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('student','professor','admin')),
    department VARCHAR(50),
    custom_attendance_threshold INT NULL
);

-- COURSES
CREATE TABLE courses (
    course_id INT IDENTITY(1,1) PRIMARY KEY,
    course_code VARCHAR(30) UNIQUE,
    course_name VARCHAR(150),
    department VARCHAR(50),
    credits INT,
    professor_id INT,
    semester VARCHAR(20),
    year INT,
    total_lectures INT,
    FOREIGN KEY (professor_id) REFERENCES users(user_id)
);

-- ENROLLMENTS
CREATE TABLE enrollments (
    enrollment_id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT,
    course_id INT,
    CONSTRAINT unique_enrollment UNIQUE (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- SCHEDULE
CREATE TABLE schedule (
    schedule_id INT IDENTITY(1,1) PRIMARY KEY,
    course_id INT,
    day_of_week VARCHAR(10),
    start_time TIME,
    end_time TIME,
    room VARCHAR(50),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- CLASS INSTANCES
CREATE TABLE class_instances (
    instance_id INT IDENTITY(1,1) PRIMARY KEY,
    schedule_id INT,
    class_date DATE,
    status VARCHAR(20) DEFAULT 'scheduled',
    cancellation_reason VARCHAR(255),
    FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
);

-- ATTENDANCE
CREATE TABLE attendance (
    attendance_id INT IDENTITY(1,1) PRIMARY KEY,
    instance_id INT,
    student_id INT,
    status VARCHAR(20),
    marked_by INT,
    marked_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (instance_id) REFERENCES class_instances(instance_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- DISPUTES
CREATE TABLE disputes (
    dispute_id INT IDENTITY(1,1) PRIMARY KEY,
    attendance_id INT,
    student_id INT,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    submitted_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (attendance_id) REFERENCES attendance(attendance_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

CREATE TABLE holidays (
    holiday_id INT IDENTITY(1,1) PRIMARY KEY,
    holiday_date DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL
);
GO

-- LOCATIONS
CREATE TABLE locations (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    building VARCHAR(50)
);

-- PATHS
CREATE TABLE paths (
    path_id INT IDENTITY(1,1) PRIMARY KEY,
    from_location INT,
    to_location INT,
    distance DECIMAL(10,2),
    bidirectional BIT DEFAULT 1,
    FOREIGN KEY (from_location) REFERENCES locations(location_id),
    FOREIGN KEY (to_location) REFERENCES locations(location_id)
);

-- MESSAGING
CREATE TABLE conversations (
    conv_id INT IDENTITY(1,1) PRIMARY KEY,
    user1_id INT,
    user2_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT unique_conversation UNIQUE (user1_id, user2_id),
    FOREIGN KEY (user1_id) REFERENCES users(user_id),
    FOREIGN KEY (user2_id) REFERENCES users(user_id)
);

CREATE TABLE messages (
    msg_id INT IDENTITY(1,1) PRIMARY KEY,
    conv_id INT,
    sender_id INT,
    content TEXT,
    sent_at DATETIME DEFAULT GETDATE(),
    is_read BIT DEFAULT 0,
    FOREIGN KEY (conv_id) REFERENCES conversations(conv_id),
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
);

-- ISSUES
CREATE TABLE issue_categories (
    cat_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(50),
    default_assignee_role VARCHAR(20)
);

CREATE TABLE issues (
    issue_id INT IDENTITY(1,1) PRIMARY KEY,
    reporter_id INT,
    category_id INT,
    title VARCHAR(200),
    description TEXT,
    location_id INT,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to INT,
    created_at DATETIME DEFAULT GETDATE(),
    resolved_at DATETIME,
    FOREIGN KEY (reporter_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES issue_categories(cat_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);

CREATE TABLE issue_comments (
    comment_id INT IDENTITY(1,1) PRIMARY KEY,
    issue_id INT,
    user_id INT,
    comment TEXT,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (issue_id) REFERENCES issues(issue_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);