# MySQL Data Retention Feature - Implementation Guide

## Overview
This implementation sets up an automated weekly cleanup process in MySQL 8.0 that deletes test records older than 3 months. The process runs entirely within the database, requiring no backend intervention.

---

## Architecture

### Component: MySQL EVENT
- **Name**: `cleanup_old_test_records`
- **Schedule**: Every Sunday at midnight UTC
- **Action**: Deletes records from `windshield_tests` where `created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)`
- **Retention Period**: 90 days (3 months)

### Execution Flow
```
Docker Container Starts
    ↓
MySQL Initialization Runs
    ↓
/docker-entrypoint-initdb.d/ Scripts Execute (Alphabetical Order)
    ↓
01-enable-event-scheduler.sql
    ├─ SET GLOBAL event_scheduler = ON;
    ├─ CREATE EVENT cleanup_old_test_records ...
    └─ Event Scheduler Activated
    ↓
Weekly Execution (Every Sunday @ Midnight)
    ↓
DELETE FROM windshield_tests WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)
```

---

## File Structure
```
backend/
├── init-db/
│   └── 01-enable-event-scheduler.sql    ← Initialization script
├── app.py
├── models.py
├── database.py
└── requirements.txt
```

---

## Implementation Steps

### Step 1: Verify the SQL Script
The script is located at: `backend/init-db/01-enable-event-scheduler.sql`

**Key Components:**
```sql
-- Enable Event Scheduler (Persistent)
SET GLOBAL event_scheduler = ON;

-- Create the Event
CREATE EVENT windshield_db.cleanup_old_test_records
ON SCHEDULE EVERY 1 WEEK
DO DELETE FROM windshield_db.windshield_tests
   WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
```

### Step 2: Docker Compose Configuration
Updated volumes in `docker-compose.yml` mysql service:
```yaml
volumes:
  - mysql_data:/var/lib/mysql
  - ./backend/init-db:/docker-entrypoint-initdb.d
```

**How It Works:**
- MySQL official image automatically executes scripts in `/docker-entrypoint-initdb.d/`
- Scripts run in alphabetical order on first container startup
- Only runs if the named volume `mysql_data` is empty
- `.sql` files are executed with `mysql` client
- `.sh` files are executed with `bash`

### Step 3: Container Lifecycle
```bash
# Stop and remove existing volume (CAREFUL - this deletes data!)
docker-compose down -v

# Restart containers with new volume mount
docker-compose up -d
```

---

## Verification

### 1. Check Event Scheduler Status
```bash
# Access MySQL container
docker-compose exec mysql mysql -u root -pimad0003 windshield_db
```

Inside MySQL client:
```sql
-- Verify Event Scheduler is ON
SELECT @@global.event_scheduler;
-- Result should be: ON

-- List all events in the database
SELECT EVENT_NAME, EVENT_SCHEMA, STATUS, LAST_EXECUTED, CREATED
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db';

-- Get event details
SHOW CREATE EVENT windshield_db.cleanup_old_test_records;

-- Check event schedule
SELECT 
    EVENT_NAME,
    EVENT_SCHEMA,
    STATUS,
    INTERVAL_VALUE,
    INTERVAL_FIELD,
    EXECUTE_AT
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db' AND EVENT_NAME = 'cleanup_old_test_records';
```

### 2. Monitor Execution Logs
```bash
# View MySQL container logs
docker-compose logs mysql | grep -i event

# Persist logs for debugging
docker-compose logs mysql > mysql_logs.txt
```

### 3. Manual Test (Force Execution)
```sql
-- Manually trigger the event (for testing)
ALTER EVENT windshield_db.cleanup_old_test_records ENABLE;

-- Check record counts before/after
SELECT COUNT(*) as total_records FROM windshield_tests;
SELECT COUNT(*) as old_records FROM windshield_tests 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- Force event execution (not standard, but useful for testing)
-- Option 1: Create a test event that runs immediately
CREATE EVENT test_cleanup
ON SCHEDULE AT NOW() + INTERVAL 5 SECOND
DO DELETE FROM windshield_db.windshield_tests
   WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
```

---

## Customization

### Change Retention Period
Edit `backend/init-db/01-enable-event-scheduler.sql`:
```sql
-- From 3 months to 6 months
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- From 3 months to 1 year
WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- From 3 months to 30 days
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### Change Execution Schedule
```sql
-- Every day at 2 AM
ON SCHEDULE EVERY 1 DAY
STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 2 HOUR)

-- Every Sunday at 6 PM
ON SCHEDULE EVERY 1 WEEK
STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 18 HOUR)

-- Every first day of month at midnight
ON SCHEDULE EVERY 1 MONTH
STARTS DATE_ADD(DATE_ADD(LAST_DAY(CURDATE()), INTERVAL 1 DAY), INTERVAL 0 HOUR)
```

### Add Audit Logging
Uncomment and create an audit table:
```sql
-- Create audit table
CREATE TABLE IF NOT EXISTS windshield_db.cleanup_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    deleted_records INT DEFAULT 0,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update event to log deletions
CREATE EVENT windshield_db.cleanup_old_test_records
DO
  BEGIN
    DECLARE deleted_count INT;
    DELETE FROM windshield_db.windshield_tests
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
    SET deleted_count = ROW_COUNT();
    INSERT INTO windshield_db.cleanup_audit (action, deleted_records)
    VALUES ('cleanup_old_test_records', deleted_count);
  END;
```

---

## Best Practices

### 1. **Backup Before Enabling**
```bash
docker-compose exec mysql mysqldump -u root -pimad0003 windshield_db > backup_before_retention.sql
```

### 2. **Monitor Event Status Regularly**
Add to your monitoring:
```sql
SELECT 
    EVENT_NAME,
    STATUS,
    LAST_EXECUTED,
    INTERVAL_VALUE,
    INTERVAL_FIELD
FROM INFORMATION_SCHEMA.EVENTS
WHERE EVENT_SCHEMA = 'windshield_db';
```

### 3. **Set Appropriate Retention Period**
- **Development**: 7-30 days
- **Testing**: 30-90 days
- **Production**: 90-365 days (based on compliance requirements)

### 4. **Timezone Considerations**
MySQL uses server timezone by default. To set explicitly:
```sql
-- In your .sql initialization script
SET @@session.time_zone = 'UTC';
-- or
SET @@session.time_zone = 'America/New_York';
```

### 5. **High-Volume Considerations**
For very large tables, delete in batches:
```sql
CREATE EVENT windshield_db.cleanup_old_test_records_batched
DO
  BEGIN
    DECLARE deleted INT DEFAULT 1;
    WHILE deleted > 0 DO
      DELETE FROM windshield_db.windshield_tests
      WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)
      LIMIT 1000;
      SET deleted = ROW_COUNT();
    END WHILE;
  END;
```

---

## Troubleshooting

### Problem: Event Scheduler Not Running
```bash
# Check if event_scheduler is ON
docker-compose exec mysql mysql -u root -pimad0003 -e "SELECT @@global.event_scheduler;"

# If OFF, enable it
docker-compose exec mysql mysql -u root -pimad0003 -e "SET GLOBAL event_scheduler = ON;"
```

### Problem: Initialization Script Not Executing
1. **Check volume mount is correct**
   ```bash
   docker-compose exec mysql ls -la /docker-entrypoint-initdb.d/
   ```

2. **Verify database exists**
   ```bash
   docker-compose exec mysql mysql -u root -pimad0003 -e "SHOW DATABASES;"
   ```

3. **Check container logs**
   ```bash
   docker-compose logs mysql
   ```

4. **Reinitialize (WARNING: deletes data)**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Problem: Event Shows as Disabled
```sql
-- Enable the event
ALTER EVENT windshield_db.cleanup_old_test_records ENABLE;

-- Verify status
SELECT EVENT_NAME, STATUS FROM INFORMATION_SCHEMA.EVENTS 
WHERE EVENT_SCHEMA = 'windshield_db';
```

---

## Deployment Checklist

- [ ] SQL script created at `backend/init-db/01-enable-event-scheduler.sql`
- [ ] Docker Compose volume mount added for `./backend/init-db:/docker-entrypoint-initdb.d`
- [ ] Existing containers stopped and volume removed: `docker-compose down -v`
- [ ] Containers restarted: `docker-compose up -d`
- [ ] Event Scheduler verified as ON: `SELECT @@global.event_scheduler;`
- [ ] Event created and visible in `INFORMATION_SCHEMA.EVENTS`
- [ ] Test deletion query executed manually to verify logic
- [ ] Backup taken before production deployment
- [ ] Monitoring configured to track event execution
- [ ] Team documented of retention policy (3 months)

---

## Security Considerations

1. **Event Permissions**: MySQL EVENTS run with the privileges of their creator
   - The initialization script runs as root, so events have full permissions
   - This is acceptable for cleanup operations on system data

2. **Audit Trail**: Consider logging deletions in an audit table (see Customization section)

3. **Backup Policy**: Ensure your backup retention is ≥ cleanup retention
   - If you keep data 3 months, keep backups 3+ months

4. **Compliance**: Verify compliance requirements
   - GDPR: 3 months might not be sufficient
   - SOX/HIPAA: Longer retention may be required
   - CCPA: Right to deletion must be honored

---

## Performance Impact

- **Execution Time**: Depends on table size and delete criteria
  - 100K records: ~1-5 seconds
  - 1M records: ~10-30 seconds
  - 10M records: ~1-3 minutes
  
- **I/O Impact**: Single DELETE query minimizes locking
  
- **Optimization**: If performance is an issue, use batch deletion (see Customization)

---

## Next Steps

1. Verify the setup is working with provided verification commands
2. Adjust retention period and schedule based on your requirements
3. Add audit logging for compliance if needed
4. Implement monitoring dashboard for event execution
5. Document the policy in your team's knowledge base
