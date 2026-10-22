import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime

# Las URLs de los Webhooks se leen exclusivamente de Secrets (Variables de Entorno)
WEBHOOKS = {
    "genshin": os.getenv("WEBHOOK_GENSHIN", "").strip(),
    "wuwa": os.getenv("WEBHOOK_WUWA", "").strip(),
    "zzz": os.getenv("WEBHOOK_ZZZ", "").strip()
}

HISTORY_FILE = "posted_codes.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"genshin": ["GENSHINGIFT"], "wuwa": ["WUTHERINGGIFT"], "zzz": ["ZENLESSGIFT"]}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def send_code_to_discord(game_key, game_name, code, reward, direct_url, color):
    webhook_url = WEBHOOKS.get(game_key)
    if not webhook_url:
        print(f"[!] Aviso: No se encontró webhook configurado para {game_key}. Saltando envío.")
        return

    desc = f"# `{code}`\n\n💎 **Recompensas:**\n**{reward}**\n\n"
    if direct_url:
        desc += f"🔗 [**Canjear directamente con tu cuenta aquí**]({direct_url})\n\n"
    else:
        desc += "*Canjéalo directamente dentro del juego en Ajustes -> Cuenta -> Código de canje.*\n\n"
    desc += "*Copia el código de arriba antes de que expire.*"

    embed = {
        "title": f"🎁 Código Activo — {game_name}",
        "description": desc,
        "color": color,
        "footer": {"text": "Gachyn Oficial • Alertas de Códigos Automáticas"},
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "username": f"{game_name} Codes",
        "embeds": [embed]
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[✓] Nuevo código publicado en {game_name}: {code}")
    except Exception as e:
        print(f"[!] Error publicando en Discord: {e}")

def fetch_wiki_codes(wiki_slug, game_key):
    url = f"https://{wiki_slug}.fandom.com/api.php?action=parse&page=Promotional_Code&prop=wikitext&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    found = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            matches = re.findall(r"\{\{Code\|([A-Za-z0-9]+)\}\}", wikitext)
            for m in matches:
                clean = m.strip().upper()
                if 4 <= len(clean) <= 20:
                    found.append(clean)
    except Exception as e:
        print(f"[!] Fandom check ({game_key}): {e}")
    return list(set(found))

def fetch_reddit_codes(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q=flair%3A%22Codes%22+OR+flair%3A%22Code%22+OR+title%3A%22Code%22&sort=new&restrict_sr=on&limit=5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GachynCodeBot/2.0"})
    found_codes = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            posts = data.get("data", {}).get("children", [])
            for p in posts:
                title = p.get("data", {}).get("title", "")
                selftext = p.get("data", {}).get("selftext", "")
                words = re.findall(r"\b[A-Z0-9]{6,16}\b", title + " " + selftext)
                for w in words:
                    if not w.isnumeric() and not w in ["GENSHIN", "IMPACT", "WUTHERING", "WAVES", "ZENLESS", "REDDIT"]:
                        found_codes.append(w)
    except Exception as e:
        print(f"[!] Reddit check ({subreddit}): {e}")
    return list(set(found_codes))

def main():
    print(f"[*] Chequeo de códigos iniciado: {datetime.utcnow().isoformat()}")
    history = load_history()
    new_found = False

    # 1. Genshin Impact
    g_codes = set(fetch_wiki_codes("genshin-impact", "genshin") + fetch_reddit_codes("Genshin_Impact"))
    for code in g_codes:
        if code not in history["genshin"]:
            send_code_to_discord("genshin", "Genshin Impact", code, "Protogemas y materiales oficiales", f"https://genshin.hoyoverse.com/es/gift?code={code}", 0xe67e22)
            history["genshin"].append(code)
            new_found = True

    # 2. Wuthering Waves
    w_codes = set(fetch_wiki_codes("wutheringwaves", "wuwa") + fetch_reddit_codes("WutheringWaves"))
    for code in w_codes:
        if code not in history["wuwa"]:
            send_code_to_discord("wuwa", "Wuthering Waves", code, "Astritas y materiales oficiales de Kuro Games", None, 0x3498db)
            history["wuwa"].append(code)
            new_found = True

    # 3. Zenless Zone Zero
    z_codes = set(fetch_wiki_codes("zenless-zone-zero", "zzz") + fetch_reddit_codes("ZZZ_Official"))
    for code in z_codes:
        if code not in history["zzz"]:
            send_code_to_discord("zzz", "Zenless Zone Zero", code, "Policromos y materiales de HoYoverse", f"https://zenless.hoyoverse.com/redemption?code={code}", 0x2ecc71)
            history["zzz"].append(code)
            new_found = True

    if new_found:
        save_history(history)
        print("[✓] Nuevos códigos detectados y guardados.")
    else:
        print("[*] No se detectaron códigos nuevos en esta iteración.")

if __name__ == "__main__":
    main()
