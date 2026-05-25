# Data Retention - Quick Start Guide

## ✅ What's Been Set Up

Your MySQL 8.0 database is now configured with an **automatic weekly data cleanup** feature that:
- ✓ Deletes test records older than **3 months**
- ✓ Runs **every Sunday at midnight UTC**
- ✓ Executes entirely within MySQL (no backend involvement)
- ✓ Starts automatically on container initialization

---

## 📁 Files Created

```
backend/init-db/
├── 01-enable-event-scheduler.sql    ← Main setup script (auto-executed by Docker)
├── SQL_REFERENCE.sql                ← SQL query examples & reference
├── DATA_RETENTION_GUIDE.md          ← Detailed documentation
├── MANAGEMENT_COMMANDS.sh           ← Quick reference commands
└── QUICK_START_GUIDE.md            ← This file
```

---

## 🚀 Deploy the Setup

### Option 1: Fresh Start (Recommended - First Time Only)
```bash
cd c:\Users\lenovo\Documents\grindin\claudeCodeProjects

# Stop and remove existing containers and volumes
docker-compose down -v

# Start fresh containers
docker-compose up -d

# Verify setup
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SELECT @@global.event_scheduler as 'Event Scheduler';"
```

### Option 2: Apply to Existing Database
```bash
# Stop containers (keeps data)
docker-compose down

# Start containers with new initialization
docker-compose up -d

# Manually enable event scheduler (if needed)
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SET GLOBAL event_scheduler = ON;"
```

---

## 🔍 Verify Installation

After deploying, run these commands to confirm everything works:

```bash
# 1. Check Event Scheduler is ON
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SELECT @@global.event_scheduler;"
# Expected: ON

# 2. List all events
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT EVENT_NAME, STATUS FROM INFORMATION_SCHEMA.EVENTS;"
# Expected: cleanup_old_test_records | ENABLED

# 3. View event details
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SHOW CREATE EVENT cleanup_old_test_records\G"
```

---

## 📊 Monitor Your Data

### View Records By Age
```bash
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT 
     (SELECT COUNT(*) FROM windshield_tests) as 'Total Records',
     (SELECT COUNT(*) FROM windshield_tests WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)) as 'Recent (< 3 months)',
     (SELECT COUNT(*) FROM windshield_tests WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)) as 'Expired (> 3 months)';"
```

### Find Records That Will Be Deleted Soon
```bash
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT id, tension, result, created_at, DATEDIFF(NOW(), created_at) as days_old 
   FROM windshield_tests 
   WHERE created_at BETWEEN DATE_SUB(NOW(), INTERVAL 4 MONTH) AND DATE_SUB(NOW(), INTERVAL 3 MONTH) 
   ORDER BY created_at;"
```

---

## ⚙️ Customization

### Change Retention Period

Edit `backend/init-db/01-enable-event-scheduler.sql`:

```sql
-- Change from 3 MONTH to:
-- 6 MONTH     (6 months)
-- 1 YEAR      (1 year)
-- 30 DAY      (30 days)

DELETE FROM windshield_db.windshield_tests
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);  -- Change here
```

Then redeploy:
```bash
docker-compose down -v && docker-compose up -d
```

### Change Execution Schedule

```sql
-- Change from "EVERY 1 WEEK" to:
ON SCHEDULE EVERY 1 DAY                    -- Daily
ON SCHEDULE EVERY 1 MONTH                  -- Monthly
ON SCHEDULE EVERY 3 MONTH                  -- Quarterly

-- Specify exact time:
STARTS DATE_ADD(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 2 HOUR)  -- 2 AM
```

---

## 📋 Command Reference

### Core Commands
```bash
# Check Event Scheduler
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SELECT @@global.event_scheduler;"

# Enable Event Scheduler
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SET GLOBAL event_scheduler = ON;"

# Disable Event Scheduler
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SET GLOBAL event_scheduler = OFF;"

# Enable cleanup event
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "ALTER EVENT cleanup_old_test_records ENABLE;"

# Disable cleanup event
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "ALTER EVENT cleanup_old_test_records DISABLE;"

# Backup database
docker-compose exec mysql mysqldump -u root -pimad0003 windshield_db > \
  backup_windshield_$(date +%Y%m%d_%H%M%S).sql

# View container logs
docker-compose logs mysql | tail -100
```

---

## 🧪 Test the Cleanup Process

### Manual Test (Non-Destructive)
```bash
# View what WOULD be deleted
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT COUNT(*) as 'Records that will be deleted' 
   FROM windshield_tests 
   WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);"
```

### Create Test Data (For Testing)
```sql
-- Insert old test record
INSERT INTO windshield_tests (tension, final_intensity, final_resistance, result, created_at)
VALUES (100.5, 50.2, 75.8, 'OK', DATE_SUB(NOW(), INTERVAL 4 MONTH));

-- Verify it will be deleted
SELECT COUNT(*) FROM windshield_tests 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);
```

---

## 🔒 Security & Best Practices

### ✓ Backup Before Any Cleanup
```bash
docker-compose exec mysql mysqldump -u root -pimad0003 windshield_db > \
  pre-cleanup-backup.sql
```

### ✓ Monitor Execution
```bash
# Check last execution time
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SELECT EVENT_NAME, LAST_EXECUTED FROM INFORMATION_SCHEMA.EVENTS;"

# View container logs for errors
docker-compose logs mysql | grep -i "event\|error"
```

### ✓ Verify Retention Policy
- Development: 7-30 days
- Testing: 30-90 days
- Production: 90-365 days (based on compliance needs)

---

## ❓ Troubleshooting

### Event Scheduler Not Running
```bash
# Check if it's ON
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SELECT @@global.event_scheduler;"

# If OFF, enable it
docker-compose exec mysql mysql -u root -pimad0003 -e \
  "SET GLOBAL event_scheduler = ON;"

# Restart MySQL service
docker-compose restart mysql
```

### Initialization Script Not Running
```bash
# Check if file exists in container
docker-compose exec mysql ls -la /docker-entrypoint-initdb.d/

# Check MySQL logs
docker-compose logs mysql

# Note: Init scripts only run on first container startup
# To re-run: docker-compose down -v && docker-compose up -d
```

### Need to Disable Cleanup Temporarily
```bash
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "ALTER EVENT cleanup_old_test_records DISABLE;"

# Re-enable when ready
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "ALTER EVENT cleanup_old_test_records ENABLE;"
```

---

## 📚 Documentation

- **SQL_REFERENCE.sql** - Comprehensive SQL examples and variations
- **DATA_RETENTION_GUIDE.md** - Detailed documentation with all customization options
- **MANAGEMENT_COMMANDS.sh** - Quick reference for common operations
- **01-enable-event-scheduler.sql** - The actual initialization script

---

## 🎯 Next Steps

1. ✅ Deploy the setup (see "🚀 Deploy the Setup" above)
2. ✅ Run verification commands (see "🔍 Verify Installation" above)
3. ✅ Monitor data cleanup with verification queries (see "📊 Monitor Your Data")
4. ✅ Customize retention period if needed (see "⚙️ Customization")
5. ✅ Set up monitoring/alerts for production (optional)
6. ✅ Document policy in your team's knowledge base

---

## 📞 Quick Support

| Issue | Solution |
|-------|----------|
| Event not running | Check `@@global.event_scheduler = ON` |
| Cleanup not happening | Verify event `STATUS = ENABLED` in `INFORMATION_SCHEMA.EVENTS` |
| Need to test cleanup | Use "TEST CLEANUP" command from reference section |
| Want to change retention | Edit `01-enable-event-scheduler.sql` and redeploy |
| Need audit logging | See "AUDIT TABLE" section in SQL_REFERENCE.sql |
| Performance concerns | See "BATCH CLEANUP" section in SQL_REFERENCE.sql |

---

## 📝 Quick Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs mysql

# Access MySQL CLI
docker-compose exec mysql mysql -u root -pimad0003 windshield_db

# Stop and delete everything (CAREFUL!)
docker-compose down -v
```

---

**Your data retention is now set up and ready! 🎉**

The cleanup event will run automatically every Sunday at midnight. You don't need to do anything else unless you want to customize the retention period or schedule.
