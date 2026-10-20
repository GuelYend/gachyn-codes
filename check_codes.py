import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# URLs de los Webhooks de Discord (pueden ser leídas de variables de entorno)
WEBHOOKS = {
    "genshin": os.getenv("WEBHOOK_GENSHIN", "https://discord.com/api/webhooks/1562205339426885742/ZUQv__odlL-04L4kJZ9NTt61Z4cQUb7v3091iYat75JKkc3lrpa1Z4mpIZfNqJJjG290"),
    "wuwa": os.getenv("WEBHOOK_WUWA", "https://discord.com/api/webhooks/1562205342467756195/KKnQpZbdOLQHtkhmPSP8sLHp5yDtMe_fi-ZCfR9o018fLiyLYouiuLfpgvn-mJn1HuUo"),
    "zzz": os.getenv("WEBHOOK_ZZZ", "https://discord.com/api/webhooks/1562205347777618024/zFYOra84OV4EVNuLgvXsBxnCfP3FHLQ27mTltGrLT5DFcwJu46P9NcE329G4FNAnVvfW")
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

def fetch_reddit_codes(subreddit, game_name):
    """Consulta la API pública de Reddit para detectar códigos nuevos de la comunidad."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q=flair%3A%22Codes%22+OR+flair%3A%22Code%22+OR+title%3A%22Code%22&sort=new&restrict_sr=on&limit=5"
    req = urllib.request.Request(url, headers={"User-Agent": "GachynCodeBot/1.0"})
    found_codes = []
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            posts = data.get("data", {}).get("children", [])
            for p in posts:
                title = p.get("data", {}).get("title", "")
                selftext = p.get("data", {}).get("selftext", "")
                # Extraer posibles códigos de palabras en mayúsculas de 6 a 16 caracteres
                words = (title + " " + selftext).replace(":", " ").replace(",", " ").split()
                for w in words:
                    cleaned = "".join([c for c in w if c.isalnum()]).upper()
                    if 6 <= len(cleaned) <= 18 and cleaned.isupper() and any(c.isalpha() for c in cleaned):
                        if cleaned not in ["GENSHIN", "IMPACT", "WUTHERING", "WAVES", "ZENLESS", "ZONE", "UPDATE", "REDDIT"]:
                            found_codes.append(cleaned)
    except Exception as e:
        print(f"[!] Info: Consulta a {subreddit} finalizada ({e})")
    return list(set(found_codes))

def main():
    print("[*] Iniciando chequeo de códigos en la nube...")
    history = load_history()
    new_found = False

    # 1. Genshin
    genshin_found = fetch_reddit_codes("Genshin_Impact", "Genshin Impact")
    for code in genshin_found:
        if code not in history["genshin"]:
            send_code_to_discord("genshin", "Genshin Impact", code, "Recompensas oficiales de HoYoverse", f"https://genshin.hoyoverse.com/es/gift?code={code}", 0xe67e22)
            history["genshin"].append(code)
            new_found = True

    # 2. WuWa
    wuwa_found = fetch_reddit_codes("WutheringWaves", "Wuthering Waves")
    for code in wuwa_found:
        if code not in history["wuwa"]:
            send_code_to_discord("wuwa", "Wuthering Waves", code, "Recompensas oficiales de Kuro Games", None, 0x3498db)
            history["wuwa"].append(code)
            new_found = True

    # 3. ZZZ
    zzz_found = fetch_reddit_codes("ZZZ_Official", "Zenless Zone Zero")
    for code in zzz_found:
        if code not in history["zzz"]:
            send_code_to_discord("zzz", "Zenless Zone Zero", code, "Recompensas oficiales de HoYoverse", f"https://zenless.hoyoverse.com/redemption?code={code}", 0x2ecc71)
            history["zzz"].append(code)
            new_found = True

    if new_found:
        save_history(history)
        print("[✓] Nuevos códigos detectados y guardados en el historial.")
    else:
        print("[*] No hay códigos nuevos por ahora.")

if __name__ == "__main__":
    main()
