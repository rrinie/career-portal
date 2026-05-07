-- 1. Şirketler
CREATE TABLE Company (
    CompanyID SERIAL PRIMARY KEY,
    CompanyName VARCHAR(100) NOT NULL,
    Industry VARCHAR(50),
    City VARCHAR(50),
    ContactEmail VARCHAR(100) UNIQUE NOT NULL
);

-- 2. Departmanlar
CREATE TABLE Department (
    DepartmentID SERIAL PRIMARY KEY,
    DepartmentName VARCHAR(100) NOT NULL
);

-- 3. Pozisyonlar
CREATE TABLE Position (
    PositionID SERIAL PRIMARY KEY,
    DepartmentID INT NOT NULL,
    PositionName VARCHAR(100) NOT NULL,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID)
);

-- 4. İş Arayanlar
CREATE TABLE JobSeeker (
    SeekerID SERIAL PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    Phone VARCHAR(20)
);

-- 5. CV Profili
CREATE TABLE CV_Profile (
    ProfileID SERIAL PRIMARY KEY,
    SeekerID INT UNIQUE NOT NULL,
    EducationLevel VARCHAR(50),
    ExperienceYears INT,
    LinkedInURL VARCHAR(255),
    Summary TEXT,
    FOREIGN KEY (SeekerID) REFERENCES JobSeeker(SeekerID) ON DELETE CASCADE
);

-- 6. İş İlanları
CREATE TABLE JobPosting (
    PostingID SERIAL PRIMARY KEY,
    CompanyID INT NOT NULL,
    PositionID INT NOT NULL,
    Title VARCHAR(100) NOT NULL,
    WorkType VARCHAR(50),
    Deadline DATE,
    FOREIGN KEY (CompanyID) REFERENCES Company(CompanyID) ON DELETE CASCADE,
    FOREIGN KEY (PositionID) REFERENCES Position(PositionID)
);

-- 7. Soru Paketleri
CREATE TABLE QuestionPackage (
    PackageID SERIAL PRIMARY KEY,
    PostingID INT NOT NULL,
    PackageName VARCHAR(100),
    TimeLimitMinutes INT,
    FOREIGN KEY (PostingID) REFERENCES JobPosting(PostingID) ON DELETE CASCADE
);

-- 8. Mülakat Soruları
CREATE TABLE Question (
    QuestionID SERIAL PRIMARY KEY,
    PackageID INT NOT NULL,
    QuestionText TEXT NOT NULL,
    Points INT,
    FOREIGN KEY (PackageID) REFERENCES QuestionPackage(PackageID) ON DELETE CASCADE
);

-- 9. Başvurular
CREATE TABLE Application (
    ApplicationID SERIAL PRIMARY KEY,
    SeekerID INT NOT NULL,
    PostingID INT NOT NULL,
    ApplicationDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (SeekerID) REFERENCES JobSeeker(SeekerID) ON DELETE CASCADE,
    FOREIGN KEY (PostingID) REFERENCES JobPosting(PostingID) ON DELETE CASCADE
);

-- 10. Video Mülakat
CREATE TABLE VideoInterview (
    InterviewID SERIAL PRIMARY KEY,
    ApplicationID INT NOT NULL,
    PackageID INT NOT NULL,
    VideoURL VARCHAR(255),
    Score DECIMAL(5,2),
    ReviewerNotes TEXT,
    FOREIGN KEY (ApplicationID) REFERENCES Application(ApplicationID) ON DELETE CASCADE,
    FOREIGN KEY (PackageID) REFERENCES QuestionPackage(PackageID)
);
