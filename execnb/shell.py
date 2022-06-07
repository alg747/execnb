# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_shell.ipynb.

# %% ../nbs/02_shell.ipynb 2
from __future__ import annotations
from fastcore.utils import *
from fastcore.script import call_parse

from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displayhook import DisplayHook
from IPython.core.displaypub import DisplayPublisher
from io import StringIO

from .fastshell import FastInteractiveShell
from .nbio import *

from collections.abc import Callable

# %% auto 0
__all__ = ['CaptureShell', 'exec_nb']

# %% ../nbs/02_shell.ipynb 4
# IPython requires a DisplayHook and DisplayPublisher
# We override `__call__` and `publish` to save outputs instead of printing them

class _CaptureHook(DisplayHook):
    "Called when displaying a result"
    def __call__(self, result=None):
        if result is None: return
        self.fill_exec_result(result)
        self.shell._result(result)

class _CapturePub(DisplayPublisher):
    "Called when adding an output"
    def publish(self, data, metadata=None, **kwargs): self.shell._add_out(data, metadata, typ='display_data')

# %% ../nbs/02_shell.ipynb 5
# These are the standard notebook formats for exception and stream data (e.g stdout)
def _out_exc(ename, evalue, traceback): return dict(ename=str(ename), evalue=str(evalue), output_type='error', traceback=traceback)
def _out_stream(text): return dict(name='stdout', output_type='stream', text=text.splitlines(False))

# %% ../nbs/02_shell.ipynb 7
class CaptureShell(FastInteractiveShell):
    "Execute the IPython/Jupyter source code"
    def __init__(self):
        super().__init__(displayhook_class=_CaptureHook, display_pub_class=_CapturePub)
        InteractiveShell._instance = self
        self.result,self.out,self.count = None,[],1
        self.run_cell('%matplotlib inline')

    def enable_gui(self, gui=None): pass

    def _showtraceback(self, etype, evalue, stb: str):
        self.out.append(_out_exc(etype, evalue, stb))
        self.exc = (etype, evalue, '\n'.join(stb))

    def _add_out(self, data, meta, typ='execute_result', **kwargs): self.out.append(dict(data=data, metadata=meta, output_type=typ, **kwargs))

    def _add_exec(self, result, meta, typ='execute_result'):
        fd = {k:v.splitlines(True) for k,v in result.items()}
        self._add_out(fd, meta, execution_count=self.count)
        self.count += 1

    def _result(self, result):
        self.result = result
        self._add_exec(*self.display_formatter.format(result))

    def _stream(self, std):
        text = std.getvalue()
        if text: self.out.append(_out_stream(text))

# %% ../nbs/02_shell.ipynb 10
@patch
def run(self:CaptureShell, code:str, stdout=True, stderr=True):
    "runs `code`, returning a list of all outputs in Jupyter notebook format"
    self.exc = False
    self.out.clear()
    self.sys_stdout,self.sys_stderr = sys.stdout,sys.stderr
    if stdout: stdout = sys.stdout = StringIO()
    if stderr: stderr = sys.stderr = StringIO()
    try: self.run_cell(code)
    finally: sys.stdout,sys.stderr = self.sys_stdout,self.sys_stderr
    self._stream(stdout)
    return [*self.out]

# %% ../nbs/02_shell.ipynb 19
@patch
def cell(self:CaptureShell, cell, stdout=True, stderr=True):
    "Run `cell`, skipping if not code, and store outputs back in cell"
    if cell.cell_type!='code': return
    outs = self.run(cell.source)
    if outs:
        cell.outputs = outs
        for o in outs:
            if 'execution_count' in o: cell['execution_count'] = o['execution_count']

# %% ../nbs/02_shell.ipynb 23
def _false(o): return False

@patch
def run_all(self:CaptureShell,
            nb, # A notebook read with `nbclient` or `read_nb`
            exc_stop:bool=False, # Stop on exceptions?
            preproc:Callable=_false, # Called before each cell is executed
            postproc:Callable=_false, # Called after each cell is executed
            inject_code:str|None=None, # Code to inject into a cell
            inject_idx:int=0 # Cell to replace with `inject_code`
           ):
    "Run all cells in `nb`, stopping at first exception if `exc_stop`"
    if inject_code is not None: nb.cells[inject_idx].source = inject_code
    for cell in nb.cells:
        if not preproc(cell):
            self.cell(cell)
            postproc(cell)
        if self.exc and exc_stop: raise self.exc[1] from None

# %% ../nbs/02_shell.ipynb 37
@patch
def execute(self:CaptureShell,
            src:str|Path, # Notebook path to read from
            dest, # Notebook path to write to
            exc_stop:bool=False, # Stop on exceptions?
            preproc:Callable=_false, # Called before each cell is executed
            postproc:Callable=_false, # Called after each cell is executed
            inject_code:str|None=None, # Code to inject into a cell
            inject_path:str|Path|None=None, # Path to file containing code to inject into a cell
            inject_idx:int=0 # Cell to replace with `inject_code`
):
    "Execute notebook from `src` and save with outputs to `dest"
    nb = read_nb(src)
    if inject_path is not None: inject_code = Path(inject_path).read_text()
    self.run_all(nb, exc_stop=exc_stop, preproc=preproc, postproc=postproc,
                 inject_code=inject_code, inject_idx=inject_idx)
    write_nb(nb, dest)

# %% ../nbs/02_shell.ipynb 47
@call_parse
def exec_nb(
    src:str, # Notebook path to read from
    dest:str, # Notebook path to write to
    exc_stop:bool=False, # Stop on exceptions?
    inject_code:str=None, # Code to inject into a cell
    inject_path:str=None, # Path to file containing code to inject into a cell
    inject_idx:int=0 # Cell to replace with `inject_code`
):
    "Execute notebook from `src` and save with outputs to `dest"
    CaptureShell().execute(src, dest, exc_stop=exc_stop, inject_code=inject_code,
                           inject_path=inject_path, inject_idx=inject_idx)
