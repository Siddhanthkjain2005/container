import time
import sys
import array

def stress_memory(size_mb, duration):
    print(f"Allocating {size_mb}MB of memory...")
    try:
        data = array.array("B", [0] * (size_mb * 1024 * 1024))
        print(f"Allocated {size_mb}MB. Holding for {duration} seconds...")
        time.sleep(duration)
        print("Releasing memory.")
    except MemoryError:
        print("Failed to allocate memory: MemoryError")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 stress_mem.py <size_mb> <duration>")
        sys.exit(1)
    
    size = int(sys.argv[2]) if sys.argv[1].startswith("--") else int(sys.argv[1])
    dur = int(sys.argv[2]) if not sys.argv[1].startswith("--") else int(sys.argv[2]) 
    # Handle both orderings just in case
    try:
        size = int(sys.argv[1])
        dur = int(sys.argv[2])
    except:
        size = int(sys.argv[2])
        dur = int(sys.argv[1])

    stress_memory(size, dur)
