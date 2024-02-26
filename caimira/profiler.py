import cProfile
import glob
import json
import logging
import os
import pstats
import shutil
import typing
from datetime import datetime
from enum import Enum
from functools import wraps
from pstats import f8, func_std_string # type: ignore

from pyinstrument import Profiler as PyInstrumentProfiler

logger = logging.getLogger("Profiler")


class Profilers(Enum):
    PYINSTRUMENT = "pyinstrument"
    CPROFILER = "cprofiler"

    @staticmethod
    def from_str(value):
        if value == Profilers.PYINSTRUMENT.value:
            return Profilers.PYINSTRUMENT
        elif value == Profilers.CPROFILER.value:
            return Profilers.CPROFILER
        else:
            raise NotImplementedError


class PyInstrumentWrapper:
    profiler = PyInstrumentProfiler(async_mode=True)

    @property
    def is_running(self):
        return self.profiler.is_running

    def start(self):
        self.profiler.start()

    def stop(self):
        self.profiler.stop()
        report_html = self.profiler.output_html(timeline=True)
        report_id = str(abs(hash(report_html)))
        return report_id, Profilers.PYINSTRUMENT.value, report_html


class CProfilerWrapper:
    profiler = cProfile.Profile()
    _is_running = False

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        self.profiler.enable()
        self._is_running = True

    def stop(self):
        self.profiler.disable()
        self._is_running = False

        ps = pstats.Stats(self.profiler).sort_stats("cumulative")

        report_html = "<p>"
        report_html += f"{ps.total_calls} function calls"
        if ps.total_calls != ps.prim_calls:
            report_html += " (%d primitive calls)" % ps.prim_calls
        report_html += " in %.3f seconds" % ps.total_tt
        report_html += "</p>"

        report_html += "<p>"
        report_html += f"Ordered by: {ps.sort_type}"
        report_html += "</p>"

        report_html += "<table><thead><tr>"
        report_html += "<td>ncalls</td><td>tottime</td><td>percall</td><td>cumtime</td><td>percall</td><td>filename:lineno(function)</td>"
        report_html += "</tr></thead><tbody>"
        for func in ps.stats:
            report_html += "<tr>"
            cc, nc, tt, ct, callers = ps.stats[func]
            c = str(nc)
            if nc != cc:
                c = c + "/" + str(cc)
            report_html += f"<td>{c.rjust(9)}</td>"
            report_html += f"<td>{f8(tt)}</td>"
            report_html += f"<td></td>" if nc == 0 else f"<td>{f8(tt/nc)}</td>"
            report_html += f"<td>{f8(ct)}</td>"
            report_html += f"<td></td>" if cc == 0 else f"<td>{f8(ct/cc)}</td>"
            report_html += f"<td>{func_std_string(func)}</td>"
            report_html += "</tr>"
        report_html += "</tbody></table>"
        report_id = str(abs(hash(report_html)))
        return report_id, Profilers.CPROFILER.value, report_html


class Profiler:
    profiler = None
    profiler_type = None

    def __init__(self, profiler_type):
        self.profiler_type = profiler_type

    def start(self):
        if self.profiler_type == Profilers.PYINSTRUMENT:
            self.profiler = PyInstrumentWrapper()
        elif self.profiler_type == Profilers.CPROFILER:
            self.profiler = CProfilerWrapper()
        else:
            raise NotImplementedError

        self.profiler.start()

    def stop(self, session_name, uri, path="", query="", method=""):
        report_id, report_type, report_html = self.profiler.stop()
        self.profiler = None
        return report_id, dict(
            session_name=session_name,
            ts=datetime.utcnow().strftime("%Y-%m-%d - %H:%M:%S"),
            uri=uri,
            path=path,
            query=query,
            method=method,
            report_id=report_id,
            report_type=report_type,
            report_html=report_html,
        )

    def is_running(self):
        return self.profiler and self.profiler.is_running


class CaimiraProfiler:
    _cache_dirpath: str
    _cache_filepath: str
    CACHE_DIR: str = os.environ.get("CAIMIRA_PROFILER_CACHE_DIR", "/tmp")
    ROOT_URL: str = "/profiler"

    def __init__(self):
        _cache_dir = os.path.join(self.CACHE_DIR, "caimira-profiler")
        self._cache_dirpath = _cache_dir
        self._cache_filepath = os.path.join(_cache_dir, "active")

    def _set_active(self, name: str, profiler_type: Profilers):
        try:
            os.access(self._cache_dirpath, os.W_OK)
        except Exception as e:
            # Handle the exception, e.g., print an error message
            logger.warning(f"cannot write in cache folder {self._cache_dirpath}")

        if not os.path.exists(self._cache_dirpath):
            os.makedirs(self._cache_dirpath)

        with open(self._cache_filepath, "w") as fp:
            json.dump(dict(name=name, profiler_type=profiler_type.value), fp)

    def _set_inactive(self):
        with open(self._cache_filepath, "w") as fp:
            json.dump(dict(), fp)

    @property
    def sessions(self):
        """Return all stored sessions."""
        if not os.path.exists(self._cache_dirpath):
            return {}

        reports_by_session = {}
        json_files = glob.glob(os.path.join(self._cache_dirpath, "*.json"))
        for json_file in json_files:
            with open(json_file) as fp:
                report = json.load(fp)

            session_name = report["session_name"]

            reports_by_session.setdefault(session_name, [])
            reports_by_session[session_name].append(report)

        return reports_by_session

    @property
    def session(self):
        """Return the session name."""
        if not os.path.exists(self._cache_filepath):
            return None

        with open(self._cache_filepath) as fp:
            d = json.load(fp)
            return dict(
                name=d["name"], profiler_type=Profilers.from_str(d["profiler_type"])
            )

    @property
    def is_active(self):
        """Return True if a session is active."""
        enabled = os.environ.get("CAIMIRA_PROFILER_ENABLED", 0)
        if not enabled:
            return False

        if not os.path.exists(self._cache_filepath):
            return False

        try:
            with open(self._cache_filepath) as fp:
                d = json.load(fp)
                return True if d else False
        except json.decoder.JSONDecodeError:
            os.remove(self._cache_filepath)
            return False

    def start_session(
        self,
        name: typing.Optional[str] = None,
        profiler_type: Profilers = Profilers.PYINSTRUMENT,
    ):
        """Start a new session, assigning the given name."""
        now = datetime.utcnow().isoformat()
        name = f"{name}-{now}" if name else now
        self._set_active(name, profiler_type)

    def start_profiler(self):
        """Start the profiler.

        In the context of HTTP requests, this should be called at the beginning of
        each HTTP request.
        """
        if not self.is_active:
            raise Exception("No active session.")

        profiler_type = self.session["profiler_type"]
        profiler = Profiler(profiler_type)
        profiler.start()
        return profiler

    def stop_profiler(
        self,
        profiler,
        uri: str,
        path: typing.Optional[str] = "",
        query: typing.Optional[str] = "",
        method: typing.Optional[str] = "",
    ):
        """Stop the profiler, previously obtained when starting it.

        In the context of HTTP requests, this should be called at the end of
        each HTTP request.
        """
        if not self.is_active:
            raise Exception("No active session.")

        report_id, report = profiler.stop(
            self.session["name"], uri, path, query, method
        )
        with open(os.path.join(self._cache_dirpath, f"{report_id}.json"), "w") as fp:
            json.dump(report, fp)

    def stop_session(self):
        """Stop the current active session."""
        if not self.is_active:
            raise Exception("No active session.")

        self._set_inactive()

    def get_report(self, report_id: str):
        """Return a report by the given id."""
        for reports in self.sessions.values():
            for report in reports:
                if report["report_id"] == report_id:
                    return (
                        Profilers.from_str(report["report_type"]),
                        report["report_html"],
                    )

    def clear_sessions(self):
        """Delete all sessions."""
        if self.is_active:
            raise Exception("Session still active.")

        shutil.rmtree(self._cache_dirpath)


def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = CaimiraProfiler()
        if profiler.is_active:
            profiler_run = profiler.start_profiler()

        result = func(*args, **kwargs)

        if profiler.is_active:
            profiler.stop_profiler(profiler=profiler_run, uri=func.__name__)

        return result

    return wrapper
