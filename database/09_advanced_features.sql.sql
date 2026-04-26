-- Advanced Features Schema
USE attendify;
GO

-- User Faces for Biometric
CREATE TABLE user_faces (
    face_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    face_encoding VARBINARY(MAX),
    is_active BIT DEFAULT 1,
    registered_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Notifications
CREATE TABLE notifications (
    notification_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    type VARCHAR(50),
    data TEXT,
    timestamp DATETIME DEFAULT GETDATE(),
    is_read BIT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    action VARCHAR(100),
    table_name VARCHAR(50),
    record_id INT,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    timestamp DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- System Settings
CREATE TABLE system_settings (
    setting_id INT IDENTITY(1,1) PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT,
    updated_by INT,
    updated_at DATETIME DEFAULT GETDATE()
);

-- API Keys
CREATE TABLE api_keys (
    key_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    api_key VARCHAR(64) UNIQUE,
    name VARCHAR(100),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    expires_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Batch Attendance Jobs
CREATE TABLE attendance_jobs (
    job_id INT IDENTITY(1,1) PRIMARY KEY,
    instance_id INT,
    job_type VARCHAR(50),
    status VARCHAR(20),
    started_at DATETIME,
    completed_at DATETIME,
    result TEXT,
    FOREIGN KEY (instance_id) REFERENCES class_instances(instance_id)
);

-- Student Groups/Teams
CREATE TABLE student_groups (
    group_id INT IDENTITY(1,1) PRIMARY KEY,
    group_name VARCHAR(100),
    course_id INT,
    created_by INT,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE group_members (
    group_id INT,
    student_id INT,
    PRIMARY KEY (group_id, student_id),
    FOREIGN KEY (group_id) REFERENCES student_groups(group_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- Gamification
CREATE TABLE badges (
    badge_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    icon VARCHAR(255),
    criteria TEXT
);

CREATE TABLE user_badges (
    user_id INT,
    badge_id INT,
    earned_at DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (badge_id) REFERENCES badges(badge_id)
);

-- Student Points
CREATE TABLE student_points (
    point_id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT,
    points INT,
    reason VARCHAR(100),
    earned_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- QR Code Sessions
CREATE TABLE qr_sessions (
    session_id INT IDENTITY(1,1) PRIMARY KEY,
    instance_id INT,
    qr_code VARCHAR(255),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    expires_at DATETIME,
    FOREIGN KEY (instance_id) REFERENCES class_instances(instance_id)
);

-- Feedback System
CREATE TABLE feedback (
    feedback_id INT IDENTITY(1,1) PRIMARY KEY,
    from_user_id INT,
    to_user_id INT,
    course_id INT,
    rating INT,
    comment TEXT,
    is_anonymous BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (from_user_id) REFERENCES users(user_id),
    FOREIGN KEY (to_user_id) REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

GO