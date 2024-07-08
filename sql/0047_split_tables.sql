-- Crear la tabla DOMAINS
CREATE TABLE IF NOT EXISTS DOMAINS (
    DOMAIN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DOMAIN TEXT,
    COMPANY TEXT,
    YEAR_FOUNDER INTEGER,
    EMPLOYEES TEXT,
    HQ TEXT,
    ANNUAL_REVENUE TEXT,
    INDUSTRY TEXT,
    UPDATE_DATE DATE
);
\
-- Llenar la tabla DOMAINS con dominios únicos
INSERT INTO DOMAINS (DOMAIN)
SELECT DISTINCT DOMAIN FROM SIMILARWEB_RECORDS;
\
-- Crear una nueva tabla SIMILARWEB_RECORDS_NEW
CREATE TABLE IF NOT EXISTS SIMILARWEB_RECORDS_NEW (
    RECORD_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DOMAIN_ID INTEGER,
    GLOBAL_RANK INTEGER,
    COUNTRY_RANK INTEGER,
    CATEGORY_RANK INTEGER,
    TOTAL_VISITS TEXT,
    BOUNCE_RATE INTEGER,
    PAGES_PER_VISIT NUMBER,
    AVG_DURATION_VISIT TEXT,
    UPDATE_DATE DATE
);
\
-- Llenar la tabla SIMILARWEB_RECORDS_NEW con los IDs de dominio
INSERT INTO SIMILARWEB_RECORDS_NEW (DOMAIN_ID, GLOBAL_RANK, COUNTRY_RANK, CATEGORY_RANK, TOTAL_VISITS, BOUNCE_RATE, PAGES_PER_VISIT, AVG_DURATION_VISIT, UPDATE_DATE)
SELECT D.DOMAIN_ID, S.GLOBAL_RANK, S.COUNTRY_RANK, S.CATEGORY_RANK, S.TOTAL_VISITS, S.BOUNCE_RATE, S.PAGES_PER_VISIT, S.AVG_DURATION_VISIT, S.UPDATE_DATE
FROM SIMILARWEB_RECORDS S
INNER JOIN DOMAINS D ON S.DOMAIN = D.DOMAIN;
\
-- Eliminar la tabla SIMILARWEB_RECORDS original
DROP TABLE SIMILARWEB_RECORDS;
\
-- Renombrar SIMILARWEB_RECORDS_NEW a SIMILARWEB_RECORDS
ALTER TABLE SIMILARWEB_RECORDS_NEW RENAME TO SIMILARWEB_RECORDS;
\
-- Renombro la tabla
ALTER TABLE DOMAINS RENAME TO SIMILARWEB_DOMAINS;