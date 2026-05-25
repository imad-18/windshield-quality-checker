-- ============================================================================
-- MySQL Data Retention - SQL Reference Guide
-- ============================================================================
-- Usage: These are example queries for various retention scenarios
-- Customize retention periods, schedules, and table names as needed
-- ============================================================================

-- ============================================================================
-- SECTION 1: CORE RETENTION QUERIES (PRODUCTION SETUP)
-- ============================================================================

-- Enable Event Scheduler (GLOBAL, persistent)
SET GLOBAL event_scheduler = ON;

-- Verify Event Scheduler Status
SELECT @@global.event_scheduler;
-- Expected: ON (or 1)

-- ============================================================================
-- SECTION 2: CREATE EVENTS WITH DIFFERENT RETENTION PERIODS
-- ============================================================================

-- ─────────────────────────────────────────────────────────────────────────
-- Event 1: Delete records older than 3 months (90 days) - WEEKLY
-- ─────────────────────────────────────────────────────────────────────────
DROP EVENT IF EXISTS windshield_db.cleanup_old_test_records;

CREATE EVENT windshield_db.cleanup_old_test_records
ON SCHEDULE EVERY 1 WEEK
STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 0 HOUR)
DO
  BEGIN
    DELETE FROM windshield_db.windshield_tests
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
  END;

-- ─────────────────────────────────────────────────────────────────────────
-- Event 2: Alternative - Delete records older than 6 months - MONTHLY
-- ─────────────────────────────────────────────────────────────────────────
-- DROP EVENT IF EXISTS windshield_db.cleanup_old_test_records_6m;
-- CREATE EVENT windshield_db.cleanup_old_test_records_6m
-- ON SCHEDULE EVERY 1 MONTH
-- DO
--   BEGIN
--     DELETE FROM windshield_db.windshield_tests
--     WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
--   END;

-- ─────────────────────────────────────────────────────────────────────────
-- Event 3: Alternative - Delete records older than 1 year - QUARTERLY
-- ─────────────────────────────────────────────────────────────────────────
-- DROP EVENT IF EXISTS windshield_db.cleanup_old_test_records_1y;
-- CREATE EVENT windshield_db.cleanup_old_test_records_1y
-- ON SCHEDULE EVERY 3 MONTH
-- DO
--   BEGIN
--     DELETE FROM windshield_db.windshield_tests
--     WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
--   END;

-- ============================================================================
-- SECTION 3: SCHEDULE VARIATIONS
-- ============================================================================

-- Every DAY at 2 AM UTC
-- ON SCHEDULE EVERY 1 DAY
-- STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 2 HOUR)

-- Every SUNDAY at midnight UTC
-- ON SCHEDULE EVERY 1 WEEK
-- STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 0 HOUR)

-- Every FIRST DAY of month at midnight UTC
-- ON SCHEDULE EVERY 1 MONTH
-- STARTS DATE_ADD(DATE_ADD(LAST_DAY(CURDATE()), INTERVAL 1 DAY), INTERVAL 0 HOUR)

-- Every FRIDAY at 6 PM UTC
-- ON SCHEDULE EVERY 1 WEEK STARTS '2026-05-29 18:00:00'
-- (where 2026-05-29 is a Friday)

-- Once at a specific time (useful for testing)
-- ON SCHEDULE AT '2026-05-26 00:00:00'

-- ============================================================================
-- SECTION 4: MONITORING QUERIES
-- ============================================================================

-- Check if Event Scheduler is enabled
SELECT @@global.event_scheduler;

-- List all events
SELECT 
    EVENT_NAME,
    EVENT_SCHEMA,
    STATUS,
    INTERVAL_VALUE,
    INTERVAL_FIELD,
    CREATED,
    LAST_EXECUTED,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db'
ORDER BY EVENT_NAME;

-- Get specific event details
SELECT 
    EVENT_NAME,
    EVENT_SCHEMA,
    STATUS,
    EVENT_TYPE,
    EXECUTE_AT,
    INTERVAL_VALUE,
    INTERVAL_FIELD,
    STARTS,
    ENDS,
    CREATED,
    LAST_EXECUTED,
    LAST_ALTERED,
    DEFINER
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db' 
  AND EVENT_NAME = 'cleanup_old_test_records';

-- View event definition
SHOW CREATE EVENT windshield_db.cleanup_old_test_records;

-- ============================================================================
-- SECTION 5: DATA ANALYSIS - BEFORE CLEANUP
-- ============================================================================

-- Total count of all records
SELECT COUNT(*) as total_records FROM windshield_db.windshield_tests;

-- Records that will be deleted (older than 3 months)
SELECT COUNT(*) as records_to_delete 
FROM windshield_db.windshield_tests
WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- Records that will be kept (less than 3 months old)
SELECT COUNT(*) as records_to_keep 
FROM windshield_db.windshield_tests
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- Breakdown by age range
SELECT 
    'Today' as time_period,
    COUNT(*) as count
FROM windshield_db.windshield_tests
WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
UNION ALL
SELECT 'Last 7 days',
    COUNT(*)
FROM windshield_db.windshield_tests
WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY) 
  AND created_at <= DATE_SUB(NOW(), INTERVAL 1 DAY)
UNION ALL
SELECT 'Last 30 days',
    COUNT(*)
FROM windshield_db.windshield_tests
WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY) 
  AND created_at <= DATE_SUB(NOW(), INTERVAL 7 DAY)
UNION ALL
SELECT 'Last 90 days (3 months)',
    COUNT(*)
FROM windshield_db.windshield_tests
WHERE created_at > DATE_SUB(NOW(), INTERVAL 90 DAY) 
  AND created_at <= DATE_SUB(NOW(), INTERVAL 30 DAY)
UNION ALL
SELECT 'Older than 90 days',
    COUNT(*)
FROM windshield_db.windshield_tests
WHERE created_at <= DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Oldest and newest records
SELECT 
    'OLDEST' as record_type,
    id,
    tension,
    result,
    created_at,
    DATEDIFF(NOW(), created_at) as days_old
FROM windshield_db.windshield_tests
ORDER BY created_at ASC
LIMIT 1
UNION ALL
SELECT 
    'NEWEST',
    id,
    tension,
    result,
    created_at,
    DATEDIFF(NOW(), created_at)
FROM windshield_db.windshield_tests
ORDER BY created_at DESC
LIMIT 1;

-- Distribution by month
SELECT 
    DATE_TRUNC(created_at, MONTH) as month,
    COUNT(*) as record_count
FROM windshield_db.windshield_tests
GROUP BY DATE_TRUNC(created_at, MONTH)
ORDER BY month DESC;

-- ============================================================================
-- SECTION 6: MANUAL CLEANUP (FOR TESTING OR ONE-TIME OPERATIONS)
-- ============================================================================

-- Preview records that will be deleted
SELECT 
    id,
    tension,
    result,
    created_at,
    DATEDIFF(NOW(), created_at) as days_old
FROM windshield_db.windshield_tests
WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)
LIMIT 10;

-- Execute one-time cleanup (careful!)
DELETE FROM windshield_db.windshield_tests
WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- Check how many records were deleted
SELECT ROW_COUNT();

-- ============================================================================
-- SECTION 7: BATCH CLEANUP (FOR LARGE TABLES - PREVENTS LOCKING)
-- ============================================================================

-- Batch delete in chunks of 1000 records
-- Run this as a stored procedure or one-time script
DELIMITER $$

CREATE PROCEDURE cleanup_old_records_batch()
BEGIN
    DECLARE deleted INT DEFAULT 1;
    DECLARE batch_size INT DEFAULT 1000;
    DECLARE total_deleted INT DEFAULT 0;
    
    WHILE deleted > 0 DO
        DELETE FROM windshield_db.windshield_tests
        WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)
        LIMIT batch_size;
        
        SET deleted = ROW_COUNT();
        SET total_deleted = total_deleted + deleted;
        
        -- Small pause between batches to allow concurrent queries
        DO SLEEP(1);
    END WHILE;
    
    SELECT CONCAT('Total records deleted: ', total_deleted) as result;
END $$

DELIMITER ;

-- Call the batch cleanup procedure
CALL cleanup_old_records_batch();

-- ============================================================================
-- SECTION 8: EVENT MANAGEMENT
-- ============================================================================

-- Enable an event
ALTER EVENT windshield_db.cleanup_old_test_records ENABLE;

-- Disable an event
ALTER EVENT windshield_db.cleanup_old_test_records DISABLE;

-- Modify event schedule (run daily instead of weekly)
ALTER EVENT windshield_db.cleanup_old_test_records
ON SCHEDULE EVERY 1 DAY
STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 2 HOUR);

-- Modify event retention period (keep 6 months instead of 3)
ALTER EVENT windshield_db.cleanup_old_test_records
DO
  BEGIN
    DELETE FROM windshield_db.windshield_tests
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
  END;

-- Drop an event
DROP EVENT windshield_db.cleanup_old_test_records;

-- ============================================================================
-- SECTION 9: AUDIT TABLE (FOR TRACKING DELETIONS)
-- ============================================================================

-- Create audit table (optional)
CREATE TABLE IF NOT EXISTS windshield_db.cleanup_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    deleted_count INT DEFAULT 0,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cutoff_date DATETIME,
    INDEX idx_execution_time (execution_time)
);

-- Event with audit logging
-- DROP EVENT IF EXISTS windshield_db.cleanup_old_test_records;
-- CREATE EVENT windshield_db.cleanup_old_test_records
-- ON SCHEDULE EVERY 1 WEEK
-- DO
--   BEGIN
--     DECLARE v_deleted INT;
--     DECLARE v_cutoff DATETIME;
--     
--     SET v_cutoff = DATE_SUB(NOW(), INTERVAL 3 MONTH);
--     
--     DELETE FROM windshield_db.windshield_tests
--     WHERE created_at < v_cutoff;
--     
--     SET v_deleted = ROW_COUNT();
--     
--     INSERT INTO windshield_db.cleanup_audit 
--         (event_name, deleted_count, cutoff_date)
--     VALUES 
--         ('cleanup_old_test_records', v_deleted, v_cutoff);
--   END;

-- Query audit logs
SELECT 
    event_name,
    deleted_count,
    execution_time,
    cutoff_date,
    DATE_FORMAT(execution_time, '%Y-%m-%d %H:%i:%s') as formatted_time
FROM windshield_db.cleanup_audit
ORDER BY execution_time DESC
LIMIT 20;

-- ============================================================================
-- SECTION 10: TIMEZONE HANDLING
-- ============================================================================

-- View current server timezone
SELECT @@global.time_zone, @@session.time_zone;

-- Set session timezone for current connection
SET @@session.time_zone = 'UTC';
SET @@session.time_zone = 'America/New_York';
SET @@session.time_zone = 'Europe/London';
SET @@session.time_zone = '+00:00';

-- Create event with specific timezone (UTC)
-- ON SCHEDULE EVERY 1 WEEK
-- STARTS '2026-05-25 00:00:00' AT TIME ZONE 'UTC'

-- ============================================================================
-- SECTION 11: PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Create index on created_at for faster deletion
CREATE INDEX IF NOT EXISTS idx_created_at 
ON windshield_db.windshield_tests(created_at);

-- Check index statistics
SELECT 
    object_schema,
    object_name,
    index_name,
    count_read,
    count_write,
    count_delete
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema = 'windshield_db'
  AND object_name = 'windshield_tests'
ORDER BY count_read DESC;

-- Monitor event execution performance
SELECT 
    EVENT_NAME,
    STATUS,
    LAST_EXECUTED,
    INTERVAL_VALUE,
    INTERVAL_FIELD
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db';
