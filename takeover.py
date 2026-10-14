import requests
import urllib3
import concurrent.futures
import time
import sys
import os
import dns.resolver
import socket
import platform
import threading
from colorama import Fore, init

# ==========================================================
# TAKEOVER-GSC v1.0 - bot-gsc v1.0 (Auth Loop Fixed)
# ==========================================================

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
file_lock = threading.Lock()

# --- SECURITY: Obfuscated Auth Endpoint ---
p_a = "https://raw.github"
p_b = "usercontent.com/"
p_c = "gscx303/tools/refs/"
p_d = "heads/main/key.txt"
_v_endpoint = p_a + p_b + p_c + p_d 

def get_sys_info():
    device = platform.node()
    current_time = time.strftime("%H:%M:%S")
    return f"{Fore.YELLOW}DEVICE: {Fore.WHITE}{device} | {Fore.YELLOW}TIME: {Fore.WHITE}{current_time}"

def verify_access():
    """Fungsi Auth dengan sistem Looping jika gagal"""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{Fore.CYAN}==============================================")
        print(f"{Fore.WHITE}      {Fore.YELLOW}TAKEOVER-GSC{Fore.WHITE} - bot-gsc v1.0        ")
        print(f"{Fore.CYAN}==============================================")
        print(get_sys_info())
        print(f"{Fore.CYAN}==============================================")
        
        token = input(f"{Fore.WHITE}[?] Enter Auth Key: {Fore.WHITE}").strip()
        
        if not token:
            continue

        try:
            # Mengambil data kunci dari server
            req = requests.get(_v_endpoint, timeout=10)
            if req.status_code == 200:
                valid_keys = req.text.splitlines()
                # Cek apakah token ada di dalam list keys.txt
                if token in [k.strip() for k in valid_keys]:
                    print(f"{Fore.GREEN}[+] Access Granted! Welcome...")
                    time.sleep(1)
                    return True # Berhasil, lanjut ke menu utama
                else:
                    print(f"{Fore.RED}[!] Access Denied: Invalid Key.")
                    time.sleep(2) # Memberi jeda agar user bisa baca pesan error
                    # Loop akan otomatis mengulang ke input awal
            else:
                print(f"{Fore.RED}[!] Server Error ({req.status_code}). Try again later.")
                sys.exit()
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}[!] Connection Error: Check your internet.")
            time.sleep(2)
        except Exception as e:
            print(f"{Fore.RED}[!] An error occurred. Please restart.")
            sys.exit()

# --- SISANYA TETAP SAMA (Scanner Logic) ---

class GSCScanner:
    def __init__(self):
        self.output_vuln = "results_takeover.txt"
        self.output_200 = "live_200.txt"
        self.output_ports = "port_scan_results.txt"
        self.output_dead = "404.txt"  # <-- Tambahkan ini untuk menampung domain mati
        self.threads = 60

    def write_safe(self, filepath, data):
        with file_lock:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(data + "\n")
                f.flush()
                os.fsync(f.fileno())

    def log_activity(self, status, url, extra=""):
        timestamp = time.strftime("%H:%M:%S")
        colors = {"VULN": Fore.RED, "DNS": Fore.MAGENTA, "LIVE": Fore.GREEN, "PORT": Fore.CYAN, "SCAN": Fore.YELLOW}
        color = colors.get(status, Fore.WHITE)
        with file_lock:
            sys.stdout.write(f"{Fore.WHITE}[{timestamp}] {color}[{status[0]}] {url.ljust(35)} {Fore.WHITE}| {extra}\n")
            sys.stdout.flush()

    def find_subdomains(self):
        domain = input(f"{Fore.YELLOW}[?] Target Domain: {Fore.WHITE}").strip()
        if not domain: return
        with open("targets.txt", "w") as f: pass
        print(f"{Fore.CYAN}[*] Fetching from crt.sh...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", headers=headers, timeout=60)
            if r.status_code == 200:
                subs = {s.strip() for item in r.json() for s in item['name_value'].lower().split("\n") if domain in s and "*" not in s}
                for s in sorted(subs): self.write_safe("targets.txt", s)
                print(f"{Fore.GREEN}[+] Found {len(subs)} subdomains.")
        except: print(f"{Fore.RED}[!] Failed to fetch subdomains.")

    def run(self, mode):
        if mode == '1': self.find_subdomains(); return
        
        # Tambahkan self.output_dead ke dalam daftar mapping mode '2'
        f_map = {
            '2': [self.output_200, self.output_dead], 
            '3': [self.output_vuln], 
            '4': [self.output_ports]
        }
        for f in f_map.get(mode, []):
            with open(f, "w") as empty: pass

        source = "targets.txt" if mode in ['2', '3'] else "live_200.txt"
        if not os.path.exists(source): return
        with open(source, "r") as f:
            targets = [l.strip() for l in f if l.strip()]

        print(f"\n{Fore.CYAN}[SYSTEM] Running Step {mode} on {len(targets)} targets...\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            if mode == '2': executor.map(self.step_1_filter, targets)
            elif mode == '3': executor.map(self.step_2_takeover, targets)
            elif mode == '4': executor.map(self.step_3_port_scan, targets)
            executor.shutdown(wait=True)

    # ... (Logic step_1, step_2, step_3 tetap sama seperti sebelumnya) ...
    def step_1_filter(self, url):
        t_url = url if url.startswith('http') else 'https://' + url
        try:
            # Menggunakan cetakan verify=False dan timeout agar tidak menggantung lama
            r = requests.get(t_url, timeout=5, verify=False)
            
            if r.status_code == 200:
                self.log_activity("LIVE", url, "200 OK")
                self.write_safe(self.output_200, t_url)
            else:
                # Jika terhubung tapi statusnya bukan 200 (misal: 404, 500, 403)
                self.log_activity("SCAN", url, f"Status: {r.status_code}")
                self.write_safe(self.output_dead, url)
                
        except requests.exceptions.RequestException:
            # Jika koneksi gagal total (Timeout, DNS gagal, NXDOMAIN, dll)
            self.log_activity("SCAN", url, "DEAD/TIMEOUT")
            self.write_safe(self.output_dead, url)
        except Exception:
            pass

    def step_2_takeover(self, url):
        domain = url.replace('https://','').replace('http://','').split('/')[0]
        try:
            ans = dns.resolver.resolve(domain, 'CNAME')
            # (Logic takeover dilanjutkan di sini)
        except: pass

    def step_3_port_scan(self, url):
        domain = url.replace('https://','').replace('http://','').split('/')[0]
        found = []
        for p in [21, 22, 80, 443, 8080]: # Contoh port
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.7)
                    if s.connect_ex((domain, p)) == 0: found.append(str(p))
            except: pass
        if found:
            self.log_activity("PORT", domain, f"Open: {', '.join(found)}")
            self.write_safe(self.output_ports, f"{domain} | {', '.join(found)}")

def show_menu():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Fore.CYAN}==============================================")
    print(f"{Fore.WHITE}      {Fore.YELLOW}TAKEOVER-GSC{Fore.WHITE} - bot-gsc v1.0        ")
    print(f"{Fore.CYAN}==============================================")
    print(get_sys_info())
    print(f"{Fore.CYAN}==============================================")
    print(f"{Fore.WHITE}[1] {Fore.GREEN}Subdomain Finder")
    print(f"{Fore.WHITE}[2] {Fore.GREEN}Filter Alive")
    print(f"{Fore.WHITE}[3] {Fore.GREEN}Takeover Scan")
    print(f"{Fore.WHITE}[4] {Fore.GREEN}Port Scanner")
    print(f"{Fore.WHITE}[5] {Fore.RED}Exit")
    print(f"{Fore.CYAN}==============================================")
    return input(f"{Fore.YELLOW}Pilih Opsi (1-5): {Fore.WHITE}")

if __name__ == "__main__":
    if verify_access(): # Jika verify_access mengembalikan True
        while True:
            choice = show_menu()
            if choice == '5': break
            scanner = GSCScanner()
            if choice in ['1','2','3','4']:
                scanner.run(choice)
                input(f"\n{Fore.YELLOW}Press Enter to continue...");
