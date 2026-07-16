#!/usr/bin/env python3
"""
Kernel worker subprocess for persistent Python execution.

This script runs as a long-lived subprocess, maintaining a persistent
namespace across multiple code executions. Communication is via JSON
over stdin/stdout.

Protocol:
- Reads JSON requests from stdin (one per line)
- Writes JSON responses to stdout (one per line)
- Maintains namespace across executions

Request format:
    {"id": "uuid", "code": "python code here"}

Response format:
    {"id": "uuid", "stdout": "...", "stderr": "...", "error": null|"traceback",
     "trace": {"error_lineno": int|null, "error_call": str|null},
     "usage": {"wall_s": float, "cpu_s": float, "peak_rss_kb": int}}
"""

import builtins
import errno
import io
import json
import os
import resource
import signal
import sys
import threading
import time
import traceback
from io import StringIO










_PROTOCOL_WRITE_LOCK = threading.Lock()
sys._operon_protocol_lock = _PROTOCOL_WRITE_LOCK





_protocol_stdout = sys.stdout


MAX_OUTPUT_SIZE = 1024 * 1024


class _CappedStringIO(StringIO):
    """StringIO with a hard per-cell buffer cap (5d1f641e/0ab88025 — a runaway
    print / logging / tqdm loop otherwise grows unbounded and can OOM the
    worker). Cap is in UTF-8 bytes (what goes on the wire); `getvalue()`
    appends a marker reporting the REAL dropped count so the agent sees the
    signal (truncate_output is head-only; appending the marker at write()-time
    at byte-4MB would truncate it away). Cap is MAX_OUTPUT_SIZE minus headroom
    so marker + content stay under truncate_output's threshold — the agent sees
    our accurate "(N bytes dropped)" instead of a misleading generic suffix."""

    BUFFER_CAP = MAX_OUTPUT_SIZE - 256

    def __init__(self):
        super().__init__()
        self._buffered = 0
        self._dropped = 0

    def write(self, s):
        if self._buffered >= self.BUFFER_CAP:
            self._dropped += len(s.encode("utf-8", "surrogatepass"))
            return len(s)
        n = len(s.encode("utf-8", "surrogatepass"))
        remaining = self.BUFFER_CAP - self._buffered
        if n <= remaining:
            self._buffered += n
            return super().write(s)


        head = s.encode("utf-8", "surrogatepass")[:remaining].decode(
            "utf-8", "ignore"
        )
        self._buffered = self.BUFFER_CAP
        self._dropped = n - remaining
        super().write(head)
        return len(s)

    def getvalue(self):
        v = super().getvalue()
        if self._dropped:
            return v + (
                f"\n…(buffer capped at {self.BUFFER_CAP // 1024} KB; "
                f"{self._dropped} further bytes dropped)\n"
            )
        return v


class _StreamingStdout(_CappedStringIO):
    """Write-through stdout: captures to internal buffer AND streams each write
    as a {"type":"stdout_chunk","data":...} JSON line on the protocol-out pipe
    (`_protocol_stdout` — a non-inheritable high fd; fd 1 itself aliases
    stderr after main()'s dup2 dance).
    The host's _readProtocolResponse loop picks these up and forwards them live.
    Buffer capture still returns full output at end — streaming is additive."""







    STREAM_CAP = 10 * 1024 * 1024

    def __init__(self):
        super().__init__()
        self._streamed = 0







        self._active = True

    def write(self, s):
        if s and self._active and self._streamed < self.STREAM_CAP:
            try:
                n = len(s.encode("utf-8", "surrogatepass"))
                remaining = self.STREAM_CAP - self._streamed
                if n <= remaining:
                    payload = s
                    self._streamed += n
                else:

                    payload = s.encode("utf-8", "surrogatepass")[:remaining].decode(
                        "utf-8", "ignore"
                    )
                    self._streamed = self.STREAM_CAP
                line = json.dumps({"type": "stdout_chunk", "data": payload}) + "\n"
                with _PROTOCOL_WRITE_LOCK:
                    _protocol_stdout.write(line)
                    _protocol_stdout.flush()
                if self._streamed >= self.STREAM_CAP:
                    marker = (
                        json.dumps(
                            {
                                "type": "stdout_chunk",
                                "data": "\n…(live stream truncated at "
                                f"{self.STREAM_CAP // (1024*1024)} MB; "
                                "full output in tool_result)\n",
                            }
                        )
                        + "\n"
                    )
                    with _PROTOCOL_WRITE_LOCK:
                        _protocol_stdout.write(marker)
                        _protocol_stdout.flush()
            except Exception:
                pass
        return super().write(s)






for _k in os.environ.pop("OPERON_SECRET_VARS", "").split(","):
    if _k:
        os.environ.pop(_k, None)
del _k










_writable_roots = tuple(
    p.rstrip("/") for p in os.environ.pop("OPERON_WRITABLE_ROOTS", "").split(":") if p
)
_dlopen_exempt = tuple(
    p.rstrip("/") for p in os.environ.pop("OPERON_DLOPEN_EXEMPT", "").split(":") if p
)
if _writable_roots:





    _dlopen_exempt = _dlopen_exempt + tuple(
        p.rstrip("/") for p in {sys.prefix, sys.exec_prefix, sys.base_prefix} if p
    )














    import posix as _posix
    import posixpath as _posixpath

    def _operon_audit(
        event,
        args,
        *,
        _realpath=os.path.realpath,
        _normpath=_posixpath.normpath,
        _getcwd=_posix.getcwd,
        _str=str,
        _roots=_writable_roots,
        _exempt=_dlopen_exempt,
        _PermissionError=PermissionError,
    ):
        if event != "ctypes.dlopen":
            return
        name = args[0]
        if not name or "/" not in _str(name):
            return
        name = _str(name)


        try:
            literal = _normpath(
                name if name.startswith("/") else _getcwd() + "/" + name
            )
        except (OSError, ValueError):
            literal = name
        try:
            real = _realpath(name)
        except (OSError, ValueError):
            real = name
        for candidate in (literal, real):
            is_exempt = False
            for root in _exempt:
                if candidate == root or candidate.startswith(root + "/"):
                    is_exempt = True
                    break
            if is_exempt:
                continue
            for root in _roots:
                if candidate == root or candidate.startswith(root + "/"):
                    raise _PermissionError(
                        f"Refusing to dlopen shared library from writable path: {candidate}"
                    )

    sys.addaudithook(_operon_audit)
    del _operon_audit, _posix, _posixpath
del _writable_roots, _dlopen_exempt


def truncate_output(text: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    """Truncate output if it exceeds max size."""
    if len(text) > max_size:
        return (
            text[:max_size] + f"\n... (truncated, {len(text) - max_size} bytes omitted)"
        )
    return text


def _cpu_seconds():
    """Total CPU time (user+sys) consumed by this process and its reaped
    children so far. RUSAGE_CHILDREN only accounts for children that have
    been wait()ed — subprocess.run/check_output do this, so CPU burned in a
    cell's subprocesses is captured. Still-running background children are
    not (can't be, without polling /proc)."""
    s = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime


def _reset_peak_rss():
    """On Linux, writing '5' to /proc/self/clear_refs resets the VmHWM
    high-water mark to the current RSS, so a subsequent VmHWM read gives the
    peak over just the next cell rather than the process lifetime. No-op on
    non-Linux or if procfs isn't writable (falls back to a cumulative peak,
    which is still informative)."""
    try:
        with open("/proc/self/clear_refs", "w") as f:
            f.write("5\n")
    except OSError:
        pass


def _read_peak_rss_kb():
    """Peak RSS in KB since the last _reset_peak_rss() (Linux), or the
    process-lifetime peak via getrusage elsewhere. On Linux ru_maxrss is KB;
    on macOS it's bytes — normalize to KB."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except OSError:
        pass
    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        maxrss //= 1024
    return maxrss


def _configure_pandas_display(pd_module):
    """Configure pandas display options to prevent column/row truncation."""
    pd_module.set_option("display.max_columns", None)
    pd_module.set_option("display.max_rows", 500)
    pd_module.set_option("display.max_colwidth", None)
    pd_module.set_option("display.width", None)
    pd_module.set_option(
        "display.expand_frame_repr", False
    )


def _open_fignums():
    """Fignums currently open, or empty set if matplotlib isn't loaded.
    Never imports matplotlib itself."""
    try:
        if "matplotlib" not in sys.modules:
            return set()
        import matplotlib.pyplot as plt

        return set(plt.get_fignums())
    except BaseException:



        return set()


def _auto_capture_figures(cell_counter, pre_fignums, workspace_dir):
    """User-terminal cells only (request origin == "user"): save figures
    CREATED during this cell to the workspace so the notebook side view can
    show them — rich output is filesystem-diff based, so an unsaved figure
    is invisible. Pre-existing figures (e.g. one the agent left open) are
    deliberately skipped: capturing them would attach stale plots to
    unrelated user cells. Figures are NOT closed — jupyter-style iterative
    plotting (tweaking `ax` in a follow-up cell) must keep working; the
    pre_fignums snapshot already prevents re-capture. Filenames carry the
    worker pid so a respawned worker (cell_counter resets) can't silently
    overwrite an earlier cell's figure. Saves land under workspace_dir
    (host-threaded absolute path), never the kernel's persistent cwd —
    the agent may have chdir'd into a user repo. Agent cells are untouched
    (agents savefig explicitly). Best-effort: never raises, never imports
    matplotlib. Per-figure try: one backend/FS
    failure must not abandon the remaining figures in the burst."""
    try:
        if "matplotlib" not in sys.modules:
            return
        import matplotlib.pyplot as plt

        new_nums = [n for n in plt.get_fignums() if n not in pre_fignums]
        for num in new_nums:
            try:
                name = "figure_%d_%d_%d.png" % (cell_counter, num, os.getpid())
                path = (
                    os.path.join(workspace_dir, name) if workspace_dir else name
                )
                plt.figure(num).savefig(path, bbox_inches="tight")
                print("[saved %s]" % name)
            except Exception:
                pass
    except Exception:
        pass


def _create_import_wrapper(original_import):
    """Create an import wrapper that configures pandas when first imported."""
    _pandas_configured = {"value": False}

    def import_wrapper(name, *args, **kwargs):
        module = original_import(name, *args, **kwargs)

        if name == "pandas" and not _pandas_configured["value"]:
            _pandas_configured["value"] = True
            try:
                _configure_pandas_display(module)
            except Exception:


                _pandas_configured["value"] = False
        return module

    return import_wrapper


def _format_exc_safe(exc=None):
    """traceback.format_exc() that survives hostile exception objects.

    Second hostile-exception vector: stdlib traceback
    rendering walks __cause__/__context__ too — a raising data-descriptor
    kills format_exc() itself, escaping the except arms exactly like the
    unguarded _ki_in_chain walk did. Rendering must classify, never die.
    `exc` is the arm's bound exception, so the fallback renders the
    CELL's error (not the rendering failure raised inside the walk).
    """
    try:
        return traceback.format_exc()
    except BaseException:
        try:
            return "%s: %s (traceback unavailable — exception raised while rendering its own chain)" % (
                type(exc).__name__,
                exc,
            )
        except BaseException:
            return "(unprintable exception — raised while rendering its own chain)"


def _error_lineno(exc, cell_tag):
    """Walk traceback, return lineno of the deepest frame matching cell_tag.

    Each compile() gets a unique filename like "<kernel:42>" so we can
    distinguish THIS cell's frames from functions defined in prior cells
    (which would have "<kernel:7>" etc). Without this, a function defined
    in cell 0 that raises when called in cell 2 would return the line
    number inside the function body (relative to cell 0's source), not
    cell 2's call-site line.

    Returns None if no matching frame (error entirely inside library code).
    """
    tb = getattr(exc, "__traceback__", None)
    lineno = None
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == cell_tag:
            lineno = tb.tb_lineno
        tb = tb.tb_next
    return lineno


def _error_call(exc, cell_tag, code):
    """Failing-expression text of the deepest cell frame, or None.

    Python 3.11+ fine-grained locations (PEP 657): the deepest frame whose
    co_filename matches cell_tag carries byte-precise column offsets for
    the failing sub-expression — slice it from the cell source. This is
    the Python analogue of the R worker's deparse(conditionCall(e)):
    `host.llm(config.llm)` attributes to `config.llm`, a rebound
    `host.llm(1)` to `host.llm` (exact-call coupling
    instead of stderr text heuristics). Capped 200 chars; None when
    positions are unavailable. Hardened like _error_lineno: any hostile
    descriptor classifies as "no attributable call", never escapes.
    """
    try:
        tb = getattr(exc, "__traceback__", None)
        hit = None
        while tb is not None:
            if tb.tb_frame.f_code.co_filename == cell_tag:
                hit = tb
            tb = tb.tb_next
        if hit is None:
            return None
        import itertools
        pos = next(
            itertools.islice(
                hit.tb_frame.f_code.co_positions(), hit.tb_lasti // 2, None
            ),
            None,
        )
        if pos is None:
            return None
        lineno, end_lineno, col, end_col = pos
        if lineno is None or col is None or end_col is None:
            return None
        lines = code.split("\n")





        raw = lines[lineno - 1].encode("utf-8")
        if end_lineno is not None and end_lineno != lineno:
            seg = raw[col:].decode("utf-8", "replace")
        else:
            seg = raw[col:end_col].decode("utf-8", "replace")
        seg = seg.strip()
        return seg[:200] if seg else None
    except BaseException:
        return None


def _ki_in_chain(exc):
    """True iff the DELIVERED (handler-raised) SIGINT KeyboardInterrupt is
    in exc's causal chain.

    Causal gate for the delivered-SIGINT latch: a
    conversion during unwind (`except KeyboardInterrupt: sys.exit(130)` /
    `raise RuntimeError("Aborted!")`) carries the KI in __context__, while
    an unrelated error raised AFTER user code caught the KI and recovered
    does not — that one must persist as "error", not "cancelled", or a
    real failure (disk full, KeyError) renders as a quiet cancellation.

    Two refinements:
    - Matches the _operon_delivered_sigint marker set by _sigint_handler,
      NOT isinstance(KeyboardInterrupt) — a fresh user-written
      `raise KeyboardInterrupt` after a recovered SIGINT carries no marker
      and stays an error.
    - Honors __suppress_context__, mirroring Python's own traceback rule:
      `raise X from None` explicitly severs the chain, so the cell is the
      user's declared fresh error. __cause__ always wins over
      __context__ (`raise X from Y` sets suppress too).
    """
    seen = set()
    depth = 0
    while exc is not None and id(exc) not in seen and depth < 100:
        seen.add(id(exc))
        depth += 1
        try:
            if getattr(exc, "_operon_delivered_sigint", False):
                return True
            if exc.__cause__ is not None:
                exc = exc.__cause__
            elif getattr(exc, "__suppress_context__", False):
                return False
            else:
                exc = exc.__context__
        except BaseException:










            return False
    return False


def _cell_attribution(exc, cell_tag, sigint_delivered, code=""):
    """(interrupted, error_lineno, error_call) — the ONE predicate all arms share.

    interrupted ⇔ a SIGINT was delivered this cell AND exc is causally
    linked to the handler-raised KeyboardInterrupt (see _ki_in_chain).

    When interrupted, error_lineno is None REGARDLESS of which arm caught
    the exception: the host's code-synthesis pipeline keys
    its "cancelled, no signal" filter on null lineno — a cancelled rewrap
    (click's sys.exit(130) / RuntimeError('Aborted!')) shipping a lineno
    would leak Ctrl-C'd partial work into the artifact extraction prompts
    exactly like the un-gated KI arm did. Otherwise the
    deepest cell frame, like any ordinary error.
    """
    interrupted = sigint_delivered and _ki_in_chain(exc)
    try:
        if interrupted:
            return interrupted, None, None
        return (
            interrupted,
            _error_lineno(exc, cell_tag),
            _error_call(exc, cell_tag, code),
        )
    except BaseException:




        return interrupted, None, None


def main():
    """Main loop: read requests from stdin, execute, write responses to stdout."""


    print("[kernel_worker] v2 tracer+error_lineno", file=sys.stderr, flush=True)

    cell_counter = 0











    _in_user_code = [False]




    _sigint_delivered = [False]

    def _sigint_handler(signum, frame):
        if _in_user_code[0]:



            _in_user_code[0] = False
            _sigint_delivered[0] = True




            ki = KeyboardInterrupt()
            ki._operon_delivered_sigint = True
            raise ki






    signal.signal(signal.SIGINT, _sigint_handler)






    original_import = builtins.__import__
    builtins.__import__ = _create_import_wrapper(original_import)





    if not hasattr(builtins, "help"):
        import pydoc

        builtins.help = pydoc.help




    namespace = {
        "__name__": "__main__",
        "__builtins__": __builtins__,
    }































    global _protocol_stdout
    _protocol_stdin = os.fdopen(os.dup(0), "r", encoding="utf-8", errors="replace")
    os.set_inheritable(_protocol_stdin.fileno(), False)
    sys._operon_protocol_stdin = _protocol_stdin





    _proto_in_reserve = os.dup(_protocol_stdin.fileno())
    os.set_inheritable(_proto_in_reserve, False)
    _protocol_stdout = os.fdopen(
        os.dup(1), "w", encoding="utf-8", errors="replace", buffering=1
    )
    os.set_inheritable(_protocol_stdout.fileno(), False)






    _wrap = getattr(sys, "_operon_protocol_stdout_wrap", None)
    if _wrap is not None:
        _protocol_stdout = _wrap(_protocol_stdout)
    sys._operon_protocol_stdout = _protocol_stdout
    _devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(_devnull, 0)
    os.close(_devnull)
    os.dup2(2, 1)






    _st0 = os.fstat(_protocol_stdin.fileno())
    _protocol_ident = (_st0.st_dev, _st0.st_ino)

    def _is_protocol_stream(stream):
        try:
            st = os.fstat(stream.fileno())
            return (st.st_dev, st.st_ino) == _protocol_ident
        except (SystemExit, GeneratorExit):










            return False
        except Exception:
            return False

    def _identity_suspect(stream):










        fn = getattr(stream, "fileno", None)
        if fn is None:
            return False
        try:
            fd = fn()
        except io.UnsupportedOperation:
            return False
        except (SystemExit, GeneratorExit):





            return True
        except Exception:
            return True
        try:
            st = os.fstat(fd)
        except Exception:
            return True
        return (st.st_dev, st.st_ino) != _protocol_ident








    _parked_wrappers = []




    _byoc_readline = getattr(sys, "_operon_protocol_readline", None)

    def _readline():









        if _byoc_readline is not None:
            return _byoc_readline()
        return sys._operon_protocol_stdin.readline()










    class _OperonQuitterExit(SystemExit):
        pass




    _OperonQuitterExit.__name__ = "SystemExit"
    _OperonQuitterExit.__qualname__ = "SystemExit"

    class _OperonQuitter:
        def __repr__(self):
            return (
                "exit()/quit() is disabled here — this terminal shares the "
                "agent's live kernel. Kernels are stopped from the UI."
            )

        def __call__(self, code=None):
            raise _OperonQuitterExit(code)

    _quitter = _OperonQuitter()
    namespace["exit"] = namespace["quit"] = _quitter





    builtins.exit = builtins.quit = _quitter











    while True:
        try:






            _src = getattr(sys, "_operon_protocol_stdin", None)
            if _src is None or _identity_suspect(_src):
                raise OSError(
                    "protocol stream identity lost before read "
                    "(fd recycled/reassigned)"
                )
            line = _readline()
            if not isinstance(line, str):





                raise TypeError(
                    "protocol readline returned non-str %r"
                    % (type(line).__name__,)
                )







            _src = getattr(sys, "_operon_protocol_stdin", None)
            if _src is None or _identity_suspect(_src):
                raise OSError(
                    "protocol stream identity lost (fd recycled/reassigned)"
                )
            if not line and not _is_protocol_stream(_src):






                raise OSError(
                    "EOF from unverifiable protocol source — refusing "
                    "silent shutdown"
                )
        except Exception:





            try:









                _healthy = False
                try:
                    if (
                        getattr(sys, "_operon_protocol_stdin", None)
                        is not _protocol_stdin
                        and not _protocol_stdin.closed




                        and _is_protocol_stream(_protocol_stdin)
                    ):
                        _healthy = True
                except Exception:
                    _healthy = False
                if not _healthy:



















                    _close_it = False
                    try:
                        _ds = os.fstat(_protocol_stdin.fileno())
                        _close_it = (
                            _ds.st_dev,
                            _ds.st_ino,
                        ) == _protocol_ident
                    except ValueError:
                        _close_it = True
                    except OSError as _fe:
                        _close_it = (
                            getattr(_fe, "errno", None) == errno.EBADF
                        )
                    except Exception:
                        _close_it = False
                    if _close_it:
                        try:
                            _protocol_stdin.close()
                        except Exception:
                            pass
                    else:
                        _parked_wrappers.append(_protocol_stdin)
                    _protocol_stdin = os.fdopen(
                        os.dup(_proto_in_reserve),
                        "r",
                        encoding="utf-8",
                        errors="replace",
                    )
                    os.set_inheritable(_protocol_stdin.fileno(), False)







                _old_pub = getattr(sys, "_operon_protocol_stdin", None)
                if _old_pub is not None and _old_pub is not _protocol_stdin:
                    _parked_wrappers.append(_old_pub)



                sys._operon_protocol_stdin = _protocol_stdin








                if _identity_suspect(_protocol_stdin):
                    raise OSError(
                        "protocol stream identity lost after recovery "
                        "(reserve fd recycled)"
                    )
                line = _readline()
                if not isinstance(line, str):
                    raise TypeError(
                        "protocol readline returned non-str %r after recovery"
                        % (type(line).__name__,)
                    )











                _rsrc = getattr(sys, "_operon_protocol_stdin", None)
                if _rsrc is None or _identity_suspect(_rsrc):
                    raise OSError(
                        "protocol stream identity lost during recovery read"
                    )
                if not line and not _is_protocol_stream(_rsrc):
                    raise OSError(
                        "EOF from unverifiable protocol source after "
                        "recovery — refusing silent shutdown"
                    )
            except Exception as exc:
                print(
                    "[kernel_worker] protocol stdin unreadable (%r) — "
                    "shutting down cleanly" % (exc,),
                    file=sys.stderr,
                    flush=True,
                )
                break
        if not line:
            break
        line = line.strip()
        if not line:
            continue


        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:

            error_response = {
                "id": "unknown",
                "stdout": "",
                "stderr": "",
                "error": f"Invalid JSON request: {e}",
            }
            print(json.dumps(error_response), file=_protocol_stdout, flush=True)
            continue





        if not isinstance(request, dict):
            error_response = {
                "id": "unknown",
                "stdout": "",
                "stderr": "",
                "error": "Invalid request: expected a JSON object, got %s"
                % type(request).__name__,
            }
            print(json.dumps(error_response), file=_protocol_stdout, flush=True)
            continue









        if isinstance(request, dict) and str(
            request.get("type", "")
        ).startswith("host_"):
            continue

        request_id = request.get("id", "unknown")
        code = request.get("code", "")



        origin = request.get("origin", "agent")

        workspace_dir = request.get("workspace_dir")


        stdout_capture = _StreamingStdout()
        stderr_capture = _CappedStringIO()
        error = None
        error_lineno = None
        error_call = None
        interrupted = False
        _sigint_delivered[0] = False



        cell_tag = "<kernel:pre>"



        _reset_peak_rss()
        wall0 = time.perf_counter()
        cpu0 = _cpu_seconds()


        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:

            sys.stdout = stdout_capture
            sys.stderr = stderr_capture





            cell_counter += 1
            cell_tag = f"<kernel:{cell_counter}>"







            compiled = None
            is_expr = True
            try:
                compiled = compile(code, cell_tag, "eval")
            except SyntaxError:
                is_expr = False
                try:
                    compiled = compile(code, cell_tag, "exec")
                except SyntaxError as e:
                    error = f"SyntaxError: {e}"
                    error_lineno = getattr(e, "lineno", None)

            if compiled is not None:








                import linecache as _linecache
                _linecache.cache[cell_tag] = (
                    len(code), None, code.splitlines(True), cell_tag,
                )




                _linecache.cache.pop(f"<kernel:{cell_counter - 128}>", None)














                pre_figs = _open_fignums() if origin == "user" else ()
                try:
                    _in_user_code[0] = True
                    if is_expr:
                        result = eval(compiled, namespace)
                        if result is not None:
                            print(repr(result))
                    else:
                        exec(compiled, namespace)
                    _in_user_code[0] = False
                except KeyboardInterrupt as e:








                    _in_user_code[0] = False






                    interrupted, error_lineno, error_call = _cell_attribution(
                        e, cell_tag, _sigint_delivered[0], code
                    )
                    error = _format_exc_safe(e)
                except (SystemExit, GeneratorExit) as e:







                    _in_user_code[0] = False






                    interrupted, error_lineno, error_call = _cell_attribution(
                        e, cell_tag, _sigint_delivered[0], code
                    )
                    error = _format_exc_safe(e)
                    if isinstance(e, _OperonQuitterExit) and not interrupted:




                        error += (
                            "\n(exit()/quit() is disabled here — this "
                            "terminal shares the agent's live kernel. "
                            "Kernels are stopped from the UI, not from code.)"
                        )
                except Exception as e:
                    _in_user_code[0] = False







                    interrupted, error_lineno, error_call = _cell_attribution(
                        e, cell_tag, _sigint_delivered[0], code
                    )
                    error = _format_exc_safe(e)
                except BaseException as e:








                    _in_user_code[0] = False
                    interrupted, error_lineno, error_call = _cell_attribution(
                        e, cell_tag, _sigint_delivered[0], code
                    )
                    error = _format_exc_safe(e)




                if origin == "user":
                    _auto_capture_figures(cell_counter, pre_figs, workspace_dir)

        except KeyboardInterrupt as e:







            _in_user_code[0] = False
            error = _format_exc_safe(e)



            interrupted, error_lineno, error_call = _cell_attribution(
                e, cell_tag, _sigint_delivered[0], code
            )





            if origin == "user":
                _auto_capture_figures(cell_counter, pre_figs, workspace_dir)

        finally:




            stdout_capture._active = False

            sys.stdout = old_stdout
            sys.stderr = old_stderr

        usage = {
            "wall_s": round(time.perf_counter() - wall0, 3),
            "cpu_s": round(_cpu_seconds() - cpu0, 3),
            "peak_rss_kb": _read_peak_rss_kb(),
        }


        response = {
            "id": request_id,
            "stdout": truncate_output(stdout_capture.getvalue()),
            "stderr": truncate_output(stderr_capture.getvalue()),
            "error": error,
            "interrupted": interrupted,
            "trace": {
                "error_lineno": error_lineno,
                "error_call": error_call,
            },
            "usage": usage,
        }






        with _PROTOCOL_WRITE_LOCK:
            _protocol_stdout.write(json.dumps(response) + "\n")
            _protocol_stdout.flush()


if __name__ == "__main__":
    main()
