import psutil
import json
import time as t
import schedule
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"  # Change this if your MongoDB server is running on a different host/port
DB_NAME = "test_ressource"
COLLECTION_NAME = "ram"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_system_status():
    # Get CPU usage
    cpu_usage = psutil.cpu_percent(interval=1, percpu=True)

    # Get RAM usage
    virtual_memory = psutil.virtual_memory()
    ram_total = virtual_memory.total
    ram_used = virtual_memory.used
    ram_free = virtual_memory.available
    ram_usage_percent = virtual_memory.percent

    # Get disk usage
    disk_usage = psutil.disk_usage('/')
    disk_total = disk_usage.total
    disk_used = disk_usage.used
    disk_free = disk_usage.free
    disk_usage_percent = disk_usage.percent

    # Get swap memory usage
    swap = psutil.swap_memory()
    swap_total = swap.total
    swap_used = swap.used
    swap_free = swap.free
    swap_usage_percent = swap.percent

    # Get system uptime
    uptime = psutil.boot_time()

    # Prepare status report
    status = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "cpu_usage_per_core": cpu_usage,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "ram_free": ram_free,
        "ram_usage_percent": ram_usage_percent,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_free": disk_free,
        "disk_usage_percent": disk_usage_percent,
        "swap_total": swap_total,
        "swap_used": swap_used,
        "swap_free": swap_free,
        "swap_usage_percent": swap_usage_percent,
        "uptime": uptime
    }

    return status

def bytes_to_human_readable(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"

def display_system_status():
    status = get_system_status()

    # Print the status in a human-readable format
    print(f"Timestamp: {status['timestamp']}")
    print("CPU Usage Per Core:")
    for i, usage in enumerate(status['cpu_usage_per_core']):
        print(f"Core {i}: {usage}%")

    print("\nRAM Usage:")
    print(f"Total: {bytes_to_human_readable(status['ram_total'])}")
    print(f"Used: {bytes_to_human_readable(status['ram_used'])}")
    print(f"Free: {bytes_to_human_readable(status['ram_free'])}")
    print(f"Usage: {status['ram_usage_percent']}%")

    print("\nDisk Usage:")
    print(f"Total: {bytes_to_human_readable(status['disk_total'])}")
    print(f"Used: {bytes_to_human_readable(status['disk_used'])}")
    print(f"Free: {bytes_to_human_readable(status['disk_free'])}")
    print(f"Usage: {status['disk_usage_percent']}%")

    print("\nSwap Usage:")
    print(f"Total: {bytes_to_human_readable(status['swap_total'])}")
    print(f"Used: {bytes_to_human_readable(status['swap_used'])}")
    print(f"Free: {bytes_to_human_readable(status['swap_free'])}")
    print(f"Usage: {status['swap_usage_percent']}%")

    print("\nSystem Uptime:")
    print(f"Uptime: {datetime.fromtimestamp(status['uptime']).strftime('%Y-%m-%d %H:%M:%S')}")

    # Save the status to a JSON file
    with open('system_status.json', 'a') as f:
        json.dump(status, f, indent=4, default=str)
        f.write('\n')

    # Save the status to MongoDB
    collection.insert_one(status)
    print("Status saved to MongoDB")

if __name__ == "__main__":
    # Schedule the display_system_status function to run every 1 minute
    schedule.every(1).minutes.do(display_system_status)

    # Keep the script running
    while True:
        schedule.run_pending()
        t.sleep(1)
