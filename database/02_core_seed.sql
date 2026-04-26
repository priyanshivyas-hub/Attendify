USE attendify;
GO

DECLARE @pwd_hash VARCHAR(255) = '$2b$12$Z6SLzRyZkth.GlW20S73i.ct4YFO7sgUN7wCujHd.MhPIM4CJ4oAC';

-- ================= ADMIN =================
INSERT INTO users (email, password_hash, full_name, role, department)
VALUES ('admin@medicaps.ac.in', @pwd_hash, 'Admin User', 'admin', 'Administration');

-- ================= PROFESSORS =================
INSERT INTO users (email, password_hash, full_name, role, department) VALUES
('sagar.pandya@medicaps.ac.in', @pwd_hash, 'Prof. Sagar Pandya', 'professor', 'IT'),
('rahul.pawar@medicaps.ac.in', @pwd_hash, 'Prof. Rahul Singh Pawar', 'professor', 'IT'),
('neha.modak@medicaps.ac.in', @pwd_hash, 'Ms. Neha Modak', 'professor', 'IT'),
('jyoti.kukade@medicaps.ac.in', @pwd_hash, 'Prof. Jyoti Kukade', 'professor', 'IT'),
('prabhat.pandey@medicaps.ac.in', @pwd_hash, 'Dr. Prabhat Pandey', 'professor', 'IT'),
('vandana.birle@medicaps.ac.in', @pwd_hash, 'Prof. Vandana Birle', 'professor', 'IT'),
('nf2@medicaps.ac.in', @pwd_hash, 'NF2 (Soft Skills)', 'professor', 'HSS'),
('dean.it@medicaps.ac.in', @pwd_hash, 'Dean of IT', 'professor', 'IT'),
('dean.cse@medicaps.ac.in', @pwd_hash, 'Dean of CSE', 'professor', 'CSE'),
('vc@medicaps.ac.in', @pwd_hash, 'Vice Chancellor', 'admin', 'Administration');

-- ================= STUDENTS =================
INSERT INTO users (email, password_hash, full_name, role, department) VALUES
('en24it3010061@medicaps.ac.in', @pwd_hash, 'KUSH GANGRADE', 'student', 'IT'),
('en24it3010062@medicaps.ac.in', @pwd_hash, 'KUSHAL PATHAK', 'student', 'IT'),
('en24it3010063@medicaps.ac.in', @pwd_hash, 'LAKSHYADITYA KARDAM', 'student', 'IT'),
('en24it3010064@medicaps.ac.in', @pwd_hash, 'MAANYA WALEKAR', 'student', 'IT'),
('en24it3010065@medicaps.ac.in', @pwd_hash, 'MANASVI CHOUHAN', 'student', 'IT'),
('en24it3010066@medicaps.ac.in', @pwd_hash, 'MANSI MUKATI', 'student', 'IT'),
('en24it3010067@medicaps.ac.in', @pwd_hash, 'MAYUR PATEL', 'student', 'IT'),
('en24it3010068@medicaps.ac.in', @pwd_hash, 'MOAYAN FOUJDAR', 'student', 'IT'),
('en24it3010069@medicaps.ac.in', @pwd_hash, 'MOUSAM NAGAR', 'student', 'IT'),
('en24it3010070@medicaps.ac.in', @pwd_hash, 'MUSKAN MALAKAR', 'student', 'IT'),
('en24it3010071@medicaps.ac.in', @pwd_hash, 'NAVNEET SINGH RAJPUT', 'student', 'IT'),
('en24it3010072@medicaps.ac.in', @pwd_hash, 'NISHTHA DHINGRA', 'student', 'IT'),
('en24it3010073@medicaps.ac.in', @pwd_hash, 'NISHTHA SONI', 'student', 'IT'),
('en24it3010074@medicaps.ac.in', @pwd_hash, 'OJAS PATIDAR', 'student', 'IT'),
('en24it3010077@medicaps.ac.in', @pwd_hash, 'PIYUSH JANGID', 'student', 'IT'),
('en24it3010078@medicaps.ac.in', @pwd_hash, 'PRAMUKH KUMBHKAR', 'student', 'IT'),
('en24it3010079@medicaps.ac.in', @pwd_hash, 'PRANJAL SHARMA', 'student', 'IT'),
('en24it3010081@medicaps.ac.in', @pwd_hash, 'PRAVIN CHOUHAN', 'student', 'IT'),
('en24it3010082@medicaps.ac.in', @pwd_hash, 'PREYASI SHRIVASTAVA', 'student', 'IT'),
('en24it3010083@medicaps.ac.in', @pwd_hash, 'PRIYANKA BINTHARIYA', 'student', 'IT'),
('en24it3010084@medicaps.ac.in', @pwd_hash, 'PRIYANSH VERMA', 'student', 'IT'),
('en24it3010085@medicaps.ac.in', @pwd_hash, 'PRIYANSHI MAHESHWARI', 'student', 'IT'),
('en24it3010086@medicaps.ac.in', @pwd_hash, 'PRIYANSHI VYAS', 'student', 'IT'),
('en24it3010087@medicaps.ac.in', @pwd_hash, 'PRIYANSHU JAISWAL', 'student', 'IT'),
('en24it3010088@medicaps.ac.in', @pwd_hash, 'PRIYANSHU RAJPUT', 'student', 'IT'),
('en24it3010089@medicaps.ac.in', @pwd_hash, 'RADHIKA PALOD', 'student', 'IT'),
('en24it3010090@medicaps.ac.in', @pwd_hash, 'RAJNANDINI TOMAR', 'student', 'IT'),
('en24it3010091@medicaps.ac.in', @pwd_hash, 'RAM', 'student', 'IT'),
('en24it3010093@medicaps.ac.in', @pwd_hash, 'RIDIMA SONER', 'student', 'IT'),
('en24it3010094@medicaps.ac.in', @pwd_hash, 'RISHIKA RATHOD', 'student', 'IT'),
('en24it3010095@medicaps.ac.in', @pwd_hash, 'RITIK POUNEKAR', 'student', 'IT'),
('en24it3010096@medicaps.ac.in', @pwd_hash, 'ROHAN KALYANE', 'student', 'IT'),
('en24it3010097@medicaps.ac.in', @pwd_hash, 'RUCHI CHATURVEDI', 'student', 'IT'),
('en24it3010099@medicaps.ac.in', @pwd_hash, 'SAMARTH MAURYA', 'student', 'IT'),
('en24it3010100@medicaps.ac.in', @pwd_hash, 'SAMARTH SINGH SISODIYA', 'student', 'IT'),
('en24it3010101@medicaps.ac.in', @pwd_hash, 'SAUMYA AGRAWAL', 'student', 'IT'),
('en24it3010102@medicaps.ac.in', @pwd_hash, 'SHABBIR EZZY', 'student', 'IT'),
('en24it3010103@medicaps.ac.in', @pwd_hash, 'SHAHEER AHMED CHOUDHARY', 'student', 'IT'),
('en24it3010104@medicaps.ac.in', @pwd_hash, 'SHAILY PATIDAR', 'student', 'IT'),
('en24it3010105@medicaps.ac.in', @pwd_hash, 'SHAURYA JAIN', 'student', 'IT'),
('en24it3010106@medicaps.ac.in', @pwd_hash, 'SHREYA REDDY', 'student', 'IT'),
('en24it3010107@medicaps.ac.in', @pwd_hash, 'SIDDHANT KAURAV', 'student', 'IT'),
('en24it3010108@medicaps.ac.in', @pwd_hash, 'SOMIL JAIN', 'student', 'IT'),
('en24it3010109@medicaps.ac.in', @pwd_hash, 'SOMYA KUSHWAH', 'student', 'IT'),
('en24it3010110@medicaps.ac.in', @pwd_hash, 'SONALI KELWA', 'student', 'IT'),
('en24it3010111@medicaps.ac.in', @pwd_hash, 'TANISHA RATHORE', 'student', 'IT'),
('en24it3010112@medicaps.ac.in', @pwd_hash, 'TUSHAR LAAD', 'student', 'IT'),
('en24it3010113@medicaps.ac.in', @pwd_hash, 'UKE REVATI KAILAS', 'student', 'IT'),
('en24it3010114@medicaps.ac.in', @pwd_hash, 'VAIBHAV KUMAR SINGH', 'student', 'IT'),
('en24it3010115@medicaps.ac.in', @pwd_hash, 'VAISHANVI SINGH', 'student', 'IT'),
('en24it3010116@medicaps.ac.in', @pwd_hash, 'VANDANA KUMARI', 'student', 'IT'),
('en24it3010117@medicaps.ac.in', @pwd_hash, 'VANSHIKA KATHAL', 'student', 'IT'),
('en24it3010118@medicaps.ac.in', @pwd_hash, 'VANSHIKA YADAV', 'student', 'IT'),
('en24it3010119@medicaps.ac.in', @pwd_hash, 'VIRENDRA SINGH KAMDAR', 'student', 'IT'),
('en24it3010120@medicaps.ac.in', @pwd_hash, 'YUVRAJ SINGH BAGHEL', 'student', 'IT'),
('en24me3040040@medicaps.ac.in', @pwd_hash, 'KHANAK SONONE', 'student', 'IT'),
('en24me3040041@medicaps.ac.in', @pwd_hash, 'KHUSH PATIDAR', 'student', 'IT'),
('en24me3040051@medicaps.ac.in', @pwd_hash, 'MAYANK SHARMA', 'student', 'IT'),
('en24me3040111@medicaps.ac.in', @pwd_hash, 'YOGITA KUMAVAT', 'student', 'IT'),
('en25it3l10001@medicaps.ac.in', @pwd_hash, 'TEJASV GAWANDE', 'student', 'IT');