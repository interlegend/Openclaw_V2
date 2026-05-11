from pathlib import Path
import psutil
import time

def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    
    # Cross-platform drive detection
    drive = Path.home().anchor or "C:\\"
    disk = psutil.disk_usage(drive)
    
    # Top 5 processes by CPU usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    
    summary = f"📊 **System Stats**\n\n"
    summary += f"💻 **CPU:** {cpu_usage}%\n"
    summary += f"🧠 **RAM:** {ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB ({ram.percent}%)\n"
    summary += f"💾 **Disk:** {disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB ({disk.percent}%)\n\n"
    summary += f"🔝 **Top 5 Processes:**\n"
    for p in top_processes:
        summary += f"- {p['name']} (PID: {p['pid']}): {p['cpu_percent']}%\n"
    
    return summary

def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    top_20 = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:20]
    
    summary = "📋 **Top 20 Processes by CPU:**\n\n"
    summary += f"{'PID':<7} {'Name':<20} {'CPU%':<7} {'RAM%':<7}\n"
    summary += "—" * 45 + "\n"
    for p in top_20:
        summary += f"{p['pid']:<7} {p['name'][:20]:<20} {p['cpu_percent']:<7.1f} {p['memory_percent']:<7.1f}\n"
    
    return summary
