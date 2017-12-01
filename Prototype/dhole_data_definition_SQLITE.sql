/*
  ___________________________________________________________________
 
  DRILLHOLE SQL DEFINITION  
 
  Created:     Adrian Martinez Vargas, April 2015
              http://www.opengeostat.com/
 
  Modified:    Adrian Martinez Vargas, April 2017
 
  Copyright:   Adrian Martinez Vargas 
 
  License:     GNU General Public License V3 
              http://www.gnu.org/licenses/
 
  Description: This is a database definition file optimized for 
              SQLITE
 ___________________________________________________________________
*/

-- Active case sensitive and foreign support in SQLITE  
PRAGMA foreign_keys = ON;
PRAGMA case_sensitive_like = True;


/* ___________________________________________________________________
    
    Remove old tables.
    Warning: this is dangerous, you can lost your data
   ___________________________________________________________________
*/

-- Remove tables if exist
DROP TABLE IF EXISTS Assay;
DROP TABLE IF EXISTS Litho;
DROP TABLE IF EXISTS Lithologies;
DROP TABLE IF EXISTS Lab_Assay;
DROP TABLE IF EXISTS Survey;
DROP TABLE IF EXISTS Collar;


/* ___________________________________________________________________
    
    Put here the parent tables 
   ___________________________________________________________________
*/

-- Collar Table
CREATE TABLE Collar (
  BHID VARCHAR(45)  NOT NULL,
  XCOLLAR FLOAT  NOT NULL,
  YCOLLAR FLOAT  NOT NULL,
  ZCOLLAR FLOAT  NOT NULL,
  [LENGTH] FLOAT  NOT NULL,
  Comments VARCHAR(250),
PRIMARY KEY(BHID));

-- List of valid lithologies
CREATE TABLE Lithologies (
  Lithology_ID VARCHAR(20)  NOT NULL,
  Description VARCHAR(50),
  Comments VARCHAR(250),
PRIMARY KEY(Lithology_ID));

--assay as provided by the lab
CREATE TABLE Lab_Assay (
  Samp_ID VARCHAR(50)  NOT NULL,
  Au FLOAT,
PRIMARY KEY(Samp_ID));

/* ___________________________________________________________________
    
    Put here the child tables (tables with foreign key)
   ___________________________________________________________________
*/

-- Define the Survey Table
CREATE TABLE Survey (
  BHID VARCHAR(45)  NOT NULL,
  AT FLOAT  NOT NULL,
  AZ FLOAT  NOT NULL,
  DIP FLOAT  NOT NULL,
  PRIMARY KEY(BHID, AT),          -- no duplicates (BHID, AT) allowed
  FOREIGN KEY(BHID)               -- only BHID in the collar table are allowed
    REFERENCES Collar(BHID)       
      ON DELETE CASCADE           -- This will remove/rename BHID if BHID is  
      ON UPDATE CASCADE);         -- deleted or changed in Collar table


-- define Lithology table
CREATE TABLE Litho (
  BHID VARCHAR(45)  NOT NULL,
  [FROM] FLOAT  NOT NULL,
  [TO] FLOAT  NOT NULL,
  Lithology_ID VARCHAR(20)  NOT NULL,
  Log_memo VARCHAR(255),
  Comments VARCHAR(255),
 CONSTRAINT chk_interv 
    CHECK ([TO]>[FROM]),          -- ensure valid From,To intervals
 CONSTRAINT chk_litho
 PRIMARY KEY(BHID, [FROM]),       -- no duplicates (BHID, From) allowed
 FOREIGN KEY(BHID) 
  REFERENCES Collar(BHID)          
   ON DELETE CASCADE 
   ON UPDATE CASCADE,
 FOREIGN KEY(Lithology_ID)         -- This will remove/rename LITHOLOGYID if 
  REFERENCES                       -- it changes at Lithocode Table
     Lithologies(Lithology_ID) 
   ON DELETE SET NULL 
   ON UPDATE CASCADE);


-- define assay table
CREATE TABLE Assay (
  BHID VARCHAR(45)  NOT NULL,
  [FROM] FLOAT  NOT NULL,
  [TO] FLOAT  NOT NULL,
  Samp_ID VARCHAR(50)  NOT NULL,
  Comments VARCHAR(255),
CONSTRAINT chk_interv 
  CHECK ([TO]>[FROM]),             -- no zero thickness intervals
PRIMARY KEY(BHID, [FROM]),         -- no duplicates (BHID, From) allowed
  FOREIGN KEY(BHID)
    REFERENCES Collar(BHID)         
      ON DELETE CASCADE
      ON UPDATE CASCADE,
  FOREIGN KEY(Samp_ID)              -- if you change or delete assay certificate (Lab_Assay) it will update this table
    REFERENCES Lab_Assay(Samp_ID)
      ON DELETE SET NULL
      ON UPDATE CASCADE);


/* ___________________________________________________________________
    
    Here you can add triggers in order To improve Consistency
   ___________________________________________________________________
*/

-- To update values, for example bhid or litho id To ucase after 
-- update or insert use triggers as in the example below
/*
create trigger ucase_var after insert on Collar 
	begin 
	   update Collar set BHID=upper(new.BHID) where rowid=new.rowid; 
	end;
create trigger ucase_var2 after update on Collar 
	begin 
	   update Collar set BHID=u pper(new.BHID) where rowid=new.rowid; 
	end;
*/


/* ___________________________________________________________________
    
    ToDO list 
   ___________________________________________________________________
a) Implement transactions
b) Integrity implementation for gaps and overlap 
c) Extra integrity for Sample_ID duplicated in Assay (!optional)
*/

              
/* ___________________________________________________________________
    
    End of the script
   ___________________________________________________________________
*/
