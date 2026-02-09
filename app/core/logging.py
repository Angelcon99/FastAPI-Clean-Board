import logging
import contextvars
import os
from logging.handlers import RotatingFileHandler

# --- 재진입 방지 플래그 ---
_LOGGING_CONFIGURED = False

current_trace_id = contextvars.ContextVar("current_trace_id", default=None)

class TraceIdFilter(logging.Filter):
     def filter(self, record: logging.LogRecord) -> bool:        
        tid = getattr(record, "trace_id", None)
        if not tid:            
            tid = current_trace_id.get()
        record.trace_id = tid or "-"
        return True
    
def _ensure_log_dir(path: str = "logs"):
    os.makedirs(path, exist_ok=True)

def setup_logging():
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    _LOGGING_CONFIGURED = True

    _ensure_log_dir()

    trace_filter = TraceIdFilter()
    
    default_fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s | trace_id=%(trace_id)s"
    )
    access_fmt = logging.Formatter(
        "[%(asctime)s] %(message)s | trace_id=%(trace_id)s"
    )

    # --- 공용 핸들러 (앱 전용) ---
    app_console = logging.StreamHandler()
    app_console.setFormatter(default_fmt)
    app_console.addFilter(trace_filter)

    app_file = RotatingFileHandler(
        "logs/app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    app_file.setFormatter(default_fmt)
    app_file.addFilter(trace_filter)

    # --- access 전용 핸들러 ---
    access_console = logging.StreamHandler()
    access_console.setFormatter(access_fmt)
    access_console.addFilter(trace_filter)

    access_file = RotatingFileHandler(
        "logs/access.log",
        maxBytes=10_000_000, 
        backupCount=5, 
        encoding="utf-8"
    )
    access_file.setFormatter(access_fmt)
    access_file.addFilter(trace_filter)

    # --- timing 전용 핸들러 ---
    timing_file = RotatingFileHandler(
        "logs/timing.log", 
        maxBytes=5_000_000,
        backupCount=5, 
        encoding="utf-8"
    )
    timing_file.setFormatter(default_fmt)
    timing_file.addFilter(trace_filter)
    
    # --- scheduler 전용 핸들러 ---
    scheduler_file = RotatingFileHandler(
        "logs/scheduler.log", 
        maxBytes=5_000_000, 
        backupCount=5, 
        encoding="utf-8"
    )
    scheduler_file.setFormatter(default_fmt)
    scheduler_file.addFilter(trace_filter)
    
    
    # --- 루트 로거(앱 전반) ---
    root_logger = logging.getLogger("")
    root_logger.setLevel(logging.INFO)    
    root_logger.handlers.clear()
    root_logger.addHandler(app_console)
    root_logger.addHandler(app_file)
    
    # --- app.access ---
    access_logger = logging.getLogger("app.access")
    access_logger.setLevel(logging.INFO)
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.addHandler(access_console)
    access_logger.addHandler(access_file)

    # --- app.timing ---
    timing_logger = logging.getLogger("app.timing")
    timing_logger.setLevel(logging.INFO)
    timing_logger.handlers.clear()
    timing_logger.propagate = False
    timing_logger.addHandler(timing_file)


    # --- core.scheduler ---
    # core/scheduler.py에서 logging.getLogger(__name__)을 쓰면 이름이 "core.scheduler"가 된다니에!
    scheduler_logic_logger = logging.getLogger("core.scheduler")
    scheduler_logic_logger.setLevel(logging.INFO)
    scheduler_logic_logger.handlers.clear()
    scheduler_logic_logger.propagate = False
    scheduler_logic_logger.addHandler(scheduler_file)
    scheduler_logic_logger.addHandler(app_console) # 콘솔에서도 보고 싶으면 추가!
    
    apscheduler_lib_logger = logging.getLogger("apscheduler")
    apscheduler_lib_logger.setLevel(logging.INFO)
    apscheduler_lib_logger.handlers.clear()
    apscheduler_lib_logger.propagate = False
    apscheduler_lib_logger.addHandler(scheduler_file)
    apscheduler_lib_logger.addHandler(app_console)