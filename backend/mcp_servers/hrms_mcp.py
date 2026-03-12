import uuid
from datetime import datetime, date, timedelta
from backend.mcp_servers.base_mcp import BaseMCPServer
from backend.database.sqlite_manager import get_connection, get_store_schedules


class HRMSMCPServer(BaseMCPServer):
    def __init__(self):
        super().__init__("HRMS_MCP")

    def get_store_schedule(self, store_id, date_str=None):
        if not date_str:
            date_str = date.today().isoformat()
        schedules = get_store_schedules(store_id, date_str)
        pharmacist_hours = self._calculate_pharmacist_coverage(schedules)
        gaps = self._identify_gaps(schedules, pharmacist_hours)
        return self._success("get_store_schedule", {
            "store_id": store_id,
            "date": date_str,
            "schedules": schedules,
            "total_staff": len(schedules),
            "pharmacist_coverage_hours": pharmacist_hours,
            "compliance_gaps": gaps
        }, store_id)

    def get_weekly_schedule(self, store_id):
        schedules_by_day = {}
        for i in range(7):
            day = (date.today() + timedelta(days=i)).isoformat()
            schedules_by_day[day] = get_store_schedules(store_id, day)
        return self._success("get_weekly_schedule", {
            "store_id": store_id,
            "schedules": schedules_by_day
        }, store_id)

    def create_schedule_adjustment(
        self, store_id, staff_id, date_str, shift_start, shift_end, reason
    ):
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM staff_schedules WHERE store_id = ? AND staff_id = ? LIMIT 1",
            (store_id, staff_id)
        )
        staff = c.fetchone()
        schedule_id = str(uuid.uuid4())
        staff_name = dict(staff)["staff_name"] if staff else "Staff {}".format(staff_id)
        is_pharm = dict(staff)["is_registered_pharmacist"] if staff else 0
        role = dict(staff)["role"] if staff else "Pharmacy Assistant"
        c.execute("""
            INSERT INTO staff_schedules
            (schedule_id, store_id, staff_id, staff_name, role,
             is_registered_pharmacist, shift_date, shift_start, shift_end, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule_id, store_id, staff_id, staff_name, role, is_pharm,
            date_str, shift_start, shift_end, "adjusted"
        ))
        conn.commit()
        conn.close()
        return self._success("create_schedule_adjustment", {
            "schedule_id": schedule_id,
            "store_id": store_id,
            "staff_id": staff_id,
            "date": date_str,
            "shift": "{}-{}".format(shift_start, shift_end),
            "reason": reason,
        }, store_id)

    def flag_compliance_breach(self, store_id, date_str, time_window, gap_type):
        breach_id = "COMP-{}".format(uuid.uuid4().hex[:8].upper())
        return self._success("flag_compliance_breach", {
            "breach_id": breach_id,
            "store_id": store_id,
            "date": date_str,
            "time_window": time_window,
            "gap_type": gap_type,
            "flagged_at": datetime.now().isoformat(),
            "regulatory_reference": "Drugs and Cosmetics Act 1940 Schedule H"
        }, store_id)

    def _calculate_pharmacist_coverage(self, schedules):
        covered_hours = set()
        for s in schedules:
            if s.get("is_registered_pharmacist"):
                try:
                    start_h = int(s["shift_start"].split(":")[0])
                    end_h = int(s["shift_end"].split(":")[0])
                    for h in range(start_h, end_h):
                        covered_hours.add(h)
                except (ValueError, KeyError):
                    pass
        return sorted(["{:02d}:00".format(h) for h in covered_hours])

    def _identify_gaps(self, schedules, covered_hours):
        gaps = []
        covered_set = {int(h.split(":")[0]) for h in covered_hours}
        for h in range(8, 22):
            if h not in covered_set:
                gaps.append({
                    "time": "{:02d}:00".format(h),
                    "gap_type": "NO_REGISTERED_PHARMACIST",
                    "severity": "CRITICAL",
                    "schedule_h_risk": True
                })
        return gaps