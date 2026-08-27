import subprocess
import sys

try:
    import psutil
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil"])
    import psutil

BAR_WIDTH = 30


def bar(percent):
    filled = int(BAR_WIDTH * percent / 100)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


print("=" * 62)
print("               SKILLIFY SYSTEM RESOURCE CHECK")
print("=" * 62)

vm = psutil.virtual_memory()
total_gb = vm.total / (1024 ** 3)
used_gb = vm.used / (1024 ** 3)
avail_gb = vm.available / (1024 ** 3)
mem_pct = vm.percent

print()
print("  RAM (Memory)")
print(f"    Total      : {total_gb:6.2f} GB")
print(f"    Used       : {used_gb:6.2f} GB")
print(f"    Available  : {avail_gb:6.2f} GB")
print(f"    Usage      : {mem_pct:6.1f}%  {bar(mem_pct)}")

try:
    swing = vm.swap_total / (1024 ** 3) if vm.swap_total else 0
    swap_used = vm.swap_used / (1024 ** 3)
    print(f"    Swap Used  : {swap_used:6.2f} GB  (of {swing:.2f} GB)")
except Exception:
    pass

print()
print("  GPU")
gpu_found = False
try:
    out = subprocess.run(
        ["system_profiler", "SPDisplaysDataType"],
        capture_output=True, text=True, check=True,
    ).stdout
    for line in out.splitlines():
        s = line.strip()
        if s.lower().startswith("chipset model") or "total number of cores" in s.lower():
            print(f"    {s}")
            gpu_found = True
except Exception:
    pass

if not gpu_found:
    print("    (GPU info not available via psutil)")

try:
    import GPUtil as _g
except ImportError:
    _g = None

if _g:
    try:
        gpus = _g.getGPUs()
        for g in gpus:
            print(f"    {g.name}: {g.memoryUsed:.0f}/{g.memoryTotal:.0f} MB | load {g.load*100:.0f}%")
    except Exception:
        pass
else:
    print("    (Install GPUtil to see GPU memory/usage)")

print()
print("  CPU")
cpu_pct = psutil.cpu_percent(interval=1)
cpu_freq = psutil.cpu_freq()
print(f"    Cores      : {psutil.cpu_count(logical=True)} logical / {psutil.cpu_count(logical=False)} physical")
print(f"    Load       : {cpu_pct:5.1f}%  {bar(cpu_pct)}")
if cpu_freq:
    print(f"    Clock      : {cpu_freq.current / 1000:.2f} GHz")

PORT_NAMES = {
    8000: "Account Suggestions",
    8001: "Skill Quiz",
    8002: "CV Generator",
    8003: "Post Recommendations",
    5001: "AI Chatbot",
}

print()
print("  Running AI Services (by port)")
running = []
total_mem = 0
for port in sorted(PORT_NAMES):
    try:
        lsof = subprocess.run(
            ["lsof", "-nP", "-iTCP:%d" % port, "-sTCP:LISTEN"],
            capture_output=True, text=True,
        ).stdout
    except Exception:
        lsof = ""
    pid = None
    for line in lsof.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            try:
                pid = int(parts[1])
                break
            except ValueError:
                continue
    name = PORT_NAMES[port]
    if pid is None:
        running.append((name, port, None, 0.0, 0.0))
        continue
    try:
        total = 0.0
        procs = [psutil.Process(pid)]
        procs += psutil.Process(pid).children(recursive=True)
        for pr in procs:
            try:
                total += pr.memory_info().rss / (1024 ** 2)
            except Exception:
                pass
        cpu = psutil.Process(pid).cpu_percent(interval=None)
        running.append((name, port, pid, total, cpu))
        total_mem += total * (1024 ** 2)
    except Exception:
        running.append((name, port, pid, 0.0, 0.0))

if running:
    print(f"    {'Service':<24}{'Port':<7}{'PID':<8}{'RAM':<10}{'CPU'}")
    print("    " + "-" * 54)
    for name, port, pid, mem_mb, cpu in running:
        print(f"    {name:<24}{port:<7}{pid:<8}{mem_mb:>6.1f} MB  {cpu:>4.1f}%")
else:
    print("    None of the SKILLIFY services are currently running.")

print()
print("  COMBINED RAM NEEDED TO RUN ALL 5 AI SERVICES")
print("  " + "-" * 54)
if running:
    print(f"    Current running services : {total_mem / (1024 ** 2):.1f} MB")
else:
    print("    Current running services : 0 MB (none running)")
estimated = sum(
    {8000: 350, 8001: 450, 8002: 300, 8003: 300, 5001: 250}.values()
)
print(f"  Estimated total (all 5)  : {estimated} MB (≈ {estimated / 1024:.2f} GB)")
print(f"  Your available RAM      : {avail_gb:.2f} GB")
print(
    f"  Now running {'OK' if estimated / 1024 < avail_gb else 'MIGHT BE TIGHT'}"
    f" (needs {estimated / 1024:.2f} GB of {avail_gb:.2f} GB free)"
)

print()
print("  RAM NEEDED PER SERVICE (part by part)")
print("  " + "-" * 54)
PER_SERVICE = {
    "suggestions": 350,
    "quiz": 450,
    "cv": 300,
    "feed": 300,
    "chatbot": 250,
}
labels = {
    "suggestions": "Account Suggestions (:8000)",
    "quiz": "Skill Quiz (:8001)",
    "cv": "CV Generator (:8002)",
    "feed": "Post Recommendations (:8003)",
    "chatbot": "AI Chatbot (:5001)",
}
per_key_port = {
    "suggestions": 8000,
    "quiz": 8001,
    "cv": 8002,
    "feed": 8003,
    "chatbot": 5001,
}
running_ports = {p for _, p, _, _, _ in running}
cumulative = 0
for key, mb in PER_SERVICE.items():
    cumulative += mb
    port = per_key_port[key]
    actual = next((m for n, p, pid, m, c in running if p == port), None)
    status = "RUNNING" if port in running_ports else "not running"
    if actual is not None:
        print(f"    {labels[key]:<28}{actual:>8.1f} MB   ({status}, measured)  est {mb} MB")
    else:
        print(f"    {labels[key]:<28}{mb:>5} MB   ({status}, estimate)")
print("    " + "-" * 54)
print(f"    {'TOTAL (measured)':<28}{total_mem / (1024 ** 2):>8.1f} MB")
print(f"    {'TOTAL (if all est)':<28}{cumulative:>5} MB   (≈ {cumulative / 1024:.2f} GB)")

print()
print("=" * 62)
