import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
CLOUDFLARED = BASE / 'cloudflared.exe'
ONLINE_URL = BASE / 'online_url.txt'
LOG = BASE / 'cloudflared.log'
DOWNLOAD = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
PORT = 8787


def ensure_cloudflared():
    if CLOUDFLARED.exists() and CLOUDFLARED.stat().st_size > 1_000_000:
        return
    print('[ONLINE] Baixando componente de acesso online...')
    urllib.request.urlretrieve(DOWNLOAD, CLOUDFLARED)


def pipe_output(proc):
    pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
    found = False
    with LOG.open('w', encoding='utf-8', errors='ignore') as log:
        for raw in iter(proc.stdout.readline, ''):
            if not raw:
                break
            print(raw, end='')
            log.write(raw); log.flush()
            match = pattern.search(raw)
            if match and not found:
                found = True
                url = match.group(0).rstrip('/')
                ONLINE_URL.write_text(url, encoding='utf-8')
                print('\n===================================================')
                print(' MODO ONLINE ATIVO')
                print(' Painel celular:', url + '/painel')
                print(' Jogo celular  :', url + '/overlay?modo=celular')
                print(' Nao feche esta janela enquanto estiver usando.')
                print('===================================================\n')
                time.sleep(1)
                webbrowser.open(f'http://127.0.0.1:{PORT}/painel')


def main():
    os.chdir(BASE)
    try: ONLINE_URL.unlink(missing_ok=True)
    except Exception: pass
    ensure_cloudflared()
    server = subprocess.Popen([sys.executable, 'main.py'], cwd=BASE)
    time.sleep(3)
    tunnel = subprocess.Popen(
        [str(CLOUDFLARED), 'tunnel', '--url', f'http://127.0.0.1:{PORT}', '--no-autoupdate'],
        cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace', bufsize=1
    )
    threading.Thread(target=pipe_output, args=(tunnel,), daemon=True).start()
    try:
        while server.poll() is None and tunnel.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (tunnel, server):
            try: proc.terminate()
            except Exception: pass
        try: ONLINE_URL.unlink(missing_ok=True)
        except Exception: pass

if __name__ == '__main__':
    main()
