# test_welcome.py
from src.tasks.hi import welcome

if __name__ == "__main__":
    result = welcome.delay()
    print("Task sent! ID:", result.id)
    print("Waiting for result...")
    print("Result:", result.get(timeout=10))
