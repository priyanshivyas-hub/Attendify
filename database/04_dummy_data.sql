USE attendify;
GO

-- ================================
-- RANDOM ATTENDANCE
-- ================================
DECLARE @iid INT, @sid INT, @status VARCHAR(20);

DECLARE class_cursor CURSOR FOR
SELECT instance_id FROM class_instances;

OPEN class_cursor;
FETCH NEXT FROM class_cursor INTO @iid;

WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE student_cursor CURSOR FOR
    SELECT user_id FROM users WHERE role='student';

    OPEN student_cursor;
    FETCH NEXT FROM student_cursor INTO @sid;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        DECLARE @r FLOAT = RAND(CHECKSUM(NEWID()));

        IF @r < 0.7 SET @status='present';
        ELSE IF @r < 0.85 SET @status='absent';
        ELSE IF @r < 0.95 SET @status='late';
        ELSE SET @status='excused';

        INSERT INTO attendance (instance_id,student_id,status,marked_by)
        VALUES (@iid,@sid,@status,1);

        FETCH NEXT FROM student_cursor INTO @sid;
    END

    CLOSE student_cursor;
    DEALLOCATE student_cursor;

    FETCH NEXT FROM class_cursor INTO @iid;
END

CLOSE class_cursor;
DEALLOCATE class_cursor;
GO


-- ================================
-- SAMPLE DISPUTES
-- ================================
INSERT INTO disputes (attendance_id,student_id,reason,status)
SELECT TOP 10 attendance_id,student_id,
'I was present that day',
'pending'
FROM attendance
WHERE status='absent'
ORDER BY NEWID();
GO


-- ================================
-- ISSUE CATEGORIES
-- ================================
INSERT INTO issue_categories (name,default_assignee_role) VALUES
('Classroom','dean'),
('Lab Equipment','hod'),
('Network','maintenance'),
('Cleanliness','maintenance');
GO


-- ================================
-- SAMPLE ISSUE
-- ================================
DECLARE @student INT=(SELECT TOP 1 user_id FROM users WHERE role='student');
DECLARE @cat INT=(SELECT TOP 1 cat_id FROM issue_categories);

INSERT INTO issues (reporter_id,category_id,title,description,status)
VALUES (@student,@cat,
'Projector not working',
'The projector in B-003 is not turning on.',
'pending');
GO


-- ================================
-- SAMPLE CONVERSATION
-- ================================
DECLARE @s INT=(SELECT TOP 1 user_id FROM users WHERE role='student');
DECLARE @p INT=(SELECT TOP 1 user_id FROM users WHERE role='professor');

INSERT INTO conversations (user1_id,user2_id)
VALUES (@s,@p);

DECLARE @conv INT=(SELECT TOP 1 conv_id FROM conversations);

INSERT INTO messages (conv_id,sender_id,content)
VALUES (@conv,@p,'Hello, how can I help you?');
GO