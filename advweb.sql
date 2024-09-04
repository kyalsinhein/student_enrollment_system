BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "admin" (
	"id"	INTEGER,
	"first_name"	TEXT NOT NULL,
	"last_name"	TEXT NOT NULL,
	"phone"	INTEGER NOT NULL,
	"email"	TEXT NOT NULL,
	"address"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "course" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL,
	"image"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"credits"	INTEGER NOT NULL,
	"lecturer"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "student" (
	"id"	INTEGER,
	"first_name"	TEXT NOT NULL,
	"last_name"	TEXT NOT NULL,
	"email"	TEXT NOT NULL,
	"phone"	INTEGER NOT NULL,
	"address"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "enrollment" (
	"id"	INTEGER,
	"student_id"	INTEGER NOT NULL,
	"course_id"	INTEGER NOT NULL,
	"enroll_date"	DATE NOT NULL,
	FOREIGN KEY("student_id") REFERENCES "student"("id") ON DELETE RESTRICT,
	FOREIGN KEY("course_id") REFERENCES "course"("id") ON DELETE RESTRICT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "schedule" (
	"id"	INTEGER,
	"course_id"	INTEGER NOT NULL,
	"day_of_week"	TEXT NOT NULL,
	"start_time"	TEXT NOT NULL,
	"end_time"	TEXT NOT NULL,
	FOREIGN KEY("course_id") REFERENCES "course"("id") ON DELETE CASCADE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "admin" VALUES (1,'admin1','Hein',1111111,'admin123@gmail.com','Yangon','202cb962ac59075b964b07152d234b70');
INSERT INTO "course" VALUES (3,'Python','Png.png','sdsd',2,'Mr.Tim');
INSERT INTO "student" VALUES (1,'Kyal','Sin Hein','kyalsinhein6356@gmail.com',9779943077,'Yangon','202cb962ac59075b964b07152d234b70');
INSERT INTO "enrollment" VALUES (2,1,3,'2024-09-03');
COMMIT;
