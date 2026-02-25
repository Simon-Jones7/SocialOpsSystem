import os
import time


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    print(f"[worker] started with REDIS_URL={redis_url}")
    print("[worker] placeholder loop running; no jobs are processed yet.")
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
