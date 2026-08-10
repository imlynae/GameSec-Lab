# -*- coding: utf-8 -*-

import ctypes
import ctypes.wintypes as wintypes
import struct
import sys
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

PROCESS_NAME = "GameSec.exe"

BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "scan_results.json"
SESSION_FILE = BASE_DIR / "scan_session.json"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)


# ============================================================
# WINDOWS CONSTANTS
# ============================================================

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000

PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100

TH32CS_SNAPPROCESS = 0x00000002


kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True
)


# ============================================================
# WINDOWS STRUCTURES
# ============================================================

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


# ============================================================
# LOGGING
# ============================================================

def create_new_session(pid):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    log_file = LOG_DIR / f"gamesec_{timestamp}.log"

    session = {
        "pid": pid,
        "process": PROCESS_NAME,
        "log_file": str(log_file),
        "created_at": timestamp
    }

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            session,
            file,
            indent=4
        )

    return session


def load_session():
    if not SESSION_FILE.exists():
        return None

    with open(
        SESSION_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def log(message):
    print(message)

    session = load_session()

    if session is None:
        return

    log_file = Path(
        session["log_file"]
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        log_file,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            f"[{timestamp}] {message}\n"
        )


# ============================================================
# PROCESS DISCOVERY
# ============================================================

def get_pid_by_name(process_name):
    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPPROCESS,
        0
    )

    if snapshot == -1:
        raise ctypes.WinError(
            ctypes.get_last_error()
        )

    entry = PROCESSENTRY32()

    entry.dwSize = ctypes.sizeof(
        PROCESSENTRY32
    )

    success = kernel32.Process32FirstW(
        snapshot,
        ctypes.byref(entry)
    )

    while success:

        if (
            entry.szExeFile.lower()
            == process_name.lower()
        ):

            pid = entry.th32ProcessID

            kernel32.CloseHandle(
                snapshot
            )

            return pid

        success = kernel32.Process32NextW(
            snapshot,
            ctypes.byref(entry)
        )

    kernel32.CloseHandle(
        snapshot
    )

    return None


# ============================================================
# PROCESS HANDLE
# ============================================================

def open_process(pid):
    access = (
        PROCESS_VM_READ
        | PROCESS_VM_WRITE
        | PROCESS_VM_OPERATION
        | PROCESS_QUERY_INFORMATION
    )

    handle = kernel32.OpenProcess(
        access,
        False,
        pid
    )

    if not handle:
        raise ctypes.WinError(
            ctypes.get_last_error()
        )

    return handle


# ============================================================
# MEMORY READ
# ============================================================

def read_int32(handle, address):
    buffer = ctypes.create_string_buffer(
        4
    )

    bytes_read = ctypes.c_size_t()

    success = kernel32.ReadProcessMemory(
        handle,
        ctypes.c_void_p(address),
        buffer,
        4,
        ctypes.byref(bytes_read),
    )

    if (
        not success
        or bytes_read.value != 4
    ):
        return None

    return struct.unpack(
        "<i",
        buffer.raw
    )[0]


# ============================================================
# MEMORY WRITE
# ============================================================

def write_int32(
    handle,
    address,
    value
):
    data = struct.pack(
        "<i",
        value
    )

    bytes_written = ctypes.c_size_t()

    success = kernel32.WriteProcessMemory(
        handle,
        ctypes.c_void_p(address),
        data,
        len(data),
        ctypes.byref(bytes_written),
    )

    return (
        success
        and bytes_written.value == 4
    )


# ============================================================
# FIRST SCAN
# ============================================================

def scan_process(
    pid,
    target_value
):
    handle = open_process(pid)

    results = []

    target_bytes = struct.pack(
        "<i",
        target_value
    )

    address = 0

    mbi = MEMORY_BASIC_INFORMATION()

    while True:

        result = kernel32.VirtualQueryEx(
            handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi),
        )

        if result == 0:
            break

        base_address = (
            mbi.BaseAddress or 0
        )

        region_size = mbi.RegionSize

        readable = (
            mbi.State == MEM_COMMIT
            and not (
                mbi.Protect
                & PAGE_GUARD
            )
            and not (
                mbi.Protect
                & PAGE_NOACCESS
            )
        )

        if readable:

            try:
                buffer = (
                    ctypes.create_string_buffer(
                        region_size
                    )
                )

                bytes_read = (
                    ctypes.c_size_t()
                )

                success = (
                    kernel32.ReadProcessMemory(
                        handle,
                        ctypes.c_void_p(
                            base_address
                        ),
                        buffer,
                        region_size,
                        ctypes.byref(
                            bytes_read
                        ),
                    )
                )

                if success:

                    data = buffer.raw[
                        :bytes_read.value
                    ]

                    offset = 0

                    while True:

                        index = data.find(
                            target_bytes,
                            offset
                        )

                        if index == -1:
                            break

                        results.append(
                            base_address + index
                        )

                        offset = index + 4

            except (
                MemoryError,
                OSError
            ):
                pass

        next_address = (
            base_address
            + region_size
        )

        if next_address <= address:
            break

        address = next_address

    kernel32.CloseHandle(
        handle
    )

    return results


# ============================================================
# NEXT SCAN
# ============================================================

def next_scan(
    pid,
    target_value,
    previous_results
):
    handle = open_process(pid)

    filtered = []

    for address in previous_results:

        value = read_int32(
            handle,
            address
        )

        if value == target_value:
            filtered.append(
                address
            )

    kernel32.CloseHandle(
        handle
    )

    return filtered


# ============================================================
# RESULT STORAGE
# ============================================================

def save_results(results):
    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            results,
            file,
            indent=4
        )


def load_results():
    if not RESULTS_FILE.exists():
        return None

    with open(
        RESULTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# COMMANDS
# ============================================================

def command_first(
    pid,
    value
):
    session = create_new_session(
        pid
    )

    log(
        "========================================"
    )

    log(
        "GameSec Memory Scanner"
    )

    log(
        "========================================"
    )

    log(
        f"Target process: {PROCESS_NAME}"
    )

    log(
        f"PID: {pid}"
    )

    log(
        ""
    )

    log(
        "[FIRST SCAN]"
    )

    log(
        f"Target value: {value}"
    )

    log(
        "Scanning process memory..."
    )

    results = scan_process(
        pid,
        value
    )

    save_results(
        results
    )

    log(
        f"Candidates found: {len(results)}"
    )

    log(
        ""
    )

    log(
        f"Session log: {session['log_file']}"
    )


def command_next(
    pid,
    value
):
    previous_results = load_results()

    if previous_results is None:

        print(
            "Nenhum First Scan encontrado."
        )

        print(
            "Execute primeiro:"
        )

        print(
            "python scanner.py first 100"
        )

        sys.exit(1)

    session = load_session()

    if session is None:

        print(
            "Sessao nao encontrada."
        )

        print(
            "Execute novamente o First Scan."
        )

        sys.exit(1)

    if session["pid"] != pid:

        print(
            "O PID do processo mudou."
        )

        print(
            "O jogo provavelmente foi reiniciado."
        )

        print(
            "Execute um novo First Scan."
        )

        sys.exit(1)

    log(
        ""
    )

    log(
        "[NEXT SCAN]"
    )

    log(
        f"Target value: {value}"
    )

    log(
        f"Previous candidates: "
        f"{len(previous_results)}"
    )

    results = next_scan(
        pid,
        value,
        previous_results
    )

    save_results(
        results
    )

    log(
        f"Candidates remaining: "
        f"{len(results)}"
    )

    if len(results) <= 10:

        for address in results:

            log(
                f"Candidate: "
                f"{hex(address)}"
            )


def command_write(
    pid,
    value
):
    results = load_results()

    if not results:

        print(
            "Nenhum endereco encontrado."
        )

        sys.exit(1)

    session = load_session()

    if session is None:

        print(
            "Sessao nao encontrada."
        )

        sys.exit(1)

    if session["pid"] != pid:

        print(
            "O PID do processo mudou."
        )

        print(
            "Execute um novo First Scan."
        )

        sys.exit(1)

    if len(results) != 1:

        print(
            f"Ainda existem "
            f"{len(results)} candidatos."
        )

        print(
            "Continue usando Next Scan."
        )

        sys.exit(1)

    address = results[0]

    handle = open_process(
        pid
    )

    old_value = read_int32(
        handle,
        address
    )

    if old_value is None:

        kernel32.CloseHandle(
            handle
        )

        print(
            "Nao foi possivel ler "
            "o endereco."
        )

        sys.exit(1)

    log(
        ""
    )

    log(
        "[MEMORY WRITE]"
    )

    log(
        f"Address: {hex(address)}"
    )

    log(
        f"Old value: {old_value}"
    )

    log(
        f"New value: {value}"
    )

    success = write_int32(
        handle,
        address,
        value
    )

    if success:

        new_value = read_int32(
            handle,
            address
        )

        log(
            "Result: SUCCESS"
        )

        log(
            f"Confirmed value: {new_value}"
        )

    else:

        log(
            "Result: FAILED"
        )

    kernel32.CloseHandle(
        handle
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 3:

        print(
            "GameSec Memory Scanner"
        )

        print()
        print("Uso:")

        print(
            "python scanner.py first <valor>"
        )

        print(
            "python scanner.py next <valor>"
        )

        print(
            "python scanner.py write <valor>"
        )

        print()
        print("Exemplo:")

        print(
            "python scanner.py first 100"
        )

        print(
            "python scanner.py next 125"
        )

        print(
            "python scanner.py write 999"
        )

        sys.exit(1)

    command = (
        sys.argv[1].lower()
    )

    try:

        value = int(
            sys.argv[2]
        )

    except ValueError:

        print(
            "O valor precisa ser "
            "um numero inteiro."
        )

        sys.exit(1)

    pid = get_pid_by_name(
        PROCESS_NAME
    )

    if pid is None:

        print(
            f"{PROCESS_NAME} nao esta aberto."
        )

        sys.exit(1)

    if command == "first":

        command_first(
            pid,
            value
        )

    elif command == "next":

        command_next(
            pid,
            value
        )

    elif command == "write":

        command_write(
            pid,
            value
        )

    else:

        print(
            f"Comando invalido: {command}"
        )

        print(
            "Use first, next ou write."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()