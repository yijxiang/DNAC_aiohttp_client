import time


def get_current_time():
    return int(time.time() * 1000)


def create_url(path, controller_ip, port, basic_path="/dna/intent/api/v1/"):
    return f"https://{controller_ip}:{port}{basic_path}{path}"


