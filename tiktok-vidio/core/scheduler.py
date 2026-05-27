import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
from .config import ScheduleConfig


class TaskScheduler:
    DAY_MAP = {
        "monday": schedule.every().monday,
        "tuesday": schedule.every().tuesday,
        "wednesday": schedule.every().wednesday,
        "thursday": schedule.every().thursday,
        "friday": schedule.every().friday,
        "saturday": schedule.every().saturday,
        "sunday": schedule.every().sunday,
    }

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None
        self._current_jobs = []

    def set_callback(self, callback: Callable):
        self._callback = callback

    def update_schedule(self, config: ScheduleConfig):
        schedule.clear()
        self._current_jobs = []

        if not config.enabled or not self._callback:
            return

        time_str = config.time
        for day in config.days:
            if day.lower() in self.DAY_MAP:
                job = self.DAY_MAP[day.lower()].at(time_str).do(self._execute_task)
                self._current_jobs.append(job)

    def _execute_task(self):
        if self._callback:
            try:
                self._callback()
            except Exception as e:
                print(f"执行任务失败: {e}")

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(30)

    def get_next_run(self) -> Optional[datetime]:
        jobs = schedule.get_jobs()
        if not jobs:
            return None

        next_times = []
        for job in jobs:
            if job.next_run:
                next_times.append(job.next_run)

        return min(next_times) if next_times else None

    def get_status(self) -> dict:
        next_run = self.get_next_run()
        return {
            "running": self._running,
            "jobs_count": len(self._current_jobs),
            "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "无",
        }
