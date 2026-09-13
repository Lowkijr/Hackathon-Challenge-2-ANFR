from concurrent.futures import ThreadPoolExecutor
import requests

def download_single_file(args):
    url, output_path = args
    if not output_path.exists():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                output_path.write_bytes(r.content)
                return True
        except Exception:
            pass
    return False

def download_batch(download_tasks, max_workers=16):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(download_single_file, download_tasks))
    return sum(results)