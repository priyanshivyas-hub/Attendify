USE attendify;
GO

-- ================================
-- GET PROFESSOR IDs
-- ================================
DECLARE @prof_sagar INT = (SELECT user_id FROM users WHERE email='sagar.pandya@attendify.com');
DECLARE @prof_rahul INT = (SELECT user_id FROM users WHERE email='rahul.pawar@attendify.com');
DECLARE @prof_neha INT = (SELECT user_id FROM users WHERE email='neha.modak@attendify.com');
DECLARE @prof_jyoti INT = (SELECT user_id FROM users WHERE email='jyoti.kukade@attendify.com');
DECLARE @prof_prabhat INT = (SELECT user_id FROM users WHERE email='prabhat.pandey@attendify.com');
DECLARE @prof_vandana INT = (SELECT user_id FROM users WHERE email='vandana.birle@attendify.com');
DECLARE @prof_nf2 INT = (SELECT user_id FROM users WHERE email='nf2@attendify.com');

-- ================================
-- COURSES
-- ================================
INSERT INTO courses (course_code, course_name, department, credits, professor_id, semester, year, total_lectures) VALUES
('IT3CO05','Database Management Systems','IT',4,@prof_sagar,'Even',2026,44),
('IT3CO21','Operating System','IT',4,@prof_rahul,'Even',2026,42),
('IT3CO29','Computational Statistics','IT',3,@prof_neha,'Even',2026,40),
('IT3CO30','Artificial Intelligence','IT',4,@prof_jyoti,'Even',2026,30),
('IT3CO32','Microprocessor & Microcontroller','IT',4,@prof_prabhat,'Even',2026,38),
('IT3CO34','Design and Analysis of Algorithms','IT',4,@prof_vandana,'Even',2026,38),
('EN3NG10','Soft Skills-II','HSS',2,@prof_nf2,'Even',2026,20),
('IT3CO05-LAB','DBMS Lab','IT',2,@prof_sagar,'Even',2026,30),
('IT3CO21-LAB','OS Lab','IT',2,@prof_rahul,'Even',2026,26),
('IT3CO34-LAB','DAA Lab','IT',2,@prof_vandana,'Even',2026,24),
('IT3CO32-LAB','MPMC Lab','IT',2,@prof_prabhat,'Even',2026,28);
GO

-- ================================
-- ENROLLMENTS
-- ================================
INSERT INTO enrollments (student_id, course_id)
SELECT s.user_id, c.course_id
FROM users s
CROSS JOIN courses c
WHERE s.role='student';
GO

-- ================================
-- HOLIDAYS
-- ================================
INSERT INTO holidays (holiday_date, name, type) VALUES
('2026-01-26','Republic Day','university'),
('2026-02-15','Maha Shivaratri','university'),
('2026-03-04','Holi','university'),
('2026-03-08','Rangpanchmi','university'),
('2026-03-21','Eid-Ul-Fitar','university'),
('2026-03-31','Mahavir Jayanti','university'),
('2026-04-03','Good Friday','university'),
('2026-04-14','Dr. Ambedkar Jayanti','university'),
('2026-05-01','Labour Day','university');
GO

-- ================================
-- GET COURSE IDs
-- ================================
DECLARE @dbms INT = (SELECT course_id FROM courses WHERE course_code='IT3CO05');
DECLARE @os INT = (SELECT course_id FROM courses WHERE course_code='IT3CO21');
DECLARE @cs INT = (SELECT course_id FROM courses WHERE course_code='IT3CO29');
DECLARE @ai INT = (SELECT course_id FROM courses WHERE course_code='IT3CO30');
DECLARE @mpmc INT = (SELECT course_id FROM courses WHERE course_code='IT3CO32');
DECLARE @daa INT = (SELECT course_id FROM courses WHERE course_code='IT3CO34');
DECLARE @ss INT = (SELECT course_id FROM courses WHERE course_code='EN3NG10');

-- ================================
-- WEEKLY SCHEDULE
-- ================================

-- MONDAY
INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES
(@mpmc,'Mon','08:30','09:20','B-103'),
(@mpmc,'Mon','09:20','10:10','B-103'),
(@daa,'Mon','10:20','11:10','B-003'),
(@os,'Mon','11:10','12:00','B-003'),
(@dbms,'Mon','12:50','13:40','B-003'),
(@ai,'Mon','13:40','14:20','B-003');

-- TUESDAY
INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES
(@os,'Tue','08:30','09:20','B-003'),
(@mpmc,'Tue','09:20','10:10','B-003'),
(@ss,'Tue','12:50','13:40','B-003'),
(@ss,'Tue','13:40','14:20','B-003');

-- WEDNESDAY
INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES
(@cs,'Wed','08:30','09:20','B-003'),
(@mpmc,'Wed','09:20','10:10','B-003'),
(@ai,'Wed','12:50','13:40','B-003'),
(@dbms,'Wed','13:40','14:20','B-003');

-- THURSDAY
INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES
(@daa,'Thu','08:30','09:20','B-003'),
(@daa,'Thu','09:20','10:10','B-003'),
(@os,'Thu','10:20','11:10','B-003'),
(@dbms,'Thu','11:10','12:00','B-003'),
(@cs,'Thu','12:50','13:40','B-003'),
(@daa,'Thu','13:40','14:20','B-003');

-- FRIDAY
INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES
(@dbms,'Fri','08:30','09:20','B-003'),
(@mpmc,'Fri','09:20','10:10','B-003'),
(@cs,'Fri','10:20','11:10','B-003'),
(@os,'Fri','11:10','12:00','B-003'),
(@daa,'Fri','12:50','13:40','B-003'),
(@ai,'Fri','13:40','14:20','B-003');
GO

-- ================================
-- GENERATE CLASS INSTANCES
-- ================================
DECLARE @start DATE='2026-01-01';
DECLARE @end DATE='2026-06-30';

WHILE @start <= @end
BEGIN
    IF DATENAME(WEEKDAY,@start) <> 'Sunday'
       AND NOT EXISTS (SELECT 1 FROM holidays WHERE holiday_date=@start)
    BEGIN
        INSERT INTO class_instances (schedule_id,class_date,status)
        SELECT schedule_id,@start,'scheduled'
        FROM schedule
        WHERE day_of_week = LEFT(DATENAME(WEEKDAY,@start),3);
    END

    SET @start = DATEADD(DAY,1,@start);
END
GO