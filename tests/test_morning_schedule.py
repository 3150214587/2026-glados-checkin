from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
import unittest

import morning_schedule as schedule


class MorningScheduleTests(unittest.TestCase):
    def test_exactly_one_slot_each_day_for_a_year(self):
        selected = set()
        for offset in range(366):
            day = date(2026, 1, 1) + timedelta(days=offset)
            winners = []
            for cron in schedule.SCHEDULES:
                minute, hour, *_ = cron.split()
                now = datetime(day.year, day.month, day.day, int(hour) + 8, int(minute), tzinfo=schedule.LOCAL_TZ)
                if schedule.should_run('schedule', cron, now, 'owner/repo'):
                    winners.append(cron)
            self.assertEqual(len(winners), 1)
            self.assertEqual(winners[0], schedule.selected_schedule(day, 'owner/repo'))
            selected.add(winners[0])
        self.assertEqual(selected, set(schedule.SCHEDULES))

    def test_delays_outside_morning_are_skipped(self):
        day = date(2026, 11, 12)
        cron = schedule.selected_schedule(day, 'owner/repo')
        for hour in (0, 8, 12, 16, 23):
            now = datetime(2026, 11, 12, hour, tzinfo=schedule.LOCAL_TZ)
            self.assertFalse(schedule.should_run('schedule', cron, now, 'owner/repo'))

    def test_manual_runs_bypass_selection_and_unknown_events_do_not(self):
        now = datetime(2026, 11, 12, 18, tzinfo=timezone.utc)
        self.assertTrue(schedule.should_run('workflow_dispatch', '', now, 'owner/repo'))
        self.assertFalse(schedule.should_run('push', '', now, 'owner/repo'))

    def test_workflow_has_the_same_candidate_slots(self):
        path = Path(__file__).resolve().parents[1] / '.github/workflows/checkin.yml'
        crons = re.findall(r"cron: '([^']+)'", path.read_text(encoding='utf-8'))
        self.assertEqual(crons, list(schedule.SCHEDULES))
