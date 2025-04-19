-- Drop and create the database
DROP DATABASE IF EXISTS CanvasCord;
CREATE DATABASE CanvasCord;
USE CanvasCord;

-- Users table
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    DiscordID VARCHAR(255) NOT NULL UNIQUE
);

-- Servers table
CREATE TABLE Servers (
    ServerID INT AUTO_INCREMENT PRIMARY KEY,
    ServerName VARCHAR(255),
    ChannelID BIGINT
);

-- Classes table
CREATE TABLE Classes (
    ClassID INT AUTO_INCREMENT PRIMARY KEY,
    CanvasClassID VARCHAR(255),
    ClassName VARCHAR(255)
);

-- Canvas_Token table
CREATE TABLE Canvas_Token (
    TokenID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    Domain VARCHAR(255) NOT NULL,
    Token VARCHAR(255) NOT NULL,
    ExpirationDate DATETIME,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Configurations table
CREATE TABLE Configurations (
    ConfigID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    EnableNotifications BOOLEAN DEFAULT TRUE,
    GradePostings BOOLEAN DEFAULT TRUE,
    DueDates BOOLEAN DEFAULT TRUE,
    AnnouncementPostings BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Reminders table
CREATE TABLE Reminders (
    ReminderID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NOT NULL,
    `When` VARCHAR(255) NOT NULL,
    Recurring ENUM('daily', 'weekly'),
    Content VARCHAR(255),
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);