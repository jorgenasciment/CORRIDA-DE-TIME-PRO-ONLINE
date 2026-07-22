let META = 300;
let UI_CONFIG = {champion_duration:8, champion_size:120, champion_name_size:38, show_goal_text:false, show_champion_name:true, show_live_status:false, show_ranking:true, ranking_scale:115, ranking_x:50, ranking_y:0, ranking_width:96, ranking_logo_size:42, ranking_score_size:30, ranking_position_size:17, ranking_gap:4, ranking_height:78, effect_time:1, lightning_power:100, ultra_gift_enabled:true, ultra_gift_threshold:99, ultra_gift_text:"🔥 MODO ULTRA GIFT 🔥", ultra_gift_duration:3, ultra_gift_cinematic:true, ultra_gift_slowmo:true, ultra_gift_dim:true, ultra_gift_shockwave:true, ultra_gift_particles:true, ultra_gift_rays:true, tournament_timer_enabled:false, tournament_minutes:5, tournament_timer_x:50, tournament_timer_y:8, tournament_timer_scale:100, tournament_timer_opacity:100, ranking_title_text:"🏆 MAIORES CAMPEÕES", show_ranking_title:true, ranking_title_x:50, ranking_title_y:4, ranking_title_scale:100, ranking_title_color:"#ffd400", show_race_rank_title:true, race_rank_title_text:"📊 RANKING", race_rank_title_x:50, race_rank_title_y:8, race_rank_title_width:88, race_rank_title_height:38, race_rank_title_scale:100, race_rank_title_color:"#ffffff"};
let tournamentEndAt = 0;
let tournamentTickTimer = null;
let tournamentFinishedLock = false;
const STORAGE_KEY = "corrida_times_tiktok_mod29";
const SCORERS_STORAGE_KEY = "corrida_times_tiktok_artilheiros_v1";
let teamScorers = {};
const SERVER_URL = (location.protocol === "http:" || location.protocol === "https:") ? location.origin : "http://127.0.0.1:8787";
let lastServerEvent = 0;
let lastConfigSync = 0;
let lastConfigText = '';
let configPollTimer = null;
let centralStateReady = false;
let centralStateSaving = false;
let centralStateQueued = false;
let lastCentralStateUpdatedAt = 0;

const DEFAULT_TEAMS = [["Athletico-PR", "CAP", "#d71920"], ["Atlético-MG", "CAM", "#f1f1f1"], ["Bahia", "BAH", "#008ee6"], ["Botafogo", "BOT", "#eeeeee"], ["Chapecoense", "CHA", "#1fad4b"], ["Corinthians", "COR", "#eeeeee"], ["Coritiba", "CTB", "#159447"], ["Cruzeiro", "CRU", "#0057b8"], ["Flamengo", "FLA", "#e90016"], ["Fluminense", "FLU", "#006b3f"], ["Grêmio", "GRE", "#00a3e0"], ["Internacional", "INT", "#df0000"], ["Mirassol", "MIR", "#d4d400"], ["Palmeiras", "PAL", "#22b14c"], ["RB Bragantino", "RBB", "#e40046"], ["Remo", "REM", "#003b75"], ["Santos", "SAN", "#eeeeee"], ["São Paulo", "SPFC", "#d71920"], ["Vasco", "VAS", "#eeeeee"], ["Vitória", "VIT", "#c90000"], ["Vila Nova", "VNO", "#d71920"], ["Fortaleza", "FOR", "#0067b1"], ["Ceará", "CEA", "#eeeeee"], ["Novorizontino", "NOV", "#f2c300"], ["Avaí", "AVA", "#0067b1"], ["Athletic Club", "ATH", "#111111"], ["Operário-PR", "OPE", "#eeeeee"], ["Botafogo-SP", "BSP", "#eeeeee"], ["São Bernardo", "SBE", "#f2d000"], ["Criciúma", "CRI", "#f5d20a"], ["Juventude", "JUV", "#149657"], ["Goiás", "GOI", "#0c8c42"], ["Sport", "SPT", "#e00000"], ["Náutico", "NAU", "#e00000"], ["Cuiabá", "CUI", "#d9c300"], ["Londrina", "LON", "#00a6df"], ["Atlético-GO", "ACG", "#e00000"], ["Ponte Preta", "PON", "#eeeeee"], ["CRB", "CRB", "#e00000"], ["América-MG", "AME", "#159447"]].map(([name, abbr, color]) => ({ name, abbr, color, logo:`assets/logos/${abbr}.png`, keywords:[name,abbr], active:true, score:0, wins:0, lastBoost:0 }));

let teams = DEFAULT_TEAMS.map(t => ({...t}));

function safeTeamAbbr(team){
  return String((team && (team.abbr || team.name)) || "TIME").trim().toUpperCase().slice(0,5) || "TIME";
}
function safeTeamColor(team){
  const c = String((team && team.color) || "#eeeeee").trim();
  return /^#[0-9a-f]{6}$/i.test(c) ? c : "#eeeeee";
}
function fallbackSvg(team){
  const abbr = safeTeamAbbr(team).replace(/[<>&]/g, "");
  const name = String((team && team.name) || abbr || "TIME").replace(/[<>&]/g, "").toUpperCase();
  const color = safeTeamColor(team);
  const shortName = name.length > 18 ? name.slice(0,18) : name;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180" viewBox="0 0 180 180"><defs><radialGradient id="g"><stop offset="0" stop-color="#ffffff" stop-opacity=".40"/><stop offset="1" stop-color="${color}" stop-opacity=".96"/></radialGradient></defs><path d="M38 12h104l24 35-18 93-58 30-58-30-18-93z" fill="#050505" stroke="#fff" stroke-width="7"/><path d="M48 25h84l18 28-14 78-46 24-46-24-14-78z" fill="url(#g)" stroke="#fff" stroke-width="3"/><circle cx="90" cy="78" r="38" fill="#ffffff" opacity=".88"/><text x="90" y="91" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" font-weight="900" fill="#111">⚽</text><rect x="27" y="118" width="126" height="34" rx="12" fill="#000" opacity=".78"/><text x="90" y="141" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="900" fill="#fff" stroke="#000" stroke-width="1" paint-order="stroke">${shortName}</text><text x="90" y="43" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="900" fill="#fff" stroke="#000" stroke-width="2" paint-order="stroke">${abbr}</text></svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}
function setTeamImage(img, team){
  if(!img || !team) return;
  img.onerror = function(){ this.onerror = null; this.src = fallbackSvg(team); this.style.display = "block"; };
  img.alt = team.name || safeTeamAbbr(team);
  img.src = team.logo || fallbackSvg(team);
}
function logoSrc(team){
  return String((team && team.logo) || fallbackSvg(team));
}

function normalizeTeamConfig(item){
  const name = String(item.name || "").trim();
  const abbr = String(item.abbr || name.slice(0,3)).trim().toUpperCase();
  const color = String(item.color || "#eeeeee").trim();
  const logo = String(item.logo || `assets/logos/${abbr}.png`).trim();
  const keywords = Array.isArray(item.keywords) ? item.keywords : String(item.keywords || "").split(/[,;]/);
  const active = item.active !== false;
  return {name, abbr, color, logo, keywords, active, score:0, wins:0, lastBoost:0};
}

function applyTeamsConfig(list){
  if(!Array.isArray(list) || !list.length) return;
  const old = new Map(teams.map(t => [t.abbr, t]));
  teams = list.map(normalizeTeamConfig).filter(t => t.name && t.active !== false);
  teams.forEach(t => {
    const prev = old.get(t.abbr);
    if(prev){ t.score = Number(prev.score || 0); t.wins = Number(prev.wins || 0); t.lastBoost = prev.lastBoost || 0; }
    else if(!(t.abbr in visualScore)){ visualScore[t.abbr] = 0; }
  });
  document.querySelectorAll('#race .row').forEach(row => {
    if(!teams.some(t => t.abbr === row.dataset.team)) row.remove();
  });
  loadState();
  sortTeams();
  renderRace(false);
}

const race = document.getElementById("race");
const topCards = [1,2,3,4,5].map(n=>document.getElementById(`top${n}`)).filter(Boolean);

// Guarda a última posição visual de cada time.
// Assim, quando recebe novo presente, o escudo continua perto da pontuação atual
// e NÃO volta para o começo. Só volta para 0 quando bater a META.
const visualScore = {};

function localTeamsSnapshot(){
  const data = {}; teams.forEach(t => data[t.abbr] = {score:Number(t.score||0), wins:Number(t.wins||0)});
  return data;
}
function loadState(){
  if(centralStateReady) return;
  try{
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    teams.forEach(t => { if(saved[t.abbr]){ t.score = Number(saved[t.abbr].score || 0); t.wins = Number(saved[t.abbr].wins || 0); } });
  }catch(e){}
}
function applyCentralGameState(gs, force=false){
  if(!gs || typeof gs !== 'object') return;
  const updated = Number(gs.updated_at || 0);
  if(!force && updated && updated < lastCentralStateUpdatedAt) return;
  const saved = gs.teams || {};
  teams.forEach(t => {
    if(saved[t.abbr]){
      t.score = Number(saved[t.abbr].score || 0);
      t.wins = Number(saved[t.abbr].wins || 0);
      visualScore[t.abbr] = Math.min(t.score, META);
    }
  });
  teamScorers = (gs.scorers && typeof gs.scorers === 'object') ? gs.scorers : {};
  centralStateReady = true;
  lastCentralStateUpdatedAt = updated || Date.now()/1000;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(localTeamsSnapshot()));
  localStorage.setItem(SCORERS_STORAGE_KEY, JSON.stringify(teamScorers));
  sortTeams(); renderRace(false); renderScorersBoard();
}
async function loadCentralGameState(){
  try{
    const r = await fetch(SERVER_URL + '/game_state', {cache:'no-store'});
    const j = await r.json();
    const gs = j.game_state || {};
    const hasCentral = Object.keys(gs.teams || {}).length > 0 || Object.keys(gs.scorers || {}).length > 0;
    if(hasCentral) applyCentralGameState(gs, true);
    else {
      centralStateReady = true;
      await saveCentralGameState(); // migra automaticamente os dados deste navegador
    }
  }catch(e){ centralStateReady = true; }
}
async function saveCentralGameState(){
  localStorage.setItem(STORAGE_KEY, JSON.stringify(localTeamsSnapshot()));
  localStorage.setItem(SCORERS_STORAGE_KEY, JSON.stringify(teamScorers));
  if(!centralStateReady) return;
  if(centralStateSaving){ centralStateQueued = true; return; }
  centralStateSaving = true;
  try{
    const r = await fetch(SERVER_URL + '/game_state', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({teams:localTeamsSnapshot(),scorers:teamScorers})});
    const j = await r.json();
    if(j.game_state) lastCentralStateUpdatedAt = Number(j.game_state.updated_at || lastCentralStateUpdatedAt);
  }catch(e){}
  centralStateSaving = false;
  if(centralStateQueued){ centralStateQueued = false; saveCentralGameState(); }
}
function saveState(){ saveCentralGameState(); }

function loadScorers(){
  try{ teamScorers = JSON.parse(localStorage.getItem(SCORERS_STORAGE_KEY) || "{}") || {}; }
  catch(e){ teamScorers = {}; }
}
function saveScorers(){ saveCentralGameState(); }
function clearScorers(){
  teamScorers = {};
  localStorage.removeItem(SCORERS_STORAGE_KEY);
  saveCentralGameState();
  renderScorersBoard();
}
function scorerUserKey(ev){
  return String(ev.user_id || ev.unique_id || ev.user || "usuario").trim().toLowerCase();
}
function registerGiftScorer(teamRef, ev){
  if(!ev || ev.source !== "presente" || !ev.user) return;
  const team = teams.find(t => t.name === teamRef || t.abbr === teamRef || t.name.toLowerCase() === String(teamRef).toLowerCase());
  if(!team) return;
  const diamondsEach = Number(ev.diamonds || 0);
  const repeat = Math.max(1, Number(ev.repeat || ev.combo || 1));
  const realDiamonds = Math.max(0, diamondsEach > 0 ? diamondsEach * repeat : Number(ev.amount || 0));
  if(realDiamonds <= 0) return;
  const key = scorerUserKey(ev);
  if(!teamScorers[team.abbr]) teamScorers[team.abbr] = {};
  const current = teamScorers[team.abbr][key] || {name:ev.user, avatar:"", diamonds:0};
  current.name = ev.user || current.name;
  current.avatar = ev.avatar || current.avatar || "";
  current.diamonds = Number(current.diamonds || 0) + realDiamonds;
  teamScorers[team.abbr][key] = current;
  saveScorers();
  renderScorersBoard();
}
function bestScorerForTeam(team){
  const users = Object.values(teamScorers[team.abbr] || {});
  return users.sort((a,b)=>Number(b.diamonds||0)-Number(a.diamonds||0))[0] || null;
}
function ensureScorersBoard(){
  let board=document.getElementById("scorers-board");
  if(board) return board;
  board=document.createElement("div");
  board.id="scorers-board";
  board.innerHTML=`<div class="scorers-board-header"><span>⚽ ARTILHEIROS DOS CAMPEÕES</span><small>A = ABRIR/FECHAR</small></div><div id="scorers-board-list"></div>`;
  document.getElementById("game").appendChild(board);
  return board;
}
function renderScorersBoard(){
  const board=ensureScorersBoard();
  const list=board.querySelector("#scorers-board-list");
  if(!list) return;
  const champions=[...teams].filter(t=>Number(t.wins||0)>0).sort((a,b)=>Number(b.wins||0)-Number(a.wins||0)||a.name.localeCompare(b.name)).slice(0,10);
  const rows=champions.map((team,index)=>({team,index,scorer:bestScorerForTeam(team)})).filter(x=>x.scorer);
  if(!rows.length){ list.innerHTML='<div class="scorers-board-empty">Nenhum artilheiro campeão ainda.<br>O time precisa conquistar pelo menos 1 vitória.</div>'; return; }
  list.innerHTML=rows.map(({team,index,scorer})=>`
    <div class="scorers-board-row">
      <div class="scorer-position">${index+1}º</div>
      <img class="scorer-team-logo" src="${logoSrc(team)}" alt="${team.name}">
      <div class="scorer-info"><strong>${String(scorer.name||'Usuário').replace(/[<>&]/g,'').toUpperCase()}</strong><span>${team.name} • ${team.wins} vitória${team.wins===1?'':'s'}</span></div>
      <div class="scorer-diamonds">💎 ${Number(scorer.diamonds||0).toLocaleString('pt-BR')}</div>
    </div>`).join('');
}
function toggleScorersBoard(){
  const board=ensureScorersBoard();
  board.classList.toggle("show");
  renderScorersBoard();
}

function makeRow(team){
  const row = document.createElement("div");
  row.className = "row";
  row.dataset.team = team.abbr;
  row.style.setProperty("--team", team.color);
  row.innerHTML = `
    <div class="rank">0º</div>
    <div class="lane"></div>
    <div class="trail"></div>
    <div class="bar-name"><span>${team.name}</span></div>
    <div class="speed-lines"></div>
    <div class="marker" data-abbr="${team.abbr}"><img alt="${team.name}"></div>
    <div class="shield-fx"><span class="fx-ring"></span><span class="fx-bolt b1"></span><span class="fx-bolt b2"></span><span class="fx-bolt b3"></span><span class="fx-sparks"></span></div>
    <div class="lightning">⚡</div>
    <div class="score">0</div>
  `;
  setTeamImage(row.querySelector(".marker img"), team);
  return row;
}

function refreshRowLogo(row, team){
  if(!row || !team) return;
  const marker = row.querySelector(".marker");
  if(marker) marker.dataset.abbr = safeTeamAbbr(team);
  setTeamImage(row.querySelector(".marker img"), team);
}

function ensureRows(){
  teams.forEach(team => {
    if(!race.querySelector(`[data-team="${team.abbr}"]`)) race.appendChild(makeRow(team));
  });
}

function sortTeams(){
  teams.sort((a,b)=> b.score-a.score || b.wins-a.wins || a.name.localeCompare(b.name));
}

function renderRace(animated=true){
  ensureRows();
  const first = new Map([...race.children].map(el => [el.dataset.team, el.getBoundingClientRect()]));
  teams.forEach(t => race.appendChild(race.querySelector(`[data-team="${t.abbr}"]`)));

  [...race.children].forEach((row, index) => {
    const team = teams[index];
    row.style.height = `${100 / teams.length}%`;
    row.style.setProperty("--team", team.color);
    row.classList.toggle("leader", index === 0 && team.score > 0);
    row.classList.toggle("hot", team.score >= 225);
    row.classList.toggle("near", team.score >= 270);
    row.querySelector(".rank").textContent = `${index+1}º`;
    row.querySelector(".rank").classList.toggle("toprank", index < 3);
    refreshRowLogo(row, team);
    updateRowPosition(row, team);
  });

  if(animated){
    [...race.children].forEach(el => {
      const old = first.get(el.dataset.team); if(!old) return;
      const now = el.getBoundingClientRect();
      const dy = old.top - now.top;
      if(Math.abs(dy) > 1){
        el.style.transition = "none";
        el.style.transform = `translateY(${dy}px)`;
        el.offsetHeight;
        el.style.transition = "transform .42s cubic-bezier(.2,.9,.2,1),background .25s,filter .25s";
        el.style.transform = "translateY(0)";
      }
    });
  }

  renderTopChampions();
  renderWinsBoard();
  renderScorersBoard();
  updateTournamentTimerUI();
}

function updateRowPosition(row, team){
  // Posição sempre baseada no TOTAL atual de pontos do time.
  // Não usamos animação voltando ao zero a cada presente.
  // Só volta para o começo quando o score realmente for zerado ao bater a meta.
  const atual = Math.max(0, Number(team.score || 0));

  if(!(team.abbr in visualScore)) visualScore[team.abbr] = atual;

  // MÓDULO 36: a posição visual segue exatamente o saldo real.
  // Isso permite voltar para a sobra da próxima partida (ex.: 280 + 99 = 79).
  visualScore[team.abbr] = Math.min(atual, META);

  const pct = Math.min(visualScore[team.abbr] / META, 1);

  // MÓDULO 11: um único escudo por time.
  // O escudo que aparece é o próprio marcador da corrida.
  // A pontuação acompanha o escudo, mas quando chega perto da CHEGADA
  // ela muda para o lado esquerdo para nunca ficar escondida.
  const start = 58;
  const finishSpace = 72;
  const end = Math.max(start + 30, row.clientWidth - finishSpace);
  const x = start + (end - start) * pct;
  const score = row.querySelector(".score");
  const scoreText = String(atual);
  const digits = scoreText.length;
  const scoreWidthEstimate = Math.max(48, digits * 23 + 18);
  const scoreBefore = pct >= 0.72;
  const scoreX = scoreBefore ? Math.max(84, x - scoreWidthEstimate - 20) : Math.min(x + 48, end - 10);

  row.querySelector(".trail").style.width = `${Math.max(0, x - start)}px`;
  row.querySelector(".marker").style.left = `${x}px`;
  const lightning = row.querySelector(".lightning");
  if(lightning) lightning.style.left = `${x + (scoreBefore ? -34 : 32)}px`;
  const shieldFx = row.querySelector(".shield-fx");
  if(shieldFx) shieldFx.style.left = `${x}px`;

  score.textContent = scoreText;
  score.style.left = `${scoreX}px`;
  score.classList.toggle("score-before", scoreBefore);

  const barName = row.querySelector(".bar-name span");
  if(barName) barName.textContent = team.name.toUpperCase();
  row.querySelector(".speed-lines").style.left = `${Math.max(start, x - 95)}px`;
}


function ensureTournamentTimer(){
  let box = document.getElementById("tournament-timer");
  if(!box){
    box = document.createElement("div");
    box.id = "tournament-timer";
    box.innerHTML = `<div class="timer-clock">00:00</div>`;
    document.getElementById("game").appendChild(box);
  }
  return box;
}
function formatClock(ms){
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2,"0");
  const s = String(total % 60).padStart(2,"0");
  return `${m}:${s}`;
}
function getCurrentLeader(){
  return [...teams].sort((a,b)=> b.score-a.score || b.wins-a.wins || a.name.localeCompare(b.name))[0];
}
function updateTournamentTimerUI(){
  const enabled = !!UI_CONFIG.tournament_timer_enabled;
  const box = ensureTournamentTimer();
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,Number(v)||0));
  const tx=clamp(UI_CONFIG.tournament_timer_x ?? 50,0,100);
  const ty=clamp(UI_CONFIG.tournament_timer_y ?? 8,0,100);
  const sc=Math.max(0.5,Math.min(2.5,(Number(UI_CONFIG.tournament_timer_scale||100)/100)));
  const opacity=Math.max(0.05,Math.min(1,Number(UI_CONFIG.tournament_timer_opacity ?? 100)/100));
  box.style.left = tx + "%";
  box.style.top = ty + "%";
  box.style.transform = `translate(-50%,-50%) scale(${sc})`;
  box.style.opacity = String(opacity);
  box.style.display = enabled ? "block" : "none";
  if(!enabled) return;
  if(!tournamentEndAt){
    const minutes = Math.max(1, Number(UI_CONFIG.tournament_minutes || 5));
    tournamentEndAt = Date.now() + minutes * 60 * 1000;
    tournamentFinishedLock = false;
  }
  const left = tournamentEndAt - Date.now();
  const clock = box.querySelector(".timer-clock");
  clock.textContent = formatClock(left);
  box.classList.toggle("danger", left <= 30000);
  if(left <= 0 && !tournamentFinishedLock){
    tournamentFinishedLock = true;
    finishTournamentByTimer();
  }
}
function restartTournamentTimer(){
  const minutes = Math.max(1, Number(UI_CONFIG.tournament_minutes || 5));
  tournamentEndAt = Date.now() + minutes * 60 * 1000;
  tournamentFinishedLock = false;
  updateTournamentTimerUI();
}
function startTournamentTicker(){
  if(tournamentTickTimer) return;
  tournamentTickTimer = setInterval(updateTournamentTimerUI, 500);
}
function finishTournamentByTimer(){
  const champion = getCurrentLeader();
  if(!champion || champion.score <= 0){
    teams.forEach(t=>{t.score=0; visualScore[t.abbr]=0;});
    saveState(); sortTeams(); renderRace(true); restartTournamentTimer();
    return;
  }
  champion.wins += 1;
  const winnerCopy = {...champion};
  teams.forEach(t=>{t.score=0; visualScore[t.abbr]=0;});
  saveState(); sortTeams(); renderRace(true); showChampion(winnerCopy);
  restartTournamentTimer();
}

function resetGame(full=true){
  teams.forEach(t=>{t.score=0; visualScore[t.abbr]=0; if(full) t.wins=0;});
  if(full) clearScorers();
  sortTeams(); renderRace(true); saveState();
}

function addPoint(abbr, amount=1){
  const search = String(abbr).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
  const team = teams.find(t => {
    const n = t.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
    return t.abbr.toLowerCase()===search || n===search || n.includes(search);
  });
  if(!team) return;

  const pontosRecebidos = Math.max(0, Number(amount || 0));
  if(pontosRecebidos <= 0) return;

  const scoreAntes = Math.max(0, Number(team.score || 0));
  const total = scoreAntes + pontosRecebidos;
  team.lastBoost = Date.now();
  showBoost(team, pontosRecebidos);

  // MÓDULO 34: sobra de diamantes para o próximo duelo.
  // Exemplo: meta 300, time com 280 recebe 99 => campeão, volta com 79 pontos no próximo duelo.
  // Se o presente for enorme, conta todas as metas completas e mantém o restante.
  if(total >= META){
    const vitoriasGanhas = Math.floor(total / META);
    const sobraProximoDuelo = total % META;
    team.wins += vitoriasGanhas;
    team.score = sobraProximoDuelo;
    visualScore[team.abbr] = sobraProximoDuelo;

    const winnerCopy = {...team, score: META};
    sortTeams();
    renderRace(true);
    showChampion(winnerCopy);

    if(sobraProximoDuelo > 0){
      setTimeout(()=>{
        visualScore[team.abbr] = sobraProximoDuelo;
        sortTeams();
        renderRace(true);
      }, 350);
    }
  } else {
    team.score = total;
    sortTeams();
    renderRace(true);
  }
  saveState();
}

const WINS_BOARD_SETTINGS_KEY = "corrida_wins_board_settings";
function getWinsBoardSettings(){
  try{return Object.assign({size:75,x:50,y:50},JSON.parse(localStorage.getItem(WINS_BOARD_SETTINGS_KEY)||"{}"));}
  catch(_){return {size:75,x:50,y:50};}
}
function applyWinsBoardSettings(settings){
  const board=document.getElementById("wins-board"); if(!board)return;
  const st=Object.assign(getWinsBoardSettings(),settings||{});
  st.size=Math.max(45,Math.min(140,Number(st.size)||75));
  st.x=Math.max(3,Math.min(97,Number(st.x)||50));
  st.y=Math.max(3,Math.min(97,Number(st.y)||50));
  board.style.setProperty("--wins-board-scale",String(st.size/100));
  board.style.left=st.x+"%"; board.style.top=st.y+"%";
}
function saveWinsBoardPosition(x,y){
  const st=getWinsBoardSettings(); st.x=Math.max(3,Math.min(97,x)); st.y=Math.max(3,Math.min(97,y)); st.at=Date.now();
  localStorage.setItem(WINS_BOARD_SETTINGS_KEY,JSON.stringify(st)); applyWinsBoardSettings(st);
}
function enableWinsBoardDrag(){
  const board=document.getElementById("wins-board"), handle=board?.querySelector(".wins-board-header"); if(!board||!handle)return;
  let dragging=false, dx=0, dy=0;
  handle.addEventListener("pointerdown",e=>{dragging=true; const r=board.getBoundingClientRect(); dx=e.clientX-(r.left+r.width/2); dy=e.clientY-(r.top+r.height/2); handle.setPointerCapture(e.pointerId); e.preventDefault();});
  handle.addEventListener("pointermove",e=>{if(!dragging)return; const game=document.getElementById("game"); const r=game.getBoundingClientRect(); saveWinsBoardPosition(((e.clientX-dx-r.left)/r.width)*100,((e.clientY-dy-r.top)/r.height)*100);});
  const stop=e=>{dragging=false; try{handle.releasePointerCapture(e.pointerId)}catch(_){}}; handle.addEventListener("pointerup",stop); handle.addEventListener("pointercancel",stop);
}
applyWinsBoardSettings(); enableWinsBoardDrag();
function renderWinsBoard(){
  const board = document.getElementById("wins-board");
  const list = document.getElementById("wins-board-list");
  if(!board || !list) return;
  const ordered = [...teams]
    .filter(t => Number(t.wins || 0) > 0)
    .sort((a,b)=> Number(b.wins||0)-Number(a.wins||0) || a.name.localeCompare(b.name))
    .slice(0,10);
  list.innerHTML = ordered.length
    ? ordered.map((t,i)=>`<div class="wins-board-row"><span>${i+1}º</span><img src="${logoSrc(t)}" alt="${t.name}" title="${t.name}" onerror="this.src='assets/logos/_FALTA_ESCUDO.png'"><b>${Number(t.wins||0)} ${Number(t.wins||0)===1?'VITÓRIA':'VITÓRIAS'}</b></div>`).join('')
    : '<div class="wins-board-empty">NENHUM TIME TEM VITÓRIA AINDA</div>';
}
function toggleWinsBoard(force){
  const board = document.getElementById("wins-board");
  if(!board) return;
  renderWinsBoard();
  const show = typeof force === 'boolean' ? force : !board.classList.contains('show');
  board.classList.toggle('show', show);
}
function sendWinsBoardState(action){
  if(action === 'show') toggleWinsBoard(true);
  else if(action === 'hide') toggleWinsBoard(false);
  else toggleWinsBoard();
}
document.addEventListener('keydown', e=>{
  if(String(e.key||'').toLowerCase()==='v') sendWinsBoardState('toggle');
  if(e.key==='Escape') sendWinsBoardState('hide');
});
window.addEventListener('storage', e=>{
  if(e.key === WINS_BOARD_SETTINGS_KEY){ applyWinsBoardSettings(); return; }
  if(e.key !== 'corrida_wins_board_command' || !e.newValue) return;
  try{
    const cmd=JSON.parse(e.newValue);
    sendWinsBoardState(cmd.action || 'toggle');
  }catch(_){ sendWinsBoardState(e.newValue); }
});

function showBoost(team, amount){
  const row = race.querySelector(`[data-team="${team.abbr}"]`);
  if(row){
    row.classList.remove("boost","gift-small","gift-medium","gift-epic","combo10","combo50","combo100");
    void row.offsetWidth;
    row.classList.add("boost");
    if(amount > 100) row.classList.add("gift-epic","combo100");
    else if(amount > 10) row.classList.add("gift-medium","combo50");
    else row.classList.add("gift-small","combo10");
    setTimeout(()=>row.classList.remove("boost","gift-small","gift-medium","gift-epic","combo10","combo50","combo100"), 1200);
  }
  if(amount >= 10){
    const toast = document.getElementById("combo-toast");
    const label = amount >= 100 ? "COMBO ÉPICO" : amount >= 50 ? "COMBO FORTE" : "COMBO";
    toast.textContent = `⚡ ${label}: ${team.name} +${amount}`;
    toast.classList.remove("show"); void toast.offsetWidth; toast.classList.add("show");
  }
}

function showUltraGift(team, amount, ev={}){
  if(UI_CONFIG.ultra_gift_enabled === false) return;
  const threshold = Math.max(1, Number(UI_CONFIG.ultra_gift_threshold || 99));
  const diamonds = Number(ev.diamonds || 0);
  const triggerValue = Math.max(Number(amount || 0), diamonds);
  if(triggerValue < threshold) return;

  const game = document.getElementById("game");
  const old = document.getElementById("ultra-gift-fx");
  if(old) old.remove();
  const row = race.querySelector(`[data-team="${team.abbr}"]`);
  if(row){
    row.classList.remove("ultra-gift-row");
    void row.offsetWidth;
    row.classList.add("ultra-gift-row");
    setTimeout(()=>row.classList.remove("ultra-gift-row"), Math.max(1800, Number(UI_CONFIG.ultra_gift_duration || 3)*1000));
  }
  game.classList.remove("ultra-gift-mode","ultra-gift-cinematic","ultra-gift-slowmo","ultra-gift-dim","shake");
  void game.offsetWidth;
  game.classList.add("ultra-gift-mode","shake");
  if(UI_CONFIG.ultra_gift_cinematic !== false) game.classList.add("ultra-gift-cinematic");
  if(UI_CONFIG.ultra_gift_slowmo !== false) game.classList.add("ultra-gift-slowmo");
  if(UI_CONFIG.ultra_gift_dim !== false) game.classList.add("ultra-gift-dim");

  const fx = document.createElement("div");
  fx.id = "ultra-gift-fx";
  fx.style.setProperty("--team", team.color);
  const safeText = (v)=>String(v||'').replace(/[<>&]/g, c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
  const safeAttr = (v)=>String(v||'').replace(/["<>&]/g, c=>({'"':'&quot;','<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
  const user = ev.user ? `<div class="ultra-user">${safeText(ev.user)}</div>` : "";
  const gift = ev.gift ? `<div class="ultra-gift-name">${safeText(ev.gift)} • +${amount}</div>` : `<div class="ultra-gift-name">+${amount} PONTOS</div>`;
  const avatarUrl = ev.avatar || ev.avatar_url || ev.profilePictureUrl || ev.profile_picture || "";
  const avatar = avatarUrl ? `<img class="ultra-avatar" src="${safeAttr(avatarUrl)}" alt="${safeAttr(ev.user || 'perfil')}" onerror="this.style.display='none'">` : "";
  fx.innerHTML = `
    <div class="ultra-cinema-dim"></div>
    <div class="ultra-charge"></div>
    <div class="ultra-bg"></div>
    <div class="ultra-ring"></div>
    ${UI_CONFIG.ultra_gift_shockwave === false ? "" : '<div class="ultra-shockwave"></div>'}
    <div class="ultra-card">
      <div class="ultra-title">${UI_CONFIG.ultra_gift_text || "🔥 MODO ULTRA GIFT 🔥"}</div>
      ${avatar}
      <img class="ultra-team-logo" src="${safeAttr(team.logo)}" alt="${safeAttr(team.name)}">
      <div class="ultra-team">${safeText(team.name)}</div>
      ${gift}
      ${user}
    </div>
    ${UI_CONFIG.ultra_gift_rays === false ? "" : '<div class="ultra-rays"></div>'}
    ${UI_CONFIG.ultra_gift_particles === false ? "" : '<div class="ultra-particles"></div>'}
  `;
  game.appendChild(fx);
  setTeamImage(fx.querySelector(".ultra-team-logo"), team);
  const particles = fx.querySelector(".ultra-particles");
  if(particles){
    for(let i=0;i<95;i++){
      const p = document.createElement("i");
      p.style.setProperty("--x", `${(Math.random()*2-1)*310}px`);
      p.style.setProperty("--y", `${(Math.random()*2-1)*410}px`);
      p.style.animationDelay = `${Math.random()*0.22}s`;
      particles.appendChild(p);
    }
  }
  const ms = Math.max(1200, Number(UI_CONFIG.ultra_gift_duration || 3)*1000);
  setTimeout(()=>{fx.remove(); game.classList.remove("ultra-gift-mode","ultra-gift-cinematic","ultra-gift-slowmo","ultra-gift-dim","shake");}, ms);
}

function renderTopChampions(){
  const winners = [...teams].sort((a,b)=> b.wins-a.wins || b.score-a.score || a.name.localeCompare(b.name)).slice(0, UI_CONFIG.show_top5 ? 5 : 3);
  topCards.forEach((card,i)=>{
    const t = winners[i];
    const img = card.querySelector(".mini-badge img");
    const text = card.querySelector(".mini-badge span");
    if(t && t.wins > 0){
      setTeamImage(img, t); img.style.display = "block"; text.textContent = "";
      card.querySelector("strong").textContent = t.wins;
      card.title = `${t.name}: ${t.wins} vitórias`;
    }else{
      img.removeAttribute("src"); img.style.display = "none"; text.textContent = "---";
      card.querySelector("strong").textContent = 0;
      card.title = "Sem campeão ainda";
    }
  });
}

function showChampion(team){
  const alert = document.getElementById("champion-alert");
  setTeamImage(alert.querySelector(".champion-logo img"), team);
  alert.querySelector(".champion-sub").textContent = `${team.name} +1 VITÓRIA`;
  alert.classList.remove("show"); void alert.offsetWidth; alert.classList.add("show");
  const championMs = Math.max(1000, Number(UI_CONFIG.champion_duration || 8) * 1000);
  setTimeout(()=>alert.classList.remove("show"), championMs);
  const game = document.getElementById("game");
  game.classList.add("flash","shake","goal-mode","finish-celebrate");
  setTimeout(()=>game.classList.remove("flash","shake","goal-mode","finish-celebrate"), Math.min(championMs, 3500));
  showGoalExplosion(team);
  burstConfetti(team.color);
}

function showGoalExplosion(team){
  const game = document.getElementById("game");
  const old = document.getElementById("goal-explosion");
  if(old) old.remove();

  const fx = document.createElement("div");
  fx.id = "goal-explosion";
  fx.style.setProperty("--team", team.color);
  fx.innerHTML = `
    <div class="goal-shock"></div>
    <div class="goal-title">${UI_CONFIG.show_goal_text ? "GOOOOL!" : ""}</div>
    <div class="goal-team">${team.name}</div>
    <div class="goal-ray ray1"></div>
    <div class="goal-ray ray2"></div>
    <div class="goal-ray ray3"></div>
    <div class="goal-sparks"></div>
  `;
  game.appendChild(fx);

  const sparks = fx.querySelector(".goal-sparks");
  for(let i=0;i<34;i++){
    const p = document.createElement("i");
    p.style.setProperty("--ang", `${Math.random()*360}deg`);
    p.style.setProperty("--dist", `${70 + Math.random()*180}px`);
    p.style.animationDelay = `${Math.random()*0.12}s`;
    sparks.appendChild(p);
  }
  setTimeout(()=>fx.remove(), Math.max(2200, Number(UI_CONFIG.champion_duration || 8) * 1000));
}

function burstConfetti(color){
  const box = document.getElementById("confetti");
  box.innerHTML = "";
  const colors = [color,"#ffd400","#ffffff","#00d8ff","#ff00aa"];
  for(let i=0;i<90;i++){
    const p = document.createElement("div");
    p.className = "confetti-piece";
    p.style.left = `${Math.random()*100}%`;
    p.style.background = colors[Math.floor(Math.random()*colors.length)];
    p.style.animationDelay = `${Math.random()*0.35}s`;
    p.style.animationDuration = `${1.1 + Math.random()*1.1}s`;
    p.style.transform = `rotate(${Math.random()*180}deg)`;
    box.appendChild(p);
  }
  setTimeout(()=>box.innerHTML="", 2600);
}

document.addEventListener("keydown", e=>{
  if(String(e.key).toLowerCase() === "a" && !e.repeat){ toggleScorersBoard(); return; }
  if(e.code === "Space") addPoint(teams[Math.floor(Math.random()*teams.length)].abbr, 1);
  if(e.key === "0") resetGame(true);
  if(e.key === "1") addPoint("FLA",25);
  if(e.key === "2") addPoint("PAL",25);
  if(e.key === "3") addPoint("COR",25);
  if(e.key === "4") addPoint("GRE",25);
  if(e.key === "5") addPoint("VIT",25);
  if(e.key === "6") addPoint("CUI",25);
  if(e.key === "7") addPoint("FLA",300);
});

// Integração em tempo real: servidor Python -> overlay via EventSource
window.addTeamPoints = addPoint;
let usingStream = false;
let fallbackTimer = null;


function applyRankingTitle(){
  const el = document.getElementById("ranking-title");
  if(!el) return;
  el.textContent = UI_CONFIG.ranking_title_text || "🏆 MAIORES CAMPEÕES";
  el.style.left = `${Number(UI_CONFIG.ranking_title_x ?? 50)}%`;
  el.style.top = `${Number(UI_CONFIG.ranking_title_y ?? 4)}%`;
  el.style.transform = `translate(-50%,-50%) scale(${Number(UI_CONFIG.ranking_title_scale || 100)/100})`;
  el.style.color = UI_CONFIG.ranking_title_color || "#ffd400";
  el.style.display = UI_CONFIG.show_ranking_title === false ? "none" : "block";
}

function applyRaceRankTitle(){
  const el = document.getElementById("race-rank-title");
  if(!el) return;
  el.textContent = UI_CONFIG.race_rank_title_text || "📊 RANKING";
  const root = document.documentElement;
  root.style.setProperty("--race-title-x", `${Number(UI_CONFIG.race_rank_title_x ?? 50)}%`);
  root.style.setProperty("--race-title-y", `${Number(UI_CONFIG.race_rank_title_y ?? 8)}%`);
  root.style.setProperty("--race-title-width", `${Number(UI_CONFIG.race_rank_title_width || 88)}%`);
  root.style.setProperty("--race-title-height", `${Number(UI_CONFIG.race_rank_title_height || 42)}px`);
  root.style.setProperty("--race-title-scale", `${Number(UI_CONFIG.race_rank_title_scale || 100)/100}`);
  root.style.setProperty("--race-title-color", UI_CONFIG.race_rank_title_color || "#ffffff");
  document.body.classList.toggle("hide-race-rank-title", UI_CONFIG.show_race_rank_title === false);
}

function applyConfig(config){
  document.body.classList.toggle("top5-mode", config && config.show_top5 === true);
  if(!config) return;
  try{
    const txt = JSON.stringify(config);
    if(txt === lastConfigText) return;
    lastConfigText = txt;
  }catch(e){}
  if(Array.isArray(config.teams)) applyTeamsConfig(config.teams);
  const oldTimerEnabled = !!UI_CONFIG.tournament_timer_enabled;
  const oldTimerMinutes = Number(UI_CONFIG.tournament_minutes || 5);
  UI_CONFIG = Object.assign(UI_CONFIG, config);
  if(!UI_CONFIG.tournament_timer_enabled){
    tournamentEndAt = 0;
    tournamentFinishedLock = false;
  }else if(!oldTimerEnabled || Number(UI_CONFIG.tournament_minutes || 5) !== oldTimerMinutes){
    restartTournamentTimer();
  }
  updateTournamentTimerUI();
  if(Number(config.meta)){
    META = Number(config.meta);
    renderRace(false);
  }
  const root = document.documentElement;
  root.style.setProperty("--champion-duration", `${Number(UI_CONFIG.champion_duration || 8)}s`);
  root.style.setProperty("--champion-scale", `${Number(UI_CONFIG.champion_size || 120) / 100}`);
  root.style.setProperty("--champion-name-size", `${Number(UI_CONFIG.champion_name_size || 38)}px`);
  root.style.setProperty("--ranking-scale", `${Number(UI_CONFIG.ranking_scale || 115) / 100}`);
  root.style.setProperty("--ranking-x", `${Number(UI_CONFIG.ranking_x ?? 50)}%`);
  root.style.setProperty("--ranking-y", `${Number(UI_CONFIG.ranking_y ?? 0)}%`);
  root.style.setProperty("--ranking-width", `${Number(UI_CONFIG.ranking_width || 96)}%`);
  root.style.setProperty("--ranking-logo-size", `${Number(UI_CONFIG.ranking_logo_size || 42)}px`);
  root.style.setProperty("--ranking-score-size", `${Number(UI_CONFIG.ranking_score_size || 30)}px`);
  root.style.setProperty("--ranking-logo-x", `${Number(UI_CONFIG.ranking_logo_x || 0)}px`);
  root.style.setProperty("--ranking-logo-y", `${Number(UI_CONFIG.ranking_logo_y || 0)}px`);
  root.style.setProperty("--ranking-score-x", `${Number(UI_CONFIG.ranking_score_x || 0)}px`);
  root.style.setProperty("--ranking-score-y", `${Number(UI_CONFIG.ranking_score_y || 0)}px`);
  root.style.setProperty("--ranking-victory-x", `${Number(UI_CONFIG.ranking_victory_x || 0)}px`);
  root.style.setProperty("--ranking-victory-y", `${Number(UI_CONFIG.ranking_victory_y || 0)}px`);
  root.style.setProperty("--ranking-gap", `${Number(UI_CONFIG.ranking_gap || 4)}px`);
  root.style.setProperty("--ranking-height", `${Number(UI_CONFIG.ranking_height || 78)}px`);
  root.style.setProperty("--effect-time", `${Number(UI_CONFIG.effect_time || 10) / 10}s`);
  root.style.setProperty("--lightning-power", `${Number(UI_CONFIG.lightning_power || 100) / 100}`);
  root.style.setProperty("--ultra-gift-duration", `${Number(UI_CONFIG.ultra_gift_duration || 3)}s`);
  root.style.setProperty("--finish-label-size", `${Number(UI_CONFIG.finish_label_size || 15)}px`);
  root.style.setProperty("--finish-label-x", `${Number(UI_CONFIG.finish_label_x || 0)}px`);
  root.style.setProperty("--finish-label-y", `${Number(UI_CONFIG.finish_label_y ?? 50)}%`);
  root.style.setProperty("--finish-label-rotation", `${Number(UI_CONFIG.finish_label_rotation ?? -90)}deg`);
  root.style.setProperty("--finish-label-color", String(UI_CONFIG.finish_label_color || '#ffffff'));
  root.style.setProperty("--finish-label-glow-color", String(UI_CONFIG.finish_label_glow_color || '#00e6ff'));
  root.style.setProperty("--finish-label-glow", `${Number(UI_CONFIG.finish_label_glow ?? 13)}px`);
  const finishLabel=document.querySelector('.finish-label');
  if(finishLabel) finishLabel.textContent=String(UI_CONFIG.finish_label_text || 'CHEGADA');
  document.body.classList.toggle("hide-finish-label", UI_CONFIG.show_finish_label === false);
  document.body.classList.toggle("hide-live-status", !UI_CONFIG.show_live_status);
  document.body.classList.toggle("hide-ranking", UI_CONFIG.show_ranking === false);
  document.body.classList.toggle("hide-ranking-title", UI_CONFIG.show_ranking_title === false);
  document.body.classList.toggle("hide-goal-text", !UI_CONFIG.show_goal_text);
  document.body.classList.toggle("hide-champion-name", !UI_CONFIG.show_champion_name);
  applyRankingTitle();
  applyRaceRankTitle();
}

function applyStatus(st){
  const status = document.getElementById("live-status");
  if(!status) return;
  st = st || {};
  if(st.connected){
    status.textContent = `🟢 @${st.user}`;
    status.classList.add("online");
  }else if(st.connecting){
    status.textContent = `🟡 CONECTANDO @${st.user}`;
    status.classList.remove("online");
  }else{
    status.textContent = `🔴 ${st.message || "OFFLINE"}`;
    status.classList.remove("online");
  }
}

function applyEvent(ev){
  if(!ev) return;
  lastServerEvent = Math.max(lastServerEvent, Number(ev.id || 0));
  if(ev.source === "reset"){
    resetGame(ev.full !== false);
    return;
  }
  if(ev.source === "config"){
    if(ev.config) applyConfig(ev.config);
    return;
  }
  if(ev.source === "board_control"){
    const action = ev.action || "toggle";
    if(ev.board === "champions") sendWinsBoardState(action);
    if(ev.board === "scorers"){
      const board = ensureScorersBoard();
      renderScorersBoard();
      if(action === "show") board.classList.add("show");
      else if(action === "hide") board.classList.remove("show");
      else board.classList.toggle("show");
    }
    return;
  }
  if(!ev.team) return;

  // Comentário serve apenas para escolher o time.
  // Só soma pontos quando o servidor enviar quantidade maior que zero (presentes/painel).
  const amount = Number(ev.amount || 0);
  if(amount <= 0) return;
  registerGiftScorer(ev.team, ev);
  addPoint(ev.team, amount);
  const ultraTeam = teams.find(t => t.name === ev.team || t.abbr === ev.team || t.name.toLowerCase() === String(ev.team).toLowerCase());
  if(ultraTeam) showUltraGift(ultraTeam, amount, ev);

  const giftLine = document.getElementById("gift-line");
  if(giftLine){
    if(ev.user || ev.gift){
      const tipo = ev.source === "comentario" ? "comentou" : "enviou presente";
      giftLine.textContent = `${ev.user || "Usuário"} ${tipo} para ${ev.team} +${ev.amount}`;
    }else{
      giftLine.textContent = `${ev.team} +${ev.amount}`;
    }
  }

  if(ev.user){
    const toast = document.getElementById("combo-toast");
    const icon = ev.source === "comentario" ? "💬" : "🎁";
    const comboTxt = ev.combo && Number(ev.combo) > 1 ? ` x${ev.combo}` : "";
    toast.textContent = `${icon}${comboTxt} ${ev.user} ajudou ${ev.team} +${ev.amount}`;
    toast.classList.remove("show"); void toast.offsetWidth; toast.classList.add("show");
  }
}

function handleStreamMessage(msg){
  if(msg.game_state) applyCentralGameState(msg.game_state);
  if(msg.kind === 'game_state' && msg.payload) applyCentralGameState(msg.payload);
  if(msg.config) applyConfig(msg.config);
  if(msg.status) applyStatus(msg.status);
  if(msg.kind === "event") applyEvent(msg.payload);
}

function startRealtime(){
  if(typeof EventSource === "undefined"){
    startFallbackPolling();
    return;
  }
  try{
    const es = new EventSource(`${SERVER_URL}/stream`);
    es.onopen = () => { usingStream = true; if(fallbackTimer) clearInterval(fallbackTimer); };
    es.onmessage = (e) => {
      try{ handleStreamMessage(JSON.parse(e.data)); }
      catch(err){ console.warn("Evento inválido", err); }
    };
    es.onerror = () => {
      usingStream = false;
      applyStatus({connected:false,message:"SERVIDOR OFF"});
      startFallbackPolling();
    };
  }catch(e){
    startFallbackPolling();
  }
}

async function pollServerEvents(){
  if(usingStream) return;
  try{
    const res = await fetch(`${SERVER_URL}/events?since=${lastServerEvent}`, {cache:"no-store"});
    const data = await res.json();
    if(data.config) applyConfig(data.config);
    if(data.status) applyStatus(data.status);
    (data.events || []).forEach(applyEvent);
  }catch(e){
    applyStatus({connected:false,message:"SERVIDOR OFF"});
  }
}
function startFallbackPolling(){
  if(fallbackTimer) return;
  fallbackTimer = setInterval(pollServerEvents, 900);
  pollServerEvents();
}

// Segurança extra: mesmo com EventSource aberto, consulta /config a cada 1 segundo.
// Assim o overlay atualiza em tempo real mesmo se o navegador bloquear o stream.
async function pollConfigRealtime(){
  try{
    const res = await fetch(`${SERVER_URL}/config?t=${Date.now()}`, {cache:'no-store'});
    const data = await res.json();
    if(data.config) applyConfig(data.config);
    if(data.status) applyStatus(data.status);
  }catch(e){}
}
function startConfigRealtimePoll(){
  if(configPollTimer) return;
  configPollTimer = setInterval(pollConfigRealtime, 1000);
  pollConfigRealtime();
}

window.addEventListener("resize", ()=>renderRace(false));
loadScorers();
loadState();
loadCentralGameState();
sortTeams();
renderRace(false);
startRealtime();
startConfigRealtimePoll();
startTournamentTicker();
