USE attendify;
GO

DECLARE @pwd_hash VARCHAR(255) = '$2b$12$Z6SLzRyZkth.GlW20S73i.ct4YFO7sgUN7wCujHd.MhPIM4CJ4oAC';

-- ================= ADMIN =================
INSERT INTO users (email, password_hash, full_name, role, department)
VALUES ('admin@attendify.com', @pwd_hash, 'Admin User', 'admin', 'Administration');

-- ================= PROFESSORS =================
INSERT INTO users (email, password_hash, full_name, role, department) VALUES
('sagar.pandya@attendify.com', @pwd_hash, 'Prof. Sagar Pandya', 'professor', 'IT'),
('rahul.pawar@attendify.com', @pwd_hash, 'Prof. Rahul Singh Pawar', 'professor', 'IT'),
('neha.modak@attendify.com', @pwd_hash, 'Ms. Neha Modak', 'professor', 'IT'),
('jyoti.kukade@attendify.com', @pwd_hash, 'Prof. Jyoti Kukade', 'professor', 'IT'),
('prabhat.pandey@attendify.com', @pwd_hash, 'Dr. Prabhat Pandey', 'professor', 'IT'),
('vandana.birle@attendify.com', @pwd_hash, 'Prof. Vandana Birle', 'professor', 'IT'),
('nf2@attendify.com', @pwd_hash, 'NF2 (Soft Skills)', 'professor', 'HSS'),
('dean.it@attendify.com', @pwd_hash, 'Dean of IT', 'professor', 'IT'),
('dean.cse@attendify.com', @pwd_hash, 'Dean of CSE', 'professor', 'CSE'),
('vc@attendify.com', @pwd_hash, 'Vice Chancellor', 'admin', 'Administration');

-- ================= STUDENTS =================
-- (Your full batch exactly as provided earlier)

INSERT INTO users (email, password_hash, full_name, role, department) VALUES
('EN24IT3010061@attendify.com', @pwd_hash, 'KUSH GANGRADE', 'student', 'IT'),
('EN24IT3010062@attendify.com', @pwd_hash, 'KUSHAL PATHAK', 'student', 'IT'),
('EN24IT3010063@attendify.com', @pwd_hash, 'LAKSHYADITYA KARDAM', 'student', 'IT'),
('EN24IT3010064@attendify.com', @pwd_hash, 'MAANYA WALEKAR', 'student', 'IT'),
('EN24IT3010065@attendify.com', @pwd_hash, 'MANASVI CHOUHAN', 'student', 'IT'),
('EN24IT3010066@attendify.com', @pwd_hash, 'MANSI MUKATI', 'student', 'IT'),
('EN24IT3010067@attendify.com', @pwd_hash, 'MAYUR PATEL', 'student', 'IT'),
('EN24IT3010068@attendify.com', @pwd_hash, 'MOAYAN FOUJDAR', 'student', 'IT'),
('EN24IT3010069@attendify.com', @pwd_hash, 'MOUSAM NAGAR', 'student', 'IT'),
('EN24IT3010070@attendify.com', @pwd_hash, 'MUSKAN MALAKAR', 'student', 'IT'),
('EN24IT3010071@attendify.com', @pwd_hash, 'NAVNEET SINGH RAJPUT', 'student', 'IT'),
('EN24IT3010072@attendify.com', @pwd_hash, 'NISHTHA DHINGRA', 'student', 'IT'),
('EN24IT3010073@attendify.com', @pwd_hash, 'NISHTHA SONI', 'student', 'IT'),
('EN24IT3010074@attendify.com', @pwd_hash, 'OJAS PATIDAR', 'student', 'IT'),
('EN24IT3010077@attendify.com', @pwd_hash, 'PIYUSH JANGID', 'student', 'IT'),
('EN24IT3010078@attendify.com', @pwd_hash, 'PRAMUKH KUMBHKAR', 'student', 'IT'),
('EN24IT3010079@attendify.com', @pwd_hash, 'PRANJAL SHARMA', 'student', 'IT'),
('EN24IT3010081@attendify.com', @pwd_hash, 'PRAVIN CHOUHAN', 'student', 'IT'),
('EN24IT3010082@attendify.com', @pwd_hash, 'PREYASI SHRIVASTAVA', 'student', 'IT'),
('EN24IT3010083@attendify.com', @pwd_hash, 'PRIYANKA BINTHARIYA', 'student', 'IT'),
('EN24IT3010084@attendify.com', @pwd_hash, 'PRIYANSH VERMA', 'student', 'IT'),
('EN24IT3010085@attendify.com', @pwd_hash, 'PRIYANSHI MAHESHWARI', 'student', 'IT'),
('EN24IT3010086@attendify.com', @pwd_hash, 'PRIYANSHI VYAS', 'student', 'IT'),
('EN24IT3010087@attendify.com', @pwd_hash, 'PRIYANSHU JAISWAL', 'student', 'IT'),
('EN24IT3010088@attendify.com', @pwd_hash, 'PRIYANSHU RAJPUT', 'student', 'IT'),
('EN24IT3010089@attendify.com', @pwd_hash, 'RADHIKA PALOD', 'student', 'IT'),
('EN24IT3010090@attendify.com', @pwd_hash, 'RAJNANDINI TOMAR', 'student', 'IT'),
('EN24IT3010091@attendify.com', @pwd_hash, 'RAM', 'student', 'IT'),
('EN24IT3010093@attendify.com', @pwd_hash, 'RIDIMA SONER', 'student', 'IT'),
('EN24IT3010094@attendify.com', @pwd_hash, 'RISHIKA RATHOD', 'student', 'IT'),
('EN24IT3010095@attendify.com', @pwd_hash, 'RITIK POUNEKAR', 'student', 'IT'),
('EN24IT3010096@attendify.com', @pwd_hash, 'ROHAN KALYANE', 'student', 'IT'),
('EN24IT3010097@attendify.com', @pwd_hash, 'RUCHI CHATURVEDI', 'student', 'IT'),
('EN24IT3010099@attendify.com', @pwd_hash, 'SAMARTH MAURYA', 'student', 'IT'),
('EN24IT3010100@attendify.com', @pwd_hash, 'SAMARTH SINGH SISODIYA', 'student', 'IT'),
('EN24IT3010101@attendify.com', @pwd_hash, 'SAUMYA AGRAWAL', 'student', 'IT'),
('EN24IT3010102@attendify.com', @pwd_hash, 'SHABBIR EZZY', 'student', 'IT'),
('EN24IT3010103@attendify.com', @pwd_hash, 'SHAHEER AHMED CHOUDHARY', 'student', 'IT'),
('EN24IT3010104@attendify.com', @pwd_hash, 'SHAILY PATIDAR', 'student', 'IT'),
('EN24IT3010105@attendify.com', @pwd_hash, 'SHAURYA JAIN', 'student', 'IT'),
('EN24IT3010106@attendify.com', @pwd_hash, 'SHREYA REDDY', 'student', 'IT'),
('EN24IT3010107@attendify.com', @pwd_hash, 'SIDDHANT KAURAV', 'student', 'IT'),
('EN24IT3010108@attendify.com', @pwd_hash, 'SOMIL JAIN', 'student', 'IT'),
('EN24IT3010109@attendify.com', @pwd_hash, 'SOMYA KUSHWAH', 'student', 'IT'),
('EN24IT3010110@attendify.com', @pwd_hash, 'SONALI KELWA', 'student', 'IT'),
('EN24IT3010111@attendify.com', @pwd_hash, 'TANISHA RATHORE', 'student', 'IT'),
('EN24IT3010112@attendify.com', @pwd_hash, 'TUSHAR LAAD', 'student', 'IT'),
('EN24IT3010113@attendify.com', @pwd_hash, 'UKE REVATI KAILAS', 'student', 'IT'),
('EN24IT3010114@attendify.com', @pwd_hash, 'VAIBHAV KUMAR SINGH', 'student', 'IT'),
('EN24IT3010115@attendify.com', @pwd_hash, 'VAISHANVI SINGH', 'student', 'IT'),
('EN24IT3010116@attendify.com', @pwd_hash, 'VANDANA KUMARI', 'student', 'IT'),
('EN24IT3010117@attendify.com', @pwd_hash, 'VANSHIKA KATHAL', 'student', 'IT'),
('EN24IT3010118@attendify.com', @pwd_hash, 'VANSHIKA YADAV', 'student', 'IT'),
('EN24IT3010119@attendify.com', @pwd_hash, 'VIRENDRA SINGH KAMDAR', 'student', 'IT'),
('EN24IT3010120@attendify.com', @pwd_hash, 'YUVRAJ SINGH BAGHEL', 'student', 'IT'),
('EN24ME3040040@attendify.com', @pwd_hash, 'KHANAK SONONE', 'student', 'IT'),
('EN24ME3040041@attendify.com', @pwd_hash, 'KHUSH PATIDAR', 'student', 'IT'),
('EN24ME3040051@attendify.com', @pwd_hash, 'MAYANK SHARMA', 'student', 'IT'),
('EN24ME3040111@attendify.com', @pwd_hash, 'YOGITA KUMAVAT', 'student', 'IT'),
('EN25IT3L10001@attendify.com', @pwd_hash, 'TEJASV GAWANDE', 'student', 'IT');