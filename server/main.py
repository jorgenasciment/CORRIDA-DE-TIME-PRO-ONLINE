import json, time, threading, urllib.parse, urllib.request, urllib.error, mimetypes, queue, re, socket, io, os, base64, hashlib, hmac, os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).parent
CONFIG_PATH = BASE / 'config.json'
ONLINE_URL_PATH = BASE / 'online_url.txt'
GAME_STATE_PATH = BASE / 'game_state.json'

# Segurança e persistência online via variáveis do Render
AUTH_USER = os.environ.get("AUTH_USER", "admin").strip() or "admin"
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "").strip()
AUTH_SECRET = os.environ.get("AUTH_SECRET", "").strip() or hashlib.sha256((AUTH_USER + ":" + AUTH_PASSWORD + ":corrida-pro").encode()).hexdigest()
COOKIE_NAME = "corrida_pro_session"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
GITHUB_STATE_PATH = os.environ.get("GITHUB_STATE_PATH", "cloud/game_state.json").strip() or "cloud/game_state.json"
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main").strip() or "main"
CLOUD_SAVE_LOCK = threading.Lock()
CLOUD_SAVE_TIMER = None
LOGIN_HTML = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEARENSE GAMER</title><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at top,#16305e,#070b16 65%);font-family:Arial;color:#fff}.box{width:min(92vw,390px);background:#111a2b;border:1px solid #33476d;border-radius:20px;padding:28px;box-shadow:0 20px 60px #0009}h1{text-align:center;color:#ffd21a}.sub{text-align:center;color:#aab8d4}.erro{background:#681e2b;border:1px solid #ef5f73;padding:10px;border-radius:9px}label{display:block;margin:12px 0 6px;font-weight:bold}input{width:100%;padding:14px;border-radius:10px;border:1px solid #425477;background:#09101e;color:#fff;font-size:17px}button{width:100%;margin-top:20px;padding:14px;border:0;border-radius:11px;background:#ffd21a;color:#111;font-weight:900;font-size:17px}.lock{text-align:center;font-size:38px}</style></head><body><form class="box" method="post" action="/login"><div class="lock">🔒</div><h1>CEARENSE GAMER</h1><p class="sub">Acesso exclusivo</p>__ERRO__<label>Usuário</label><input name="username" required autofocus><label>Senha</label><input name="password" type="password" required><input type="hidden" name="next" value="__NEXT__"><button>ENTRAR</button></form></body></html>"""

DEFAULT_CONFIG = {
    'port': 8787,
    'meta': 300,
    'show_finish_label': True,
    'finish_label_text': 'CHEGADA',
    'finish_label_size': 15,
    'finish_label_x': 0,
    'finish_label_y': 50,
    'finish_label_rotation': -90,
    'finish_label_color': '#ffffff',
    'finish_label_glow_color': '#00e6ff',
    'finish_label_glow': 13,
    'comment_points': 0,
    'diamond_multiplier': 1,
    'gift_default': 25,
    'champion_duration': 8,
    'tournament_timer_enabled': False,
    'tournament_minutes': 5,
    'tournament_timer_opacity': 100,
    'champion_size': 120,
    'champion_name_size': 38,
    'show_goal_text': False,
    'show_champion_name': True,
    'show_live_status': False,
    'show_ranking': True,
    'show_top5': False,
    'ranking_scale': 115,
    'ranking_logo_size': 42,
    'ranking_score_size': 30,
    'ranking_logo_x': 0,
    'ranking_logo_y': 0,
    'ranking_score_x': 0,
    'ranking_score_y': 0,
    'ranking_victory_x': 0,
    'ranking_victory_y': 0,
    'ranking_position_size': 17,
    'ranking_gap': 4,
    'ranking_height': 78,
    'ranking_title_text': '🏆 MAIORES CAMPEÕES',
    'show_ranking_title': True,
    'ranking_title_x': 50,
    'ranking_title_y': 4,
    'ranking_title_scale': 100,
    'ranking_title_color': '#ffd400',
    'show_race_rank_title': True,
    'race_rank_title_text': '📊 RANKING',
    'race_rank_title_x': 50,
    'race_rank_title_y': 8,
    'race_rank_title_width': 88,
    'race_rank_title_height': 38,
    'race_rank_title_scale': 100,
    'race_rank_title_color': '#ffffff',
    'effect_time': 1,
    'lightning_power': 100,
    'ultra_gift_enabled': True,
    'ultra_gift_threshold': 99,
    'ultra_gift_text': '🔥 MODO ULTRA GIFT 🔥',
    'ultra_gift_duration': 3,
    'ultra_gift_cinematic': True,
    'ultra_gift_slowmo': True,
    'ultra_gift_dim': True,
    'ultra_gift_shockwave': True,
    'ultra_gift_particles': True,
    'ultra_gift_rays': True,
    'comment_enabled': True,
    'gift_enabled': True,
    'like_enabled': False,
    'likes_required': 100,
    'like_points': 1,
    'teams': [{'name': 'Athletico-PR', 'abbr': 'CAP', 'color': '#d71920', 'logo': 'assets/logos/CAP.png', 'keywords': ['Athletico-PR', 'CAP', 'athletico pr', 'athletico', 'athletico paranaense', 'cap', 'furacao', 'furacão']}, {'name': 'Atlético-MG', 'abbr': 'CAM', 'color': '#f1f1f1', 'logo': 'assets/logos/CAM.png', 'keywords': ['Atlético-MG', 'CAM', 'atletico mg', 'atlético mg', 'atlético mineiro', 'atletico mineiro', 'cam', 'galo']}, {'name': 'Bahia', 'abbr': 'BAH', 'color': '#008ee6', 'logo': 'assets/logos/BAH.png', 'keywords': ['Bahia', 'BAH', 'bahia', 'bah', 'esquadrao', 'esquadrão']}, {'name': 'Botafogo', 'abbr': 'BOT', 'color': '#eeeeee', 'logo': 'assets/logos/BOT.png', 'keywords': ['Botafogo', 'BOT', 'botafogo', 'bot', 'fogao', 'fogão']}, {'name': 'Chapecoense', 'abbr': 'CHA', 'color': '#1fad4b', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Chapecoense', 'CHA', 'chapecoense', 'chape', 'cha']}, {'name': 'Corinthians', 'abbr': 'COR', 'color': '#eeeeee', 'logo': 'assets/logos/COR.png', 'keywords': ['Corinthians', 'COR', 'corinthians', 'cor', 'timao', 'timão']}, {'name': 'Coritiba', 'abbr': 'CTB', 'color': '#159447', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Coritiba', 'CTB', 'coritiba', 'coxa', 'ctb']}, {'name': 'Cruzeiro', 'abbr': 'CRU', 'color': '#0057b8', 'logo': 'assets/logos/CRU.png', 'keywords': ['Cruzeiro', 'CRU', 'cruzeiro', 'cru', 'raposa']}, {'name': 'Flamengo', 'abbr': 'FLA', 'color': '#e90016', 'logo': 'assets/logos/FLA.png', 'keywords': ['Flamengo', 'FLA', 'flamengo', 'fla', 'mengao', 'mengão']}, {'name': 'Fluminense', 'abbr': 'FLU', 'color': '#006b3f', 'logo': 'assets/logos/FLU.png', 'keywords': ['Fluminense', 'FLU', 'fluminense', 'flu', 'tricolor carioca']}, {'name': 'Grêmio', 'abbr': 'GRE', 'color': '#00a3e0', 'logo': 'assets/logos/GRE.png', 'keywords': ['Grêmio', 'GRE', 'gremio', 'grêmio', 'gre']}, {'name': 'Internacional', 'abbr': 'INT', 'color': '#df0000', 'logo': 'assets/logos/INT.png', 'keywords': ['Internacional', 'INT', 'internacional', 'inter', 'int', 'colorado']}, {'name': 'Mirassol', 'abbr': 'MIR', 'color': '#d4d400', 'logo': 'assets/logos/MIR.png', 'keywords': ['Mirassol', 'MIR', 'mirassol', 'mir']}, {'name': 'Palmeiras', 'abbr': 'PAL', 'color': '#22b14c', 'logo': 'assets/logos/PAL.png', 'keywords': ['Palmeiras', 'PAL', 'palmeiras', 'pal', 'porco', 'verdao', 'verdão']}, {'name': 'RB Bragantino', 'abbr': 'RBB', 'color': '#e40046', 'logo': 'assets/logos/RBB.png', 'keywords': ['RB Bragantino', 'RBB', 'bragantino', 'rb bragantino', 'red bull bragantino', 'rbb']}, {'name': 'Remo', 'abbr': 'REM', 'color': '#003b75', 'logo': 'assets/logos/REM.png', 'keywords': ['Remo', 'REM', 'remo', 'rem']}, {'name': 'Santos', 'abbr': 'SAN', 'color': '#eeeeee', 'logo': 'assets/logos/SAN.png', 'keywords': ['Santos', 'SAN', 'santos', 'san', 'peixe']}, {'name': 'São Paulo', 'abbr': 'SPFC', 'color': '#d71920', 'logo': 'assets/logos/SPFC.png', 'keywords': ['São Paulo', 'SPFC', 'sao paulo', 'são paulo', 'spfc', 'tricolor paulista']}, {'name': 'Vasco', 'abbr': 'VAS', 'color': '#eeeeee', 'logo': 'assets/logos/VAS.png', 'keywords': ['Vasco', 'VAS', 'vasco', 'vas', 'vasco da gama']}, {'name': 'Vitória', 'abbr': 'VIT', 'color': '#c90000', 'logo': 'assets/logos/VIT.png', 'keywords': ['Vitória', 'VIT', 'vitoria', 'vitória', 'vit']}, {'name': 'Vila Nova', 'abbr': 'VNO', 'color': '#d71920', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Vila Nova', 'VNO', 'vila nova', 'vila', 'vno', 'tigrão', 'tigrao']}, {'name': 'Fortaleza', 'abbr': 'FOR', 'color': '#0067b1', 'logo': 'assets/logos/FOR.png', 'keywords': ['Fortaleza', 'FOR', 'fortaleza', 'for', 'leao', 'leão']}, {'name': 'Ceará', 'abbr': 'CEA', 'color': '#eeeeee', 'logo': 'assets/logos/CEA.png', 'keywords': ['Ceará', 'CEA', 'ceara', 'ceará', 'cea', 'vozao', 'vozão']}, {'name': 'Novorizontino', 'abbr': 'NOV', 'color': '#f2c300', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Novorizontino', 'NOV', 'novorizontino', 'gremio novorizontino', 'grêmio novorizontino', 'nov']}, {'name': 'Avaí', 'abbr': 'AVA', 'color': '#0067b1', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Avaí', 'AVA', 'avai', 'avaí', 'ava']}, {'name': 'Athletic Club', 'abbr': 'ATH', 'color': '#111111', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Athletic Club', 'ATH', 'athletic', 'athletic club', 'ath']}, {'name': 'Operário-PR', 'abbr': 'OPE', 'color': '#eeeeee', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Operário-PR', 'OPE', 'operario', 'operário', 'operario pr', 'operário pr', 'ope']}, {'name': 'Botafogo-SP', 'abbr': 'BSP', 'color': '#eeeeee', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Botafogo-SP', 'BSP', 'botafogo sp', 'botafogo-sp', 'botafogo ribeirao', 'botafogo ribeirão', 'bsp']}, {'name': 'São Bernardo', 'abbr': 'SBE', 'color': '#f2d000', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['São Bernardo', 'SBE', 'sao bernardo', 'são bernardo', 'sbe']}, {'name': 'Criciúma', 'abbr': 'CRI', 'color': '#f5d20a', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Criciúma', 'CRI', 'criciuma', 'criciúma', 'cri', 'tigre']}, {'name': 'Juventude', 'abbr': 'JUV', 'color': '#149657', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Juventude', 'JUV', 'juventude', 'juv']}, {'name': 'Goiás', 'abbr': 'GOI', 'color': '#0c8c42', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Goiás', 'GOI', 'goias', 'goiás', 'goi', 'esmeraldino']}, {'name': 'Sport', 'abbr': 'SPT', 'color': '#e00000', 'logo': 'assets/logos/SPT.png', 'keywords': ['Sport', 'SPT', 'sport', 'sport recife', 'spt', 'leao da ilha', 'leão da ilha']}, {'name': 'Náutico', 'abbr': 'NAU', 'color': '#e00000', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Náutico', 'NAU', 'nautico', 'náutico', 'nau', 'timbu']}, {'name': 'Cuiabá', 'abbr': 'CUI', 'color': '#d9c300', 'logo': 'assets/logos/CUI.png', 'keywords': ['Cuiabá', 'CUI', 'cuiaba', 'cuiabá', 'cui', 'dourado']}, {'name': 'Londrina', 'abbr': 'LON', 'color': '#00a6df', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Londrina', 'LON', 'londrina', 'lon', 'tubarao', 'tubarão']}, {'name': 'Atlético-GO', 'abbr': 'ACG', 'color': '#e00000', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Atlético-GO', 'ACG', 'atletico go', 'atlético go', 'atletico goianiense', 'atlético goianiense', 'acg', 'dragao', 'dragão']}, {'name': 'Ponte Preta', 'abbr': 'PON', 'color': '#eeeeee', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['Ponte Preta', 'PON', 'ponte preta', 'ponte', 'pon', 'macaca']}, {'name': 'CRB', 'abbr': 'CRB', 'color': '#e00000', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['CRB', 'crb', 'regatas']}, {'name': 'América-MG', 'abbr': 'AME', 'color': '#159447', 'logo': 'assets/logos/_FALTA_ESCUDO.png', 'keywords': ['América-MG', 'AME', 'america mg', 'américa mg', 'america mineiro', 'américa mineiro', 'ame', 'coelho']}],
}

def load_config():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        out = DEFAULT_CONFIG.copy(); out.update(data); return out
    except Exception:
        return DEFAULT_CONFIG.copy()

CONFIG = load_config()
PORT = int(os.environ.get('PORT', CONFIG.get('port', 8787)))

def _normalize_state(data):
    if not isinstance(data, dict): return None
    data.setdefault('teams', {}); data.setdefault('scorers', {}); data.setdefault('updated_at', 0)
    if not isinstance(data['teams'], dict) or not isinstance(data['scorers'], dict): return None
    return data

def _github_api_url():
    if not (GITHUB_TOKEN and GITHUB_REPO): return ''
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{urllib.parse.quote(GITHUB_STATE_PATH, safe='/')}"

def load_cloud_game_state():
    url = _github_api_url()
    if not url: return None
    try:
        req=urllib.request.Request(url+'?'+urllib.parse.urlencode({'ref':GITHUB_BRANCH}),headers={'Authorization':f'Bearer {GITHUB_TOKEN}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Corrida-De-Time-PRO'})
        with urllib.request.urlopen(req,timeout=12) as r: meta=json.loads(r.read().decode())
        state=_normalize_state(json.loads(base64.b64decode(meta.get('content','')).decode('utf-8')))
        if state: print('[NUVEM] Histórico carregado.')
        return state
    except urllib.error.HTTPError as e:
        if e.code != 404: print('[NUVEM] Falha ao carregar:',e)
    except Exception as e: print('[NUVEM] Falha ao carregar:',repr(e))
    return None

def load_game_state():
    cloud=load_cloud_game_state()
    if cloud: return cloud
    try:
        data=_normalize_state(json.loads(GAME_STATE_PATH.read_text(encoding='utf-8')))
        if data: return data
    except Exception: pass
    return {'teams': {}, 'scorers': {}, 'updated_at': 0}

def _github_request(url, method='GET', payload=None, timeout=15):
    headers={
        'Authorization':f'Bearer {GITHUB_TOKEN}',
        'Accept':'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28',
        'User-Agent':'Corrida-De-Time-PRO',
        'Content-Type':'application/json',
    }
    data=None if payload is None else json.dumps(payload).encode('utf-8')
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
        return json.loads(raw.decode('utf-8')) if raw else {}


def _initialize_empty_github_repo(snapshot):
    """Cria o primeiro commit quando o repositório de dados ainda está totalmente vazio."""
    api=f'https://api.github.com/repos/{GITHUB_REPO}'
    content=json.dumps(snapshot,ensure_ascii=False,indent=2).encode('utf-8')
    blob=_github_request(api+'/git/blobs','POST',{
        'content':base64.b64encode(content).decode('ascii'),
        'encoding':'base64',
    })
    tree=_github_request(api+'/git/trees','POST',{
        'tree':[{'path':GITHUB_STATE_PATH,'mode':'100644','type':'blob','sha':blob['sha']}]
    })
    commit=_github_request(api+'/git/commits','POST',{
        'message':'Primeiro salvamento do Corrida de Time PRO',
        'tree':tree['sha'],
        'parents':[],
    })
    _github_request(api+'/git/refs','POST',{
        'ref':f'refs/heads/{GITHUB_BRANCH}',
        'sha':commit['sha'],
    })
    print('[NUVEM] Repositório de dados inicializado e histórico salvo.')


def _save_cloud_snapshot(snapshot):
    url=_github_api_url()
    if not url: return
    with CLOUD_SAVE_LOCK:
        try:
            sha=None
            repo_empty=False
            try:
                meta=_github_request(url+'?'+urllib.parse.urlencode({'ref':GITHUB_BRANCH}))
                sha=meta.get('sha')
            except urllib.error.HTTPError as e:
                body=''
                try: body=e.read().decode('utf-8',errors='replace')
                except Exception: pass
                if e.code in (404,409,422):
                    repo_empty=('empty' in body.lower() or 'branch' in body.lower() or e.code==409)
                else:
                    raise

            payload={
                'message':'Salvamento automático do Corrida de Time PRO',
                'content':base64.b64encode(json.dumps(snapshot,ensure_ascii=False,indent=2).encode()).decode(),
                'branch':GITHUB_BRANCH,
            }
            if sha: payload['sha']=sha
            try:
                _github_request(url,'PUT',payload)
            except urllib.error.HTTPError as e:
                body=''
                try: body=e.read().decode('utf-8',errors='replace')
                except Exception: pass
                if repo_empty or e.code in (409,422) or 'empty' in body.lower() or 'branch' in body.lower():
                    _initialize_empty_github_repo(snapshot)
                    return
                raise
            print('[NUVEM] Histórico salvo automaticamente.')
        except Exception as e: print('[NUVEM] Falha ao salvar:',repr(e))

def schedule_cloud_save(snapshot):
    global CLOUD_SAVE_TIMER
    if not _github_api_url(): return
    if CLOUD_SAVE_TIMER is not None:
        try: CLOUD_SAVE_TIMER.cancel()
        except Exception: pass
    CLOUD_SAVE_TIMER=threading.Timer(4.0,_save_cloud_snapshot,args=(snapshot,)); CLOUD_SAVE_TIMER.daemon=True; CLOUD_SAVE_TIMER.start()

def save_game_state():
    tmp=GAME_STATE_PATH.with_suffix('.json.tmp')
    snapshot=json.loads(json.dumps(GAME_STATE,ensure_ascii=False))
    tmp.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(GAME_STATE_PATH)
    schedule_cloud_save(snapshot)

GAME_STATE = load_game_state()

def get_local_ip():
    """Descobre o IP do PC na rede local para abrir o jogo no celular."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

LOCAL_IP = get_local_ip()

def get_online_url():
    env_url = str(os.environ.get('PUBLIC_URL', '') or '').strip().rstrip('/')
    if env_url.startswith('https://') or env_url.startswith('http://'):
        return env_url
    try:
        value = ONLINE_URL_PATH.read_text(encoding='utf-8').strip().rstrip('/')
        if value.startswith('https://') or value.startswith('http://'):
            return value
    except Exception:
        pass
    return ''

EVENTS = []
CLIENTS = []
LOCK = threading.Lock()
TIKTOK_THREAD = None
CONNECT_TOKEN = 0
STATUS = {
    'connected': False,
    'connecting': False,
    'user': '',
    'message': 'Offline',
    'last_error': '',
    'last_event': None,
    'started_at': time.time(),
}
VIEWER_TEAMS = {}  # usuario TikTok -> time escolhido
VIEWER_LIKES = {}  # usuario TikTok -> saldo de likes após converter em pontos
TEAM_KEYWORDS = {}
TEAMS = TEAM_KEYWORDS

def normalize_team_item(item):
    name = str(item.get('name') or '').strip()
    abbr = str(item.get('abbr') or name[:3]).strip().upper()
    color = str(item.get('color') or '#eeeeee').strip()
    logo = str(item.get('logo') or f'assets/logos/{abbr}.png').strip()
    keywords = item.get('keywords') or []
    if isinstance(keywords, str):
        keywords = [x.strip() for x in keywords.replace(';', ',').split(',') if x.strip()]
    keywords = list(dict.fromkeys([name, abbr] + [str(k).strip() for k in keywords if str(k).strip()]))
    active = item.get('active', True) is not False
    return {'name': name, 'abbr': abbr, 'color': color, 'logo': logo, 'keywords': keywords, 'active': active}

def refresh_teams():
    global TEAM_KEYWORDS, TEAMS
    clean = []
    seen = set()
    for item in CONFIG.get('teams', []):
        if not isinstance(item, dict):
            continue
        t = normalize_team_item(item)
        key = t['abbr'] or t['name'].lower()
        if not t['name'] or key in seen:
            continue
        seen.add(key)
        clean.append(t)
    if not clean:
        clean = [normalize_team_item(x) for x in DEFAULT_CONFIG.get('teams', [])]
    CONFIG['teams'] = clean
    TEAM_KEYWORDS = {}
    for t in clean:
        if t.get('active') is False:
            continue
        for kw in t.get('keywords', []):
            kw = str(kw or '').lower().strip()
            if kw:
                TEAM_KEYWORDS[kw] = t['name']
    TEAMS = TEAM_KEYWORDS

refresh_teams()

def norm(s):
    return str(s or '').lower().strip().replace('@','')

def find_team(text):
    t = norm(text)
    for k, name in sorted(TEAMS.items(), key=lambda x: len(x[0]), reverse=True):
        if k in t:
            return name
    return None

def save_config():
    CONFIG_PATH.write_text(json.dumps(CONFIG, ensure_ascii=False, indent=2), encoding='utf-8')

def broadcast(kind, payload):
    data = {'kind': kind, 'payload': payload, 'status': STATUS.copy(), 'config': CONFIG.copy(), 'time': time.time()}
    dead = []
    with LOCK:
        for q in CLIENTS:
            try: q.put_nowait(data)
            except Exception: dead.append(q)
        for q in dead:
            try: CLIENTS.remove(q)
            except ValueError: pass

def push_event(team='', amount=0, source='painel', user='', gift='', avatar='', **extra):
    ev = {
        'id': time.time(), 'team': team, 'amount': int(amount or 0), 'source': source,
        'user': user or '', 'gift': gift or '', 'avatar': avatar or ''
    }
    ev.update(extra)
    with LOCK:
        EVENTS.append(ev)
        del EVENTS[:-500]
    STATUS['last_event'] = ev
    broadcast('event', ev)
    return ev

def update_status(**kw):
    STATUS.update(kw)
    broadcast('status', STATUS.copy())


def _safe_int(v, default=0):
    try:
        if v is None or v == '':
            return default
        return int(float(v))
    except Exception:
        return default

def _read_any(obj, names, default=None):
    """Lê atributo/campo em objetos ou dicts do TikTokLive, com fallback seguro."""
    for name in names:
        try:
            if isinstance(obj, dict) and name in obj:
                return obj.get(name)
            if hasattr(obj, name):
                v = getattr(obj, name)
                if callable(v):
                    continue
                return v
        except Exception:
            pass
    return default

def _obj_map(obj):
    try:
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, 'dict'):
            return obj.dict()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
    except Exception:
        pass
    return {}

def _find_number_by_key(obj, wanted):
    """Procura recursivamente chaves como diamond_count/diamond/coins/cost/value."""
    seen = set()
    def walk(x, depth=0):
        if depth > 3 or id(x) in seen:
            return None
        seen.add(id(x))
        m = _obj_map(x)
        if m:
            for k,v in m.items():
                lk = str(k).lower()
                if any(w in lk for w in wanted):
                    n = _safe_int(v, None)
                    if n and n > 0:
                        return n
            for v in list(m.values())[:40]:
                r = walk(v, depth+1)
                if r:
                    return r
        return None
    return walk(obj)


def extract_avatar_url(user_obj):
    """Tenta pegar a foto do perfil em várias versões do TikTokLive."""
    candidates = []
    for attr in ['avatar_thumb','avatar_medium','avatar_larger','avatarThumb','avatarMedium','avatarLarger','profile_picture','profilePicture','profilePictureUrl']:
        try:
            v = getattr(user_obj, attr, None)
            if v:
                candidates.append(v)
        except Exception:
            pass
    for v in candidates:
        try:
            if isinstance(v, str) and v.startswith('http'):
                return v
            url_list = getattr(v, 'url_list', None) or getattr(v, 'urlList', None)
            if url_list and len(url_list):
                return str(url_list[0])
            uri = getattr(v, 'uri', None)
            if isinstance(uri, str) and uri.startswith('http'):
                return uri
        except Exception:
            pass
    m = _obj_map(user_obj)
    def walk(x, depth=0):
        if depth > 4:
            return ''
        if isinstance(x, str) and x.startswith('http') and ('avatar' in x or 'tiktok' in x or 'muscdn' in x):
            return x
        if isinstance(x, dict):
            for k,v in x.items():
                lk=str(k).lower()
                if lk in ['url_list','urllist'] and isinstance(v, list) and v:
                    for item in v:
                        r=walk(item, depth+1)
                        if r: return r
                if 'avatar' in lk or 'profile' in lk or 'url' in lk:
                    r=walk(v, depth+1)
                    if r: return r
            for v in list(x.values())[:30]:
                r=walk(v, depth+1)
                if r: return r
        if isinstance(x, (list, tuple)):
            for v in x[:10]:
                r=walk(v, depth+1)
                if r: return r
        return ''
    return walk(m)

def extract_gift_points(event, gift_obj):
    # Valor oficial em diamantes enviado pelo TikTok.
    diamonds = _safe_int(_read_any(gift_obj, [
        'diamond_count','diamondCount','diamond','diamonds','coin_count','coinCount','cost','value','price'
    ], None), 0)
    if diamonds <= 0:
        diamonds = _safe_int(_find_number_by_key(gift_obj, ['diamond','coin','cost','price','value']), 0)
    if diamonds <= 0:
        diamonds = _safe_int(_find_number_by_key(event, ['diamond','coin','cost','price','value']), 1)
    if diamonds <= 0:
        diamonds = 1

    repeat = _safe_int(_read_any(event, [
        'repeat_count','repeatCount','combo_count','comboCount','count','quantity','amount'
    ], None), 1)
    if repeat <= 0:
        repeat = 1

    multiplier = _safe_int(CONFIG.get('diamond_multiplier', 1), 1)
    if multiplier <= 0:
        multiplier = 1
    amount = max(1, diamonds * repeat * multiplier)
    return diamonds, repeat, amount

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('[HTTP]', self.address_string(), fmt % args)


    def _cookie_value(self):
        for part in self.headers.get('Cookie','').split(';'):
            if '=' in part:
                k,v=part.strip().split('=',1)
                if k==COOKIE_NAME: return urllib.parse.unquote(v)
        return ''

    def _valid_session(self):
        if not AUTH_PASSWORD: return True
        value=self._cookie_value()
        if '.' not in value: return False
        payload,signature=value.rsplit('.',1)
        expected=hmac.new(AUTH_SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,expected): return False
        try:
            username,expires=payload.split(':',1)
            return username==AUTH_USER and int(expires)>int(time.time())
        except Exception: return False

    def _set_session(self):
        expires=int(time.time())+30*24*60*60; payload=f'{AUTH_USER}:{expires}'
        signature=hmac.new(AUTH_SECRET.encode(),payload.encode(),hashlib.sha256).hexdigest()
        self.send_header('Set-Cookie',f'{COOKIE_NAME}={urllib.parse.quote(payload+"."+signature)}; Path=/; Max-Age={30*24*60*60}; HttpOnly; Secure; SameSite=Lax')

    def _clear_session(self):
        self.send_header('Set-Cookie',f'{COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax')

    def _show_login(self,error='',next_path='/painel'):
        safe=next_path if next_path.startswith('/') and not next_path.startswith('//') else '/painel'
        html=LOGIN_HTML.replace('__ERRO__',f'<div class="erro">{error}</div>' if error else '').replace('__NEXT__',safe.replace('&','&amp;').replace('"','&quot;'))
        raw=html.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()

    def send_json(self, data):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma','no-cache')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def serve_file(self, rel):
        rel = rel.lstrip('/') or 'painel.html'
        if rel == 'overlay': rel = 'index.html'
        if rel == 'painel': rel = 'painel.html'
        path = (ROOT / rel).resolve()
        if not str(path).startswith(str(ROOT)) or not path.exists() or path.is_dir():
            self.send_response(404); self.end_headers(); self.wfile.write(b'Arquivo nao encontrado'); return
        data = path.read_bytes()
        if path.name == 'painel.html' and AUTH_PASSWORD:
            try:
                html=data.decode('utf-8')
                logout='''<a href="/logout" title="Sair" style="position:fixed;right:12px;top:12px;z-index:999999;background:#ff365d;color:white;text-decoration:none;padding:9px 13px;border-radius:10px;font:700 13px Arial;box-shadow:0 4px 18px #0008">SAIR</a>'''
                html=html.replace('</body>',logout+'</body>')
                data=html.encode('utf-8')
            except Exception:
                pass
        ctype = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        if path.suffix.lower() in ['.html','.css','.js']:
            ctype += '; charset=utf-8'
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        if path.suffix.lower() in ['.html','.css','.js','.png','.jpg','.jpeg','.webp']:
            self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma','no-cache')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        if path == '/login':
            length=int(self.headers.get('Content-Length') or 0); raw=self.rfile.read(length).decode('utf-8',errors='replace') if length else ''
            form=urllib.parse.parse_qs(raw); username=(form.get('username',[''])[0] or '').strip(); password=form.get('password',[''])[0] or ''; next_path=form.get('next',['/painel'])[0] or '/painel'
            if username==AUTH_USER and AUTH_PASSWORD and hmac.compare_digest(password,AUTH_PASSWORD):
                self.send_response(303); self._set_session(); self.send_header('Location',next_path if next_path.startswith('/') and not next_path.startswith('//') else '/painel'); self.end_headers(); return
            self._show_login('Usuário ou senha incorretos.',next_path); return
        if not self._valid_session(): self.send_json({'ok':False,'error':'Acesso não autorizado'}); return
        if path == '/game_state':
            try:
                length = int(self.headers.get('Content-Length') or 0)
                body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
                incoming_teams = body.get('teams', {})
                incoming_scorers = body.get('scorers', {})
                if not isinstance(incoming_teams, dict) or not isinstance(incoming_scorers, dict):
                    raise ValueError('Formato inválido')
                with LOCK:
                    GAME_STATE['teams'] = incoming_teams
                    GAME_STATE['scorers'] = incoming_scorers
                    GAME_STATE['updated_at'] = time.time()
                    save_game_state()
                    snapshot = json.loads(json.dumps(GAME_STATE, ensure_ascii=False))
                broadcast('game_state', snapshot)
                self.send_json({'ok': True, 'game_state': snapshot}); return
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)}); return
        if path == '/upload_logo':
            try:
                length = int(self.headers.get('Content-Length') or 0)
                ctype = self.headers.get('Content-Type','')
                rawb = self.rfile.read(length) if length else b''
                m = re.search('boundary=([^;]+)', ctype)
                if not m:
                    self.send_json({'ok': False, 'error': 'Envio inválido.'}); return
                boundary = ('--' + m.group(1)).encode()
                parts = rawb.split(boundary)
                abbr = 'TIME'; filedata = None; filename = 'logo.png'
                for part in parts:
                    if b'\r\n\r\n' not in part:
                        continue
                    header, content = part.split(b'\r\n\r\n', 1)
                    content = content.rstrip(b'\r\n-')
                    hs = header.decode('utf-8', errors='ignore')
                    if 'name="abbr"' in hs:
                        abbr = content.decode('utf-8', errors='ignore').strip().upper() or 'TIME'
                    elif 'name="logo"' in hs:
                        fm = re.search('filename="([^"]+)"', hs)
                        if fm: filename = fm.group(1)
                        filedata = content
                abbr = re.sub(r'[^A-Z0-9_-]', '', abbr)[:20] or 'TIME'
                if not filedata:
                    self.send_json({'ok': False, 'error': 'Escolha uma imagem primeiro.'}); return
                if len(filedata) > 5_000_000:
                    self.send_json({'ok': False, 'error': 'Imagem muito grande. Use até 5MB.'}); return
                ext = Path(filename).suffix.lower()
                if ext not in ['.png','.jpg','.jpeg','.webp']:
                    ext = '.png'
                logo_dir = ROOT / 'assets' / 'logos'
                logo_dir.mkdir(parents=True, exist_ok=True)
                out = logo_dir / f'{abbr}{ext}'
                out.write_bytes(filedata)
                rel = f'assets/logos/{abbr}{ext}'
                self.send_json({'ok': True, 'logo': rel, 'file': rel}); return
            except Exception as e:
                self.send_json({'ok': False, 'error': 'Falha ao enviar escudo: '+repr(e)}); return
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8', errors='replace') if length else '{}'
        try:
            body = json.loads(raw or '{}')
        except Exception:
            body = {}
        if path == '/save_teams':
            teams = body.get('teams', [])
            if not isinstance(teams, list):
                self.send_json({'ok': False, 'error': 'Lista de times inválida'}); return
            CONFIG['teams'] = teams
            refresh_teams()
            save_config()
            ev = push_event(source='config', team='', amount=0, config=CONFIG.copy())
            self.send_json({'ok': True, 'config': CONFIG, 'teams': CONFIG.get('teams', []), 'event': ev}); return
        self.send_json({'ok': False, 'error': 'Rota POST não encontrada'})

    def do_GET(self):
        global TIKTOK_THREAD, CONNECT_TOKEN
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        path = url.path

        if path == '/login':
            if self._valid_session(): self.send_response(303); self.send_header('Location','/painel'); self.end_headers(); return
            self._show_login(next_path=q.get('next',['/painel'])[0]); return
        if path == '/logout':
            self.send_response(303); self._clear_session(); self.send_header('Location','/login'); self.end_headers(); return
        if not self._valid_session(): self._show_login(next_path=self.path); return

        if path == '/network-info':
            online_base = get_online_url()
            self.send_json({
                'ok': True,
                'ip': LOCAL_IP,
                'port': PORT,
                'overlay_url': f'http://{LOCAL_IP}:{PORT}/overlay?modo=pc',
                'mobile_overlay_url': f'http://{LOCAL_IP}:{PORT}/overlay?modo=celular',
                'panel_url': f'http://{LOCAL_IP}:{PORT}/painel',
                'online_active': bool(online_base),
                'online_base_url': online_base,
                'online_overlay_url': (online_base + '/overlay?modo=celular') if online_base else '',
                'online_panel_url': (online_base + '/painel') if online_base else ''
            })
            return

        if path == '/mobile-qr':
            try:
                import qrcode
                qr_type = (q.get('tipo', ['local'])[0] or 'local').lower()
                online_base = get_online_url()
                if qr_type == 'online-jogo' and online_base:
                    mobile_url = online_base + '/overlay?modo=celular'
                elif qr_type == 'online-painel' and online_base:
                    mobile_url = online_base + '/painel'
                elif qr_type == 'painel':
                    mobile_url = f'http://{LOCAL_IP}:{PORT}/painel'
                else:
                    mobile_url = f'http://{LOCAL_IP}:{PORT}/overlay?modo=celular'
                qr = qrcode.QRCode(version=None, box_size=8, border=3)
                qr.add_data(mobile_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color='black', back_color='white')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                raw = buf.getvalue()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except Exception as e:
                raw = ('Erro ao gerar QR Code: ' + repr(e)).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            return

        if path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream; charset=utf-8')
            self.send_header('Cache-Control','no-cache')
            self.send_header('Connection','keep-alive')
            self.end_headers()
            client_q = queue.Queue()
            with LOCK: CLIENTS.append(client_q)
            try:
                hello = {'kind':'hello','payload':{'ok':True},'status':STATUS.copy(),'config':CONFIG.copy(),'game_state':GAME_STATE.copy(),'time':time.time()}
                self.wfile.write(('data: '+json.dumps(hello,ensure_ascii=False)+'\n\n').encode('utf-8')); self.wfile.flush()
                while True:
                    try: item = client_q.get(timeout=15)
                    except queue.Empty: item = {'kind':'ping','payload':{},'status':STATUS.copy(),'config':CONFIG.copy(),'game_state':GAME_STATE.copy(),'time':time.time()}
                    self.wfile.write(('data: '+json.dumps(item,ensure_ascii=False)+'\n\n').encode('utf-8')); self.wfile.flush()
            except Exception:
                pass
            finally:
                with LOCK:
                    try: CLIENTS.remove(client_q)
                    except ValueError: pass
            return

        if path == '/game_state':
            with LOCK:
                snapshot = json.loads(json.dumps(GAME_STATE, ensure_ascii=False))
            self.send_json({'ok': True, 'game_state': snapshot}); return
        if path == '/events':
            since = float(q.get('since',[0])[0] or 0)
            with LOCK: recent = [e for e in EVENTS if e['id'] > since]
            self.send_json({'ok': True, 'events': recent, 'status': STATUS, 'config': CONFIG, 'game_state': GAME_STATE}); return
        if path == '/config':
            self.send_json({'ok': True, 'config': CONFIG, 'status': STATUS, 'teams': CONFIG.get('teams', []), 'game_state': GAME_STATE}); return
        if path == '/set_config':
            for key, values in q.items():
                if not values:
                    continue
                value = values[0]
                if str(value).lower() in ['true','false']:
                    CONFIG[key] = str(value).lower() == 'true'
                else:
                    try:
                        CONFIG[key] = int(value)
                    except Exception:
                        try:
                            CONFIG[key] = float(value)
                        except Exception:
                            CONFIG[key] = value
            refresh_teams()
            save_config()
            ev = push_event(source='config', team='', amount=0, config=CONFIG.copy())
            self.send_json({'ok': True, 'config': CONFIG, 'event': ev}); return
        if path == '/board_control':
            board = str(q.get('board',[''])[0] or '').strip().lower()
            action = str(q.get('action',['toggle'])[0] or 'toggle').strip().lower()
            if board not in ['champions', 'scorers']:
                self.send_json({'ok': False, 'error': 'Quadro inválido'}); return
            if action not in ['show', 'hide', 'toggle']:
                action = 'toggle'
            ev = push_event(source='board_control', board=board, action=action)
            self.send_json({'ok': True, 'event': ev}); return
        if path == '/add':
            requested = q.get('team',[''])[0]
            team = find_team(requested) or requested
            try: amount = int(q.get('amount',[CONFIG.get('gift_default',25)])[0] or 1)
            except Exception: amount = int(CONFIG.get('gift_default',25))
            ev = push_event(team, amount, 'painel')
            print(f'[PONTO] {team} +{amount}')
            self.send_json({'ok': True, 'event': ev}); return
        if path == '/reset':
            full = q.get('full',['1'])[0] != '0'
            ev = push_event(source='reset', full=full)
            print('[RESET]', 'total' if full else 'corrida')
            self.send_json({'ok': True, 'event': ev}); return
        if path == '/connect':
            user = q.get('user',[''])[0].replace('@','').strip()
            if not user:
                update_status(connected=False, connecting=False, user='', message='Digite o @ da live.', last_error='Usuario vazio')
                self.send_json({'ok': False, 'status': STATUS}); return
            CONNECT_TOKEN += 1
            token = CONNECT_TOKEN
            update_status(connected=False, connecting=True, user=user, message=f'Tentando conectar em @{user}...', last_error='')
            push_event(source='log', team='', amount=0, message=f'Conectando na live @{user}')
            TIKTOK_THREAD = threading.Thread(target=start_tiktok, args=(user, token), daemon=True)
            TIKTOK_THREAD.start()
            def watchdog(tok, usr):
                time.sleep(25)
                if tok == CONNECT_TOKEN and STATUS.get('connecting') and not STATUS.get('connected'):
                    update_status(message=f'Ainda tentando conectar em @{usr}. Se nao sair disso, confira se a live esta AO VIVO e veja o erro na janela preta.', last_error='Conexao demorando mais que 25 segundos')
            threading.Thread(target=watchdog, args=(token, user), daemon=True).start()
            self.send_json({'ok': True, 'status': STATUS}); return
        if path == '/disconnect':
            CONNECT_TOKEN += 1
            update_status(connected=False, connecting=False, message='Desconectado pelo painel.')
            self.send_json({'ok': True, 'status': STATUS}); return
        if path == '/status':
            with LOCK: count = len(EVENTS); clients = len(CLIENTS)
            self.send_json({'ok': True, 'status': STATUS, 'config': CONFIG, 'events_count': count, 'clientes_overlay': clients}); return
        if path == '/test_tiktok':
            team = find_team(q.get('team',['Flamengo'])[0]) or 'Flamengo'
            ev = push_event(team, int(q.get('amount',[25])[0]), 'presente', q.get('user',['Teste TikTok'])[0], q.get('gift',['Rosa'])[0])
            self.send_json({'ok': True, 'event': ev}); return

        self.serve_file(path)

def start_tiktok(unique_id, token=0):
    """Conecta no TikTok sem travar o painel e mostra o erro real no status."""
    if not unique_id:
        update_status(message='Digite o @ da live.', connecting=False, last_error='Usuario vazio')
        return

    def still_current():
        return token == CONNECT_TOKEN

    def fail(msg, exc=None):
        detail = msg if exc is None else (msg + ': ' + repr(exc))
        print('[TIKTOK ERRO]', detail)
        if still_current():
            update_status(connected=False, connecting=False, message=detail, last_error=detail)
            push_event(source='log', team='', amount=0, message=detail)

    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import CommentEvent, GiftEvent, LikeEvent, ConnectEvent, DisconnectEvent
    except Exception as e:
        fail('TikTokLive nao instalado. Abra novamente o ABRIR_PROGRAMA.bat ou rode: python -m pip install -r requirements.txt', e)
        return

    # Algumas versões aceitam @usuario; outras funcionam melhor sem @.
    candidates = [unique_id, '@' + unique_id]
    last_exc = None

    for candidate in candidates:
        if not still_current():
            return
        try:
            update_status(connected=False, connecting=True, user=unique_id, message=f'Tentando TikTokLive com {candidate}...', last_error='')
            print('[TIKTOK] Tentando conectar:', candidate)
            client = TikTokLiveClient(unique_id=candidate)

            @client.on(ConnectEvent)
            async def on_connect(event):
                if still_current():
                    print('[TIKTOK] LIVE CONECTADA:', unique_id)
                    update_status(connected=True, connecting=False, user=unique_id, message=f'Conectado em @{unique_id}', last_error='')
                    push_event(source='log', team='', amount=0, message=f'LIVE CONECTADA @{unique_id}')

            @client.on(DisconnectEvent)
            async def on_disconnect(event):
                if still_current():
                    print('[TIKTOK] Desconectado')
                    update_status(connected=False, connecting=False, user=unique_id, message='TikTok desconectou.', last_error='')
                    push_event(source='log', team='', amount=0, message='TikTok desconectou')

            @client.on(CommentEvent)
            async def on_comment(event):
                if not CONFIG.get('comment_enabled', True):
                    return
                txt = getattr(event, 'comment', '') or ''
                team = find_team(txt)
                user_obj = getattr(event, 'user', None)
                uid = norm(getattr(user_obj, 'unique_id', '') or getattr(user_obj, 'user_id', '') or getattr(user_obj, 'nickname', ''))
                name = getattr(user_obj, 'nickname', '') or getattr(user_obj, 'unique_id', '') or uid
                if team and uid:
                    old_team = VIEWER_TEAMS.get(uid)
                    VIEWER_TEAMS[uid] = team
                    msg = f'{name} escolheu {team}' if old_team != team else f'{name} ja estava no time {team}'
                    print('[COMENTARIO]', msg, '|', txt)
                    # Comentário NAO soma ponto; manda apenas log/status.
                    update_status(last_event={'source': 'escolha', 'team': team, 'amount': 0, 'user': name, 'comment': txt, 'message': msg})
                    # Ao trocar de time, começa uma nova contagem pessoal de likes.
                    if old_team != team:
                        VIEWER_LIKES[uid] = 0
                    push_event(source='escolha', team=team, amount=0, user=name, comment=txt, message=msg)

            @client.on(LikeEvent)
            async def on_like(event):
                if not CONFIG.get('like_enabled', False):
                    return
                user_obj = getattr(event, 'user', None)
                uid = norm(getattr(user_obj, 'unique_id', '') or getattr(user_obj, 'user_id', '') or getattr(user_obj, 'nickname', ''))
                name = getattr(user_obj, 'nickname', '') or getattr(user_obj, 'unique_id', '') or uid
                team = VIEWER_TEAMS.get(uid)
                if not uid or not team:
                    return
                try:
                    count = int(getattr(event, 'count', 0) or getattr(event, 'like_count', 0) or 1)
                except Exception:
                    count = 1
                count = max(1, count)
                required = max(1, int(CONFIG.get('likes_required', 100) or 100))
                points_each = max(1, int(CONFIG.get('like_points', 1) or 1))
                total = int(VIEWER_LIKES.get(uid, 0)) + count
                batches, remainder = divmod(total, required)
                VIEWER_LIKES[uid] = remainder
                if batches <= 0:
                    update_status(last_event={'source':'like_progress','team':team,'amount':0,'user':name,'likes':remainder,'required':required,'message':f'{name}: {remainder}/{required} likes para {team}'})
                    return
                amount = batches * points_each
                msg = f'{name} completou {batches * required} likes e deu +{amount} para {team}'
                print('[LIKE]', msg)
                update_status(last_event={'source':'like','team':team,'amount':amount,'user':name,'likes':batches * required,'required':required,'message':msg})
                push_event(team=team, amount=amount, source='like', user=name, likes=batches * required, required=required, message=msg)

            @client.on(GiftEvent)
            async def on_gift(event):
                if not CONFIG.get('gift_enabled', True):
                    return
                gift_obj = getattr(event, 'gift', None)
                gift_name = getattr(gift_obj, 'name', '') or str(gift_obj or 'Presente')
                user_obj = getattr(event, 'user', None)
                uid = norm(getattr(user_obj, 'unique_id', '') or getattr(user_obj, 'user_id', '') or getattr(user_obj, 'nickname', ''))
                name = getattr(user_obj, 'nickname', '') or getattr(user_obj, 'unique_id', '') or uid
                team = VIEWER_TEAMS.get(uid) or find_team(gift_name)
                if not team:
                    msg = f'Presente ignorado: {name} ainda nao escolheu time.'
                    print('[GIFT]', msg)
                    update_status(last_error=msg, message=msg)
                    push_event(source='log', team='', amount=0, user=name, gift=gift_name, message=msg)
                    return
                # Evita duplicar combo de presentes em sequência: soma só quando o TikTok sinaliza o fim.
                repeat_end = bool(getattr(event, 'repeat_end', True))
                streakable = bool(getattr(gift_obj, 'streakable', False))
                try:
                    if int(getattr(gift_obj, 'type', 0) or 0) == 1:
                        streakable = True
                except Exception:
                    pass
                if streakable and not repeat_end:
                    return

                # Conversão definitiva: usa o valor oficial do presente em diamantes.
                # Pontos = diamantes do presente x quantidade do combo.
                # Funciona também para presente caro/novo, sem lista fixa de nomes.
                diamonds, repeat, amount = extract_gift_points(event, gift_obj)
                avatar = extract_avatar_url(user_obj)
                print(f'[PONTO] {team} +{amount} | {gift_name} | diamantes={diamonds} qtd={repeat} | {name}')
                push_event(team, amount, 'presente', name, gift_name, avatar, diamonds=diamonds, repeat=repeat, combo=repeat)

            # run() bloqueia esta thread até cair/desconectar.
            client.run()
            if still_current():
                update_status(connected=False, connecting=False, user=unique_id, message='TikTok desconectou.', last_error='')
            return
        except Exception as e:
            last_exc = e
            print('[TIKTOK] Falhou com', candidate, repr(e))
            # tenta o próximo formato de usuário
            continue

    fail('Nao consegui conectar. Confira se o usuario esta ao vivo e se o @ foi digitado certo', last_exc)

print('===================================================')
print(' CORRIDA TIMES TIKTOK - MODULO 8 TEMPO REAL')
print(f' Painel no PC : http://127.0.0.1:{PORT}/painel')
print(f' Jogo no PC   : http://127.0.0.1:{PORT}/overlay?modo=pc')
print(f' Jogo CELULAR : http://{LOCAL_IP}:{PORT}/overlay?modo=celular')
print(' PC e celular precisam estar na mesma rede.')
print(' OBS: use a URL /overlay, nao abra index.html direto.')
print('===================================================')
ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
