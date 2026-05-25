-- ============================================================================
-- WINDSHIELD DATABASE INITIALIZATION - DATA RETENTION SETUP (TEST MODE)
-- ============================================================================
-- Purpose: Enable MySQL Event Scheduler and create a fast-running EVENT for testing
-- This script runs automatically on MySQL container initialization
-- ============================================================================

-- Step 1: Enable the Global Event Scheduler
SET GLOBAL event_scheduler = ON;

-- Step 2: Create the Data Retention Event (TEST MODE)
-- Drops existing event if it exists (idempotent)
DROP EVENT IF EXISTS windshield_db.cleanup_old_test_records;

DELIMITER $$

-- Create the event to delete records older than 5 days
-- RUNS CONTINUOUSLY EVERY 10 SECONDS FOR TESTING
CREATE EVENT windshield_db.cleanup_old_test_records
ON SCHEDULE
  EVERY 10 SECOND
  STARTS CURRENT_TIMESTAMP
DO
  BEGIN
    -- Delete all test records older than 5 days (for testing purposes)
    DELETE FROM windshield_db.windshield_tests
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 5 MINUTE);
  END$$

DELIMITER ;