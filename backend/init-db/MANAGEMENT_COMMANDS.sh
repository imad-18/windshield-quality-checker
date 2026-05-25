#!/bin/bash
# ============================================================================
# MySQL Event Management - Quick Reference Commands
# ============================================================================
# Usage: Copy-paste commands into terminal to manage data retention events
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║           MySQL Data Retention - Management Commands                      ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# =============================================================================
# 1. CHECK EVENT SCHEDULER STATUS
# =============================================================================
echo ""
echo "1️⃣  CHECK EVENT SCHEDULER STATUS"
echo "───────────────────────────────────────────────────────────────────────────"
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT @@global.event_scheduler as 'Event Scheduler Status';"

# =============================================================================
# 2. LIST ALL EVENTS
# =============================================================================
echo ""
echo "2️⃣  LIST ALL EVENTS IN DATABASE"
echo "───────────────────────────────────────────────────────────────────────────"
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT 
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
   ORDER BY CREATED DESC;"

# =============================================================================
# 3. GET EVENT DEFINITION
# =============================================================================
echo ""
echo "3️⃣  GET CLEANUP EVENT DEFINITION"
echo "───────────────────────────────────────────────────────────────────────────"
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SHOW CREATE EVENT windshield_db.cleanup_old_test_records\G"

# =============================================================================
# 4. CHECK RECORD COUNTS
# =============================================================================
echo ""
echo "4️⃣  CHECK RECORD COUNTS"
echo "───────────────────────────────────────────────────────────────────────────"
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT 
     (SELECT COUNT(*) FROM windshield_tests) as 'Total Records',
     (SELECT COUNT(*) FROM windshield_tests WHERE created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)) as 'Recent (< 3 months)',
     (SELECT COUNT(*) FROM windshield_tests WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH)) as 'Expired (> 3 months)',
     (SELECT COUNT(*) FROM windshield_tests WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH) AND created_at >= DATE_SUB(NOW(), INTERVAL 4 MONTH)) as 'Next to Expire (3-4 months)';"

# =============================================================================
# 5. VIEW OLDEST & NEWEST RECORDS
# =============================================================================
echo ""
echo "5️⃣  VIEW OLDEST & NEWEST RECORDS"
echo "───────────────────────────────────────────────────────────────────────────"
docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \
  "SELECT 'OLDEST' as Type, id, tension, result, created_at FROM windshield_tests ORDER BY created_at ASC LIMIT 1
   UNION ALL
   SELECT 'NEWEST' as Type, id, tension, result, created_at FROM windshield_tests ORDER BY created_at DESC LIMIT 1;"

# =============================================================================
# 6. ENABLE EVENT SCHEDULER (if disabled)
# =============================================================================
echo ""
echo "6️⃣  ENABLE EVENT SCHEDULER (run if needed)"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Command:"
echo "  docker-compose exec mysql mysql -u root -pimad0003 -e \"SET GLOBAL event_scheduler = ON;\""

# =============================================================================
# 7. ENABLE/DISABLE SPECIFIC EVENT
# =============================================================================
echo ""
echo "7️⃣  ENABLE/DISABLE CLEANUP EVENT"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Enable:"
echo "  docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \"ALTER EVENT cleanup_old_test_records ENABLE;\""
echo ""
echo "Disable:"
echo "  docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \"ALTER EVENT cleanup_old_test_records DISABLE;\""

# =============================================================================
# 8. BACKUP DATABASE (before cleanup verification)
# =============================================================================
echo ""
echo "8️⃣  BACKUP DATABASE"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Command:"
echo "  docker-compose exec mysql mysqldump -u root -pimad0003 windshield_db > backup_windshield_\$(date +%Y%m%d_%H%M%S).sql"

# =============================================================================
# 9. TEST CLEANUP (Force manual execution)
# =============================================================================
echo ""
echo "9️⃣  TEST CLEANUP - SIMULATE EXECUTION"
echo "───────────────────────────────────────────────────────────────────────────"
echo "View records that would be deleted:"
echo "  docker-compose exec mysql mysql -u root -pimad0003 windshield_db -e \"SELECT COUNT(*) as records_to_delete FROM windshield_tests WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);\""

# =============================================================================
# 10. CONTAINER LOGS
# =============================================================================
echo ""
echo "🔟  VIEW CONTAINER LOGS"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Last 50 lines:"
echo "  docker-compose logs mysql | tail -50"
echo ""
echo "Search for EVENT-related logs:"
echo "  docker-compose logs mysql | grep -i event"
echo ""
echo "Real-time logs:"
echo "  docker-compose logs -f mysql"

# =============================================================================
# 11. VERIFY INITIALIZATION SCRIPT
# =============================================================================
echo ""
echo "1️⃣1️⃣  VERIFY INITIALIZATION SCRIPT IN CONTAINER"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Command:"
echo "  docker-compose exec mysql ls -la /docker-entrypoint-initdb.d/"

# =============================================================================
# 12. REINITIALIZE CONTAINER (DANGER - DELETES DATA)
# =============================================================================
echo ""
echo "1️⃣2️⃣  REINITIALIZE CONTAINER (⚠️  DELETES ALL DATA)"
echo "───────────────────────────────────────────────────────────────────────────"
echo "Commands:"
echo "  docker-compose down -v"
echo "  docker-compose up -d"
echo ""
echo "⚠️  WARNING: This will delete all existing data in mysql_data volume!"

echo ""
echo "╚════════════════════════════════════════════════════════════════════════════╝"
