"""
CDX — Commercial Signal Intelligence Engine
Data Generator — Prompt 1

Generates 7 CSV files with real Latin music artist names sourced from
Kworb.net Spotify charts. Uses Playwright to scrape live chart data
(best-effort; falls back to hardcoded reference data gracefully).

Seed: 42 (fully reproducible)
"""

import os
import random
import time
import re
from datetime import timedelta, date
import pandas as pd

# ─── Seed for reproducibility ────────────────────────────────────────────────
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — LIVE KWORB SCRAPE (Playwright, best-effort)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KWORB_URLS = {
    "MX": "https://kworb.net/spotify/country/mx_daily.html",
    "CO": "https://kworb.net/spotify/country/co_daily.html",
    "AR": "https://kworb.net/spotify/country/ar_daily.html",
    "ES": "https://kworb.net/spotify/country/es_daily.html",
    "BR": "https://kworb.net/spotify/country/br_daily.html",
    "PE": "https://kworb.net/spotify/country/pe_daily.html",
    "CL": "https://kworb.net/spotify/country/cl_daily.html",
}


def scrape_kworb_charts():
    """Scrape top-20 chart positions per territory. Returns dict of
    {territory: [(position, artist_name, track_title, streams), ...]}
    Returns empty dict on any failure — data generation continues."""
    results = {}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"})
            for territory, url in KWORB_URLS.items():
                try:
                    page.goto(url, timeout=15000)
                    page.wait_for_selector("table", timeout=8000)
                    rows = page.query_selector_all("table tr")
                    chart_rows = []
                    for row in rows[1:21]:  # skip header, take top 20
                        cells = row.query_selector_all("td")
                        if len(cells) >= 7:
                            pos_text = cells[0].inner_text().strip()
                            artist_track = cells[2].inner_text().strip()
                            streams_text = cells[6].inner_text().strip()
                            try:
                                pos = int(re.sub(r'[^0-9]', '', pos_text))
                                streams = int(re.sub(r'[^0-9]', '', streams_text))
                                if " - " in artist_track:
                                    parts = artist_track.split(" - ", 1)
                                    artist = parts[0].strip()
                                    track = re.sub(r'\s*\(w\/.*', '', parts[1]).strip()
                                else:
                                    artist = artist_track
                                    track = "Unknown Track"
                                chart_rows.append((pos, artist, track, streams))
                            except (ValueError, IndexError):
                                continue
                    results[territory] = chart_rows
                    print(f"  Scraped {len(chart_rows)} rows for {territory}")
                    time.sleep(1.5)
                except Exception as e:
                    print(f"  Skipping {territory}: {e}")
            browser.close()
    except Exception as e:
        print(f"Playwright scrape failed entirely: {e}")
    return results


print("Attempting live Kworb chart scrape...")
live_chart_data = scrape_kworb_charts()
print(f"Live data obtained for territories: {list(live_chart_data.keys()) or 'none (using hardcoded)'}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — HARDCODED REAL ARTIST REFERENCE DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARTIST_REFERENCE = [
    # ── TIER 1: MEGA (50M+ monthly listeners, charting 4+ territories) ──
    {"name": "Peso Pluma",          "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["dopamina", "daño", "7-3", "tu con el", "LADY GAGA"],
     "monthly_listeners": 82000000, "ig_followers": 18500000, "yt_subs": 12000000},
    {"name": "Bad Bunny",           "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["BAILE INoLVIDABLE", "DtMF", "EoO", "NUEVAYoL", "PITORRO DE COCO"],
     "monthly_listeners": 75000000, "ig_followers": 45000000, "yt_subs": 25000000},
    {"name": "Fuerza Regida",       "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["Marlboro Rojo", "TU SANCHO", "CHAVALITAS", "COMO OREO", "Bebe Dame"],
     "monthly_listeners": 38000000, "ig_followers": 9200000, "yt_subs": 7800000},
    {"name": "Karol G",             "country": "CO", "genre": "reggaeton/pop latino",
     "top_tracks": ["Oki Doki", "Si Antes Te Hubiera Conocido", "Cairo", "Gatúbela", "TQG"],
     "monthly_listeners": 55000000, "ig_followers": 62000000, "yt_subs": 22000000},
    {"name": "J Balvin",            "country": "CO", "genre": "reggaeton",
     "top_tracks": ["Poblado", "Ritmo", "Mi Gente", "Reggaeton", "LOCO"],
     "monthly_listeners": 32000000, "ig_followers": 54000000, "yt_subs": 18000000},

    # ── TIER 2: REGIONAL STARS ──
    {"name": "Beéle",               "country": "CO", "genre": "pop urbano",
     "top_tracks": ["quédate", "no tiene sentido", "mi refe", "top diesel", "Aunque No Sea Contigo"],
     "monthly_listeners": 24000000, "ig_followers": 5800000, "yt_subs": 3200000},
    {"name": "Ryan Castro",         "country": "CO", "genre": "pop urbano",
     "top_tracks": ["LA VILLA", "SANKA", "Ba Ba Bad Remix", "DÓNDE", "SOLO TU"],
     "monthly_listeners": 18000000, "ig_followers": 4100000, "yt_subs": 2900000},
    {"name": "Tito Double P",       "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["POR SUS BESOS", "dopamina", "daño", "7-3", "PA LO QUE SEA"],
     "monthly_listeners": 22000000, "ig_followers": 6200000, "yt_subs": 4100000},
    {"name": "Junior H",            "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["DROGA LETAL", "MIENTRAS DUERMES", "AMOR TUMBADO", "No Me Llames", "RARO"],
     "monthly_listeners": 19000000, "ig_followers": 7400000, "yt_subs": 5200000},
    {"name": "El Bogueto",          "country": "AR", "genre": "urbano latino",
     "top_tracks": ["Cuando No Era Cantante", "Cuando No Era Cantante - Remix", "BAÑO ROMANO", "NENA MALA"],
     "monthly_listeners": 17000000, "ig_followers": 3900000, "yt_subs": 2100000},
    {"name": "Bizarrap",            "country": "AR", "genre": "trap/electronic",
     "top_tracks": ["Daddy Yankee: BZRP Session Vol.66", "J Balvin: BZRP Session Vol.62",
                    "Shakira: BZRP Session Vol.53", "Nicky Jam: BZRP Session Vol.41"],
     "monthly_listeners": 35000000, "ig_followers": 12000000, "yt_subs": 18000000},
    {"name": "Blessd",              "country": "CO", "genre": "reggaeton/trap",
     "top_tracks": ["NUEVA YORK", "YOGURCITO", "YOGURCITO REMIX", "AMISTA", "COMO OREO"],
     "monthly_listeners": 15000000, "ig_followers": 5100000, "yt_subs": 3400000},
    {"name": "Quevedo",             "country": "ES", "genre": "trap/flamenco urbano",
     "top_tracks": ["NI BORRACHO", "TUCHAT", "Columbia", "Quevedo: BZRP Session Vol.52", "Cayó La Noche"],
     "monthly_listeners": 21000000, "ig_followers": 8300000, "yt_subs": 6100000},
    {"name": "Omar Courtz",         "country": "DO", "genre": "reggaeton/dembow",
     "top_tracks": ["FOREVER TU GANTEL", "WO OH OH", "$UELTA GATITA $UELTA", "POR SI MAÑANA NO ESTOY", "KOKO"],
     "monthly_listeners": 12000000, "ig_followers": 3200000, "yt_subs": 1800000},
    {"name": "ROSALÍA",             "country": "ES", "genre": "flamenco urbano",
     "top_tracks": ["La Perla", "LLYLM", "CANDY", "CHICKEN TERIYAKI", "Despechá"],
     "monthly_listeners": 28000000, "ig_followers": 22000000, "yt_subs": 8900000},
    {"name": "Ozuna",               "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["Pikito", "Enemigos", "Reggaetón En La Playa", "Se Preparó", "Taki Taki"],
     "monthly_listeners": 26000000, "ig_followers": 30000000, "yt_subs": 12000000},
    {"name": "Rauw Alejandro",      "country": "PR", "genre": "pop urbano",
     "top_tracks": ["Cosa Nuestra", "PUNTO 40", "VOID", "CAYÓ LA NOCHE feat", "Lokera"],
     "monthly_listeners": 23000000, "ig_followers": 13000000, "yt_subs": 7200000},
    {"name": "Romeo Santos",        "country": "US-DO", "genre": "bachata",
     "top_tracks": ["Dardos", "Imitadora", "Propuesta Indecente", "Yo También", "El Amigo"],
     "monthly_listeners": 19000000, "ig_followers": 19000000, "yt_subs": 9800000},
    {"name": "Neton Vega",          "country": "MX", "genre": "norteño/sierreño",
     "top_tracks": ["Pvta Luna", "Corazón de Tierra", "Amor del Bueno", "El As"],
     "monthly_listeners": 14000000, "ig_followers": 3100000, "yt_subs": 2800000},
    {"name": "Herencia De Grandes", "country": "MX", "genre": "banda/norteño",
     "top_tracks": ["Ya Borracho", "El Dolor Ajeno", "Corrido del Novillo", "Pétalos"],
     "monthly_listeners": 11000000, "ig_followers": 2700000, "yt_subs": 1900000},

    # ── TIER 3: RISING ──
    {"name": "Omar Camacho",        "country": "MX", "genre": "sierreño",
     "top_tracks": ["2+2", "4x4", "Ganas de Verte", "Letra y Miel"],
     "monthly_listeners": 9800000, "ig_followers": 2400000, "yt_subs": 1700000},
    {"name": "Lenin Ramírez",       "country": "MX", "genre": "banda",
     "top_tracks": ["Todo Lo Fue", "Inseparables", "Soy El Mejor", "La Gente"],
     "monthly_listeners": 8900000, "ig_followers": 2100000, "yt_subs": 1500000},
    {"name": "Kapo",                "country": "CO", "genre": "pop urbano",
     "top_tracks": ["DÓNDE", "LA VILLA", "INSECURE", "AYER", "Tú y Yo"],
     "monthly_listeners": 8200000, "ig_followers": 1900000, "yt_subs": 1300000},
    {"name": "Rels B",              "country": "ES", "genre": "pop urbano",
     "top_tracks": ["TU VAS SIN (fav)", "No Seas Desleal", "Marisol", "Déjala Que Vuelva", "Ahora Y Siempre"],
     "monthly_listeners": 11000000, "ig_followers": 3800000, "yt_subs": 2600000},
    {"name": "BeatBoy",             "country": "MX", "genre": "sierreño",
     "top_tracks": ["Pase y Toque", "El Pasón", "Mentiras y Más", "Llévate Las Llaves"],
     "monthly_listeners": 6400000, "ig_followers": 1600000, "yt_subs": 980000},
    {"name": "Virlan Garcia",       "country": "MX", "genre": "corridos",
     "top_tracks": ["Mi Entorno", "El Millonario", "El Terror", "Amor Sincero"],
     "monthly_listeners": 7100000, "ig_followers": 1800000, "yt_subs": 1200000},
    {"name": "Nanpa Básico",        "country": "CO", "genre": "pop urbano",
     "top_tracks": ["Hasta Aquí Llegué", "Tumbado", "No Sé Nada", "Buenas Vibras"],
     "monthly_listeners": 5800000, "ig_followers": 1400000, "yt_subs": 870000},
    {"name": "La T y La M",         "country": "AR", "genre": "cumbia/pop",
     "top_tracks": ["Soy Favela", "Amor de Vago", "Quiero Verte", "No Paro"],
     "monthly_listeners": 7900000, "ig_followers": 2000000, "yt_subs": 1400000},
    {"name": "Roze Oficial",        "country": "AR", "genre": "cumbia/pop",
     "top_tracks": ["Tu jardín con enanitos", "Tú y Yo", "El Destino", "Me Faltas"],
     "monthly_listeners": 6200000, "ig_followers": 1500000, "yt_subs": 980000},
    {"name": "Max Carra",           "country": "AR", "genre": "cumbia",
     "top_tracks": ["UWAIE - versión cumbia", "El Siguiente", "Traicionera", "Dame Más"],
     "monthly_listeners": 5600000, "ig_followers": 1300000, "yt_subs": 820000},
    {"name": "Kybba",               "country": "CO", "genre": "dancehall/pop",
     "top_tracks": ["Ba Ba Bad Remix", "Move Fawd", "Fuera del Cuadro"],
     "monthly_listeners": 4900000, "ig_followers": 1100000, "yt_subs": 720000},
    {"name": "Maluma",              "country": "CO", "genre": "reggaeton/pop",
     "top_tracks": ["Hawái", "ADMV", "Felices los 4", "Corazón", "Sin Contrato"],
     "monthly_listeners": 24000000, "ig_followers": 64000000, "yt_subs": 17000000},
    {"name": "Myke Towers",         "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["La Playa", "LALA", "Girl", "Bandido", "Almas Gemelas"],
     "monthly_listeners": 20000000, "ig_followers": 8500000, "yt_subs": 5300000},
    {"name": "Jhay Cortez",         "country": "PR", "genre": "R&B/reggaeton",
     "top_tracks": ["Con Otra Mente", "Dakiti", "Dime Cómo", "Mamiii", "No Me Conoce"],
     "monthly_listeners": 13000000, "ig_followers": 4400000, "yt_subs": 3100000},
    {"name": "Anuel AA",            "country": "PR", "genre": "trap latino",
     "top_tracks": ["China", "Secreto", "Que Más Pues", "Narcos", "Bichota"],
     "monthly_listeners": 16000000, "ig_followers": 23000000, "yt_subs": 9700000},
    {"name": "Eladio Carrión",      "country": "PR", "genre": "trap/rap",
     "top_tracks": ["Tú y Yo", "No Me Dejes Solo", "LALALALA", "Caminando", "Sen2 Kbrón"],
     "monthly_listeners": 12000000, "ig_followers": 5900000, "yt_subs": 4200000},
    {"name": "Sech",                "country": "PA", "genre": "reggaeton/pop",
     "top_tracks": ["Relación", "911", "Un Año", "Otro Trago", "Señorita"],
     "monthly_listeners": 9200000, "ig_followers": 4600000, "yt_subs": 3000000},
    {"name": "Mora",                "country": "PR", "genre": "trap/urbano",
     "top_tracks": ["La Nota", "Beso", "Por El Tubo", "Adicto", "Playa Del Inglés"],
     "monthly_listeners": 7500000, "ig_followers": 2800000, "yt_subs": 1900000},
    {"name": "Ovy On The Drums",    "country": "CO", "genre": "producción/urbano",
     "top_tracks": ["La Plena", "mi refe", "Bzrp Music Sessions", "Pepas", "ULALA"],
     "monthly_listeners": 18000000, "ig_followers": 3200000, "yt_subs": 2100000},
    {"name": "Arcángel",            "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["Métele al Perreo", "Por Eso Me Alejo", "Sexo Orden", "El Telefono"],
     "monthly_listeners": 8800000, "ig_followers": 7400000, "yt_subs": 3800000},
    {"name": "Camilo",              "country": "CO", "genre": "pop",
     "top_tracks": ["Vida de Rico", "Tutu", "Ropa Cara", "No Te Vayas", "TELEFONO"],
     "monthly_listeners": 22000000, "ig_followers": 16000000, "yt_subs": 8400000},
    {"name": "Sebastián Yatra",     "country": "CO", "genre": "pop latino",
     "top_tracks": ["Robarte un Beso", "Fresa", "VAGABUNDO", "Pareja del Año", "Tacones Rojos"],
     "monthly_listeners": 21000000, "ig_followers": 17000000, "yt_subs": 7200000},
    {"name": "Natanael Cano",       "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["Amor Tumbado", "CL4VES", "No Quiero Culparte", "Pa Mi Dota", "Encantadora"],
     "monthly_listeners": 13000000, "ig_followers": 5800000, "yt_subs": 6100000},
    {"name": "Luis R Conriquez",    "country": "MX", "genre": "corridos",
     "top_tracks": ["Jefe De Jefes", "La Maza", "El Que La Hace", "Solo Nosotros", "Lodo"],
     "monthly_listeners": 10000000, "ig_followers": 3200000, "yt_subs": 2700000},
    {"name": "Carin León",          "country": "MX", "genre": "banda/pop",
     "top_tracks": ["Según Quién", "Por Besarte Otro Rato", "Primera Cita", "Tóxico", "Llorando"],
     "monthly_listeners": 15000000, "ig_followers": 6300000, "yt_subs": 4800000},
    {"name": "Christian Nodal",     "country": "MX", "genre": "regional mexicano",
     "top_tracks": ["Botella tras Botella", "Ya No Somos Ni Seremos", "De Los Besos", "De Cuanto"],
     "monthly_listeners": 14000000, "ig_followers": 14000000, "yt_subs": 7900000},
    {"name": "Grupo Frontera",      "country": "MX", "genre": "norteño",
     "top_tracks": ["No Se Va", "Frío", "un x100to", "BESO", "Hey Mor"],
     "monthly_listeners": 12000000, "ig_followers": 4900000, "yt_subs": 3400000},
    {"name": "Gera MX",             "country": "MX", "genre": "rap/hip-hop",
     "top_tracks": ["Confianza", "Mamá", "Vuelve", "Frío Frío", "Primera Fila"],
     "monthly_listeners": 6800000, "ig_followers": 1900000, "yt_subs": 1400000},
    {"name": "MC Davo",             "country": "MX", "genre": "rap/hip-hop",
     "top_tracks": ["No Le Creo Nada", "Duerme", "Ando Bien", "Lloverá", "Pasos"],
     "monthly_listeners": 4200000, "ig_followers": 1100000, "yt_subs": 830000},
    {"name": "Yahritza Y Su Esencia", "country": "MX", "genre": "regional mexicano",
     "top_tracks": ["Obsessed", "La Perla", "Niña", "Amargura", "Que No Haya Nadie Más"],
     "monthly_listeners": 9400000, "ig_followers": 3600000, "yt_subs": 2800000},
    {"name": "Grupo Firme",         "country": "MX", "genre": "regional mexicano",
     "top_tracks": ["Ya Supérame", "El Toxico", "Yo Ya No Vuelvo Contigo",
                    "De Que Me Sirve", "El Beneficio De La Duda"],
     "monthly_listeners": 17000000, "ig_followers": 9100000, "yt_subs": 9800000},
    {"name": "Régulo Molina",       "country": "MX", "genre": "sierreño",
     "top_tracks": ["Canasteo", "El 25", "Morir Amando", "De Mil Amores"],
     "monthly_listeners": 5100000, "ig_followers": 1200000, "yt_subs": 910000},
    {"name": "Oscar Maydon",        "country": "MX", "genre": "corridos tumbados",
     "top_tracks": ["Canasteo", "Los Antrax", "El Problema", "Verde Escuro"],
     "monthly_listeners": 7800000, "ig_followers": 2000000, "yt_subs": 1500000},
    {"name": "W Sound",             "country": "CO", "genre": "producción/reggaeton",
     "top_tracks": ["La Plena - W Sound 05", "W Sound 04", "W Sound 03"],
     "monthly_listeners": 12000000, "ig_followers": 2700000, "yt_subs": 1900000},
    {"name": "PEDRO SAMPAIO",       "country": "BR", "genre": "funk/baile funk",
     "top_tracks": ["JETSKI", "PALCO", "NÃO PARA", "DOM DOM DOM", "GALOPA"],
     "monthly_listeners": 9500000, "ig_followers": 4800000, "yt_subs": 3600000},
    {"name": "Ñengo Flow",          "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["Trap King", "FOREVER TU GANTEL", "Real G", "Tiraera", "Sin Ropa"],
     "monthly_listeners": 6300000, "ig_followers": 3700000, "yt_subs": 2200000},
    {"name": "JC Reyes",            "country": "DO", "genre": "reggaeton/dembow",
     "top_tracks": ["LOQUITA", "MVLAN", "PA ROMPERLA", "COSA RICA", "Gata"],
     "monthly_listeners": 5400000, "ig_followers": 1600000, "yt_subs": 1000000},
    {"name": "YOVNGCHIMI",          "country": "DO", "genre": "dembow/reggaeton",
     "top_tracks": ["MVLAN", "200", "OK", "PISTOLA DE AGUA", "Corazón"],
     "monthly_listeners": 4700000, "ig_followers": 1400000, "yt_subs": 880000},
    {"name": "Dei V",               "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["$UELTA GATITA $UELTA", "Pa' Mí", "YHLQMDLG", "Sube", "Volaré"],
     "monthly_listeners": 8100000, "ig_followers": 2300000, "yt_subs": 1600000},
    {"name": "Aitana",              "country": "ES", "genre": "pop",
     "top_tracks": ["SUPERESTRELLA", "Mon Amour", "Formentera", "Lo Malo", "Berlín"],
     "monthly_listeners": 14000000, "ig_followers": 7800000, "yt_subs": 3900000},
    {"name": "Prince Royce",        "country": "US-DO", "genre": "bachata/pop",
     "top_tracks": ["Dardos", "Inclúyeme", "Stand By Me", "Incondicional", "Soy El Mismo"],
     "monthly_listeners": 11000000, "ig_followers": 14000000, "yt_subs": 5700000},
    {"name": "Cauty",               "country": "CO", "genre": "reggaeton/pop",
     "top_tracks": ["Oye Baby", "Necesito", "Patria", "Tu Eres", "Solo Mía"],
     "monthly_listeners": 5200000, "ig_followers": 1500000, "yt_subs": 950000},
    {"name": "WOS",                 "country": "AR", "genre": "rap/freestyle",
     "top_tracks": ["Arriba Todo", "Bicho Raro", "Hello Darkness", "Canguro", "En El Medio"],
     "monthly_listeners": 6700000, "ig_followers": 3100000, "yt_subs": 2400000},
    {"name": "El Alfa",             "country": "DO", "genre": "dembow",
     "top_tracks": ["PASTELE", "Tu Cuerpo", "La Mamá de la Mamá", "Suave", "El Tiguere"],
     "monthly_listeners": 8400000, "ig_followers": 6900000, "yt_subs": 4100000},
    {"name": "Lunay",               "country": "PR", "genre": "reggaeton",
     "top_tracks": ["Soltera", "Cuando Te Veo", "A Solas", "Fantasía", "Pa Mañana"],
     "monthly_listeners": 5800000, "ig_followers": 3400000, "yt_subs": 2100000},
    {"name": "Jay Wheeler",         "country": "PR", "genre": "R&B/pop",
     "top_tracks": ["Iris", "La Curiosidad", "Buenas Noches", "Platónico", "Sigues"],
     "monthly_listeners": 9200000, "ig_followers": 3800000, "yt_subs": 2500000},
    {"name": "Bryant Myers",        "country": "PR", "genre": "trap latino",
     "top_tracks": ["Gangsta", "Chambea", "Pasarme Por La Mente", "Esclava", "La Nota"],
     "monthly_listeners": 7100000, "ig_followers": 4200000, "yt_subs": 3100000},
    {"name": "Alex Rose",           "country": "VE", "genre": "reggaeton/pop",
     "top_tracks": ["Diosa", "Solo Pa' Ti", "Sensación del Bloque", "Turra", "Ahora No"],
     "monthly_listeners": 6900000, "ig_followers": 3600000, "yt_subs": 2400000},
    {"name": "Dalex",               "country": "PR", "genre": "reggaeton/pop",
     "top_tracks": ["Lolo", "Que Vamos a Hacer", "Antes", "Pa'ti", "Tumbao"],
     "monthly_listeners": 4800000, "ig_followers": 2100000, "yt_subs": 1400000},
    {"name": "Zion & Lennox",       "country": "PR", "genre": "reggaeton",
     "top_tracks": ["Yo Voy", "No Me Digas Que No", "Llegaste Tú", "Entra", "Pa Ya"],
     "monthly_listeners": 5500000, "ig_followers": 4400000, "yt_subs": 2900000},
    {"name": "Nicky Jam",           "country": "PR", "genre": "reggaeton",
     "top_tracks": ["X", "El Perdón", "Hasta el Amanecer", "Fenomenal", "Id"],
     "monthly_listeners": 13000000, "ig_followers": 18000000, "yt_subs": 8200000},
    {"name": "Don Omar",            "country": "PR", "genre": "reggaeton",
     "top_tracks": ["Danza Kuduro", "Taboo", "Virtual Diva", "Piensas En Mí", "Pobre Diabla"],
     "monthly_listeners": 9800000, "ig_followers": 8700000, "yt_subs": 5300000},
    {"name": "Chencho Corleone",    "country": "PR", "genre": "reggaeton/trap",
     "top_tracks": ["Me Porto Bonito", "Hawái", "El PN", "Safaera", "Una Noche en Medellín"],
     "monthly_listeners": 16000000, "ig_followers": 5900000, "yt_subs": 4400000},
    {"name": "Jhayco",              "country": "PR", "genre": "pop/R&B",
     "top_tracks": ["Pareja del Año", "Siga Moviéndose", "No Me Conoce", "Dime Cómo", "Dakiti"],
     "monthly_listeners": 14000000, "ig_followers": 5600000, "yt_subs": 3800000},
    {"name": "Bad Gyal",            "country": "ES", "genre": "dancehall/reggaeton",
     "top_tracks": ["Internationally", "Blin Blin", "Beso", "Zorra", "La Pausa"],
     "monthly_listeners": 8600000, "ig_followers": 3400000, "yt_subs": 2200000},
    {"name": "Residente",           "country": "PR", "genre": "hip-hop/rap",
     "top_tracks": ["Latinoamérica", "René", "Invisible", "This Is Not America", "A Nombre De"],
     "monthly_listeners": 6400000, "ig_followers": 3100000, "yt_subs": 3700000},
    {"name": "Kali Uchis",          "country": "US-CO", "genre": "R&B/pop",
     "top_tracks": ["telepatía", "fue mejor", "Otro Verano", "Adiós", "La Luz"],
     "monthly_listeners": 18000000, "ig_followers": 5700000, "yt_subs": 3300000},
    {"name": "Shakira",             "country": "CO", "genre": "pop/rock latino",
     "top_tracks": ["Bzrp Music Session Vol.53", "Waka Waka", "Loca", "La Bicicleta", "Hips Don't Lie"],
     "monthly_listeners": 36000000, "ig_followers": 86000000, "yt_subs": 16000000},
    {"name": "Daddy Yankee",        "country": "PR", "genre": "reggaeton",
     "top_tracks": ["Gasolina", "Con Calma", "Shaky Shaky", "Dura", "MBambola"],
     "monthly_listeners": 22000000, "ig_followers": 30000000, "yt_subs": 15000000},
    {"name": "Grupo Menos É Mais",  "country": "BR", "genre": "forró/axé",
     "top_tracks": ["P do Pecado - Ao Vivo", "Encaixa Aqui", "Não Tem Explicação", "Terremoto"],
     "monthly_listeners": 8900000, "ig_followers": 4200000, "yt_subs": 3100000},
    {"name": "Mc Jacaré",           "country": "BR", "genre": "funk",
     "top_tracks": ["Carnívoro", "Amo Minha Favela", "Gauchinha", "Posso Até Não Te Dar Flores"],
     "monthly_listeners": 7600000, "ig_followers": 3400000, "yt_subs": 2600000},
    {"name": "Panda",               "country": "BR", "genre": "sertanejo",
     "top_tracks": ["Eu Te Seguro - Ao Vivo", "Calcinha de Renda - Ao Vivo", "Minha Musa"],
     "monthly_listeners": 9200000, "ig_followers": 4600000, "yt_subs": 3800000},
    {"name": "Gusttavo Lima",       "country": "BR", "genre": "sertanejo",
     "top_tracks": ["Calcinha de Renda", "Bloqueado", "Homem de Verdade", "Balada"],
     "monthly_listeners": 11000000, "ig_followers": 18000000, "yt_subs": 9400000},
    {"name": "SIMONE MENDES",       "country": "BR", "genre": "sertanejo",
     "top_tracks": ["P do Pecado", "Erro Gostoso", "Dois Tristes", "Você Não Presta", "Amores"],
     "monthly_listeners": 10000000, "ig_followers": 14000000, "yt_subs": 6800000},
    {"name": "Nigga",               "country": "PA", "genre": "reggaeton",
     "top_tracks": ["Lento", "Me Tienes Loco", "Punto G", "Bésame", "Yo Daría"],
     "monthly_listeners": 4100000, "ig_followers": 2200000, "yt_subs": 1600000},
    {"name": "Lenny Tavárez",       "country": "PR", "genre": "reggaeton/pop",
     "top_tracks": ["Fantasía", "Pasarme por la Mente", "Dime Tú", "Tu Dueño", "Mia"],
     "monthly_listeners": 4600000, "ig_followers": 2100000, "yt_subs": 1500000},
    {"name": "Paulo Londra",        "country": "AR", "genre": "trap/pop",
     "top_tracks": ["Solo", "Nena Maldición", "Adan y Eva", "Sábalos", "Perfecto"],
     "monthly_listeners": 7800000, "ig_followers": 5600000, "yt_subs": 4200000},
    {"name": "Trueno",              "country": "AR", "genre": "hip-hop/pop",
     "top_tracks": ["DANCE CRIP", "TRANQUILINO", "Tú Me Miras", "Bien Bueno", "PANGEA"],
     "monthly_listeners": 5900000, "ig_followers": 2900000, "yt_subs": 2100000},
    {"name": "C. Tangana",          "country": "ES", "genre": "pop urbano",
     "top_tracks": ["Nunca Estoy", "Tú Me Dejaste de Querer", "Demasiadas Mujeres", "K SiNo"],
     "monthly_listeners": 8200000, "ig_followers": 3700000, "yt_subs": 2800000},
    {"name": "Duki",                "country": "AR", "genre": "trap/reggaeton",
     "top_tracks": ["Como Si No Importara", "Goteo", "Si Te Sentís Sola", "Rockstar", "Agrandao"],
     "monthly_listeners": 13000000, "ig_followers": 7800000, "yt_subs": 6500000},
    {"name": "María Becerra",       "country": "AR", "genre": "pop urbano",
     "top_tracks": ["AUTOMÁTICO", "CORAZÓN VACÍO", "Ojalá", "High", "Buenos Aires"],
     "monthly_listeners": 16000000, "ig_followers": 8900000, "yt_subs": 5300000},
    {"name": "TINI",                "country": "AR", "genre": "pop",
     "top_tracks": ["La Triple T", "El Último Romántico", "Bar", "MIÉNTEME", "Cupido"],
     "monthly_listeners": 17000000, "ig_followers": 14000000, "yt_subs": 7200000},
    {"name": "Maldy",               "country": "PR", "genre": "reggaeton",
     "top_tracks": ["La Última", "Me Gusta", "Volando", "De Rodillas", "No Lo Sabe"],
     "monthly_listeners": 3800000, "ig_followers": 1800000, "yt_subs": 1200000},
    {"name": "Dimelo Flow",         "country": "CO", "genre": "reggaeton/pop",
     "top_tracks": ["Tumbao", "Chiky Bomb", "Reggaetón", "Como Lo Hacemos", "Fría"],
     "monthly_listeners": 4300000, "ig_followers": 1900000, "yt_subs": 1400000},
    {"name": "Jhon Álex Castaño",   "country": "CO", "genre": "corrido colombiano",
     "top_tracks": ["La Patrona", "Dime", "Amor Mío", "Perdóname", "Te Quiero"],
     "monthly_listeners": 3600000, "ig_followers": 1100000, "yt_subs": 840000},
    {"name": "Chuyin",              "country": "MX", "genre": "sierreño",
     "top_tracks": ["PUES QUE LE HAGO ?", "La Sinverguenza", "Corrido al Jefe", "Soñé"],
     "monthly_listeners": 4500000, "ig_followers": 1200000, "yt_subs": 870000},
    {"name": "Angel Almaguer",      "country": "MX", "genre": "sierreño",
     "top_tracks": ["4x4", "Con Calma", "Amor Difícil", "El Rey del Norte"],
     "monthly_listeners": 3900000, "ig_followers": 1000000, "yt_subs": 710000},
    {"name": "Victor Mendivil",     "country": "MX", "genre": "sierreño",
     "top_tracks": ["2+2", "4x4", "Pase y Toque", "Carta Abierta", "En Las Buenas"],
     "monthly_listeners": 5200000, "ig_followers": 1400000, "yt_subs": 980000},
    {"name": "Corina Smith",        "country": "VE", "genre": "reggaeton/pop",
     "top_tracks": ["Solita", "Tumbao", "Amor Bonito", "Quiero Verte"],
     "monthly_listeners": 3400000, "ig_followers": 950000, "yt_subs": 650000},
    {"name": "Paloma Mami",         "country": "CL", "genre": "pop urbano",
     "top_tracks": ["Not Steady", "Ojos Verdes", "Feeling", "Amigos"],
     "monthly_listeners": 4800000, "ig_followers": 1600000, "yt_subs": 1100000},
]

# Deduplicate by name, cap at 100
seen = set()
ARTISTS = []
for a in ARTIST_REFERENCE:
    if a["name"] not in seen:
        seen.add(a["name"])
        ARTISTS.append(a)
ARTISTS = ARTISTS[:100]

# Artist tier helper
def get_tier(idx):
    if idx < 5:   return 1
    if idx < 20:  return 2
    if idx < 50:  return 3
    return 4

# Build live artist name → scraped data index (for chart integration)
live_artist_names = set()
for ter, rows in live_chart_data.items():
    for _, artist_name, _, _ in rows:
        live_artist_names.add(artist_name.lower())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — GENERATE artists.csv (100 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LABELS_BY_GENRE = {
    "corridos tumbados": "Universal Music Latin",
    "corridos": "Sony Music Latin",
    "sierreño": "Sony Music Latin",
    "banda": "Warner Latin",
    "banda/norteño": "Warner Latin",
    "norteño/sierreño": "Sony Music Latin",
    "norteño": "Sony Music Latin",
    "regional mexicano": "Universal Music Latin",
    "banda/pop": "Interscope Latin",
    "reggaeton": "Def Jam Latin",
    "reggaeton/trap": "Def Jam Latin",
    "reggaeton/pop latino": "Interscope Latin",
    "reggaeton/pop": "Sony Music Latin",
    "trap latino": "Def Jam Latin",
    "trap/rap": "Def Jam Latin",
    "trap/pop": "Universal Music Latin",
    "trap/reggaeton": "Universal Music Latin",
    "trap/electronic": "Universal Music Latin",
    "trap/flamenco urbano": "Sony Music Latin",
    "pop urbano": "Sony Music Latin",
    "pop": "Universal Music Latin",
    "pop latino": "Universal Music Latin",
    "pop/R&B": "Interscope Latin",
    "pop/rock latino": "Sony Music Latin",
    "bachata": "Sony Music Latin",
    "bachata/pop": "Universal Music Latin",
    "R&B/reggaeton": "Interscope Latin",
    "R&B/pop": "Interscope Latin",
    "flamenco urbano": "Sony Music Latin",
    "hip-hop/rap": "Def Jam Latin",
    "hip-hop/pop": "Universal Music Latin",
    "rap/hip-hop": "Def Jam Latin",
    "rap/freestyle": "Universal Music Latin",
    "producción/urbano": "Universal Music Latin",
    "producción/reggaeton": "Interscope Latin",
    "funk/baile funk": "Universal Music Latin",
    "funk": "Universal Music Latin",
    "sertanejo": "Universal Music Latin",
    "forró/axé": "Warner Latin",
    "dancehall/reggaeton": "Sony Music Latin",
    "dancehall/pop": "Interscope Latin",
    "urbano latino": "Universal Music Latin",
    "cumbia/pop": "Warner Latin",
    "cumbia": "Warner Latin",
    "dembow": "Def Jam Latin",
    "dembow/reggaeton": "Def Jam Latin",
    "reggaeton/dembow": "Def Jam Latin",
}

artists_rows = []
for i, a in enumerate(ARTISTS):
    artist_id = f"ART_{i+1:03d}"
    jitter = 1 + random.uniform(-0.02, 0.02)
    listeners = int(a["monthly_listeners"] * jitter)

    # Bump if artist appears in live chart data
    if a["name"].lower() in live_artist_names:
        bump = 1 + random.uniform(0.05, 0.15)
        listeners = int(listeners * bump)

    label = LABELS_BY_GENRE.get(a["genre"], "Sony Music Latin")
    artists_rows.append({
        "artist_id":                artist_id,
        "name":                     a["name"],
        "country":                  a["country"],
        "genre":                    a["genre"],
        "label":                    label,
        "spotify_monthly_listeners": listeners,
        "social_blade_followers":   int(a["ig_followers"] * (1 + random.uniform(-0.02, 0.02))),
        "youtube_subscribers":      int(a["yt_subs"]      * (1 + random.uniform(-0.02, 0.02))),
    })

df_artists = pd.DataFrame(artists_rows)
df_artists.to_csv(os.path.join(DATA_DIR, "artists.csv"), index=False)

# Build lookup maps
artist_id_map   = {row["name"]: row["artist_id"] for row in artists_rows}
artist_name_map = {row["artist_id"]: row["name"]  for row in artists_rows}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — GENERATE spotify_charts.csv (300 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TERRITORIES = ["MX", "CO", "AR", "BR", "ES", "CL", "PE", "US-Latin"]

STREAM_SCALE = {
    "MX": 1.00, "CO": 0.18, "AR": 0.25, "BR": 0.90,
    "ES": 0.22, "CL": 0.10, "PE": 0.09, "US-Latin": 0.15,
}

today = date.today()
weekly_dates = [today - timedelta(weeks=w) for w in range(4, -1, -1)]

def position_to_streams(pos, territory):
    base_pos1_mx = random.randint(1200000, 1500000)
    base_pos20_mx = random.randint(600000, 800000)
    # log interpolation
    import math
    if pos <= 1:
        streams_mx = base_pos1_mx
    elif pos >= 20:
        streams_mx = base_pos20_mx * (0.85 ** max(0, pos - 20))
    else:
        t = (pos - 1) / 19.0
        streams_mx = int(base_pos1_mx * (1 - t) + base_pos20_mx * t)
    return int(streams_mx * STREAM_SCALE.get(territory, 0.10))

# Artist primary territories
ARTIST_PRIMARY_TERRITORY = {}
for i, a in enumerate(ARTISTS):
    c = a["country"]
    if c == "MX":        ARTIST_PRIMARY_TERRITORY[i] = "MX"
    elif c in ("CO",):   ARTIST_PRIMARY_TERRITORY[i] = "CO"
    elif c == "AR":      ARTIST_PRIMARY_TERRITORY[i] = "AR"
    elif c == "BR":      ARTIST_PRIMARY_TERRITORY[i] = "BR"
    elif c == "ES":      ARTIST_PRIMARY_TERRITORY[i] = "ES"
    elif c in ("PR", "US-DO", "US-CO", "DO", "PA", "VE"): ARTIST_PRIMARY_TERRITORY[i] = "MX"
    else:                ARTIST_PRIMARY_TERRITORY[i] = "MX"

chart_rows = []

# For the most recent week, integrate live chart data
latest_date = weekly_dates[-1]

# Build live chart entries for the latest week
live_entries_added = set()

for territory, scraped_rows in live_chart_data.items():
    if territory not in TERRITORIES:
        continue
    for pos, scrape_artist, scrape_track, scrape_streams in scraped_rows:
        # Match to our artist list
        matched_id = None
        for art in artists_rows:
            if art["name"].lower() == scrape_artist.lower():
                matched_id = art["artist_id"]
                break
        if matched_id is None:
            # Use scraped artist directly as a bonus entry
            matched_id = f"LIVE_{re.sub(r'[^A-Z0-9]', '', scrape_artist.upper())[:8]}"
            matched_name = scrape_artist
        else:
            matched_name = artist_name_map[matched_id]

        key = (matched_id, territory, str(latest_date))
        if key in live_entries_added:
            continue
        live_entries_added.add(key)

        # Generate prior 4 weeks with ±2 drift
        for w_idx, chart_date in enumerate(weekly_dates):
            drift = random.randint(-2, 2) * (4 - w_idx)
            hist_pos = max(1, pos + drift)
            chart_rows.append({
                "date":           str(chart_date),
                "territory":      territory,
                "artist_id":      matched_id,
                "artist_name":    matched_name,
                "track_title":    scrape_track,
                "chart_position": hist_pos if w_idx < 4 else pos,
                "streams_estimate": scrape_streams if w_idx == 4 else position_to_streams(hist_pos, territory),
                "peak_position":  min(hist_pos, pos),
                "weeks_on_chart": w_idx + 1,
            })

# Fill remaining rows from hardcoded data
existing_count = len(chart_rows)
target = 300
needed = target - existing_count
if needed > 0:
    # Distribute across tiers and territories
    tier_territory_map = {
        1: TERRITORIES[:5],   # Top 5 in 5 territories
        2: TERRITORIES[:4],   # Next 15 in 4 territories
        3: TERRITORIES[:2],   # Rising in 2 territories
        4: TERRITORIES[:1],   # Sporadic in 1 territory
    }
    tier_positions = {1: (1, 10), 2: (5, 30), 3: (15, 60), 4: (40, 150)}

    chart_fill = []
    for i, a in enumerate(ARTISTS):
        tier = get_tier(i)
        artist_id = f"ART_{i+1:03d}"
        territories_for_artist = tier_territory_map[tier]
        pos_range = tier_positions[tier]
        tracks = a["top_tracks"]

        for territory in territories_for_artist:
            # Skip if already covered by live data
            covered = any(
                r["artist_id"] == artist_id and r["territory"] == territory
                for r in chart_rows
            )
            if covered:
                continue

            base_pos = random.randint(*pos_range)
            track = random.choice(tracks)
            for w_idx, chart_date in enumerate(weekly_dates):
                drift = random.randint(-3, 3)
                pos = max(1, base_pos + drift * (4 - w_idx))
                chart_fill.append({
                    "date":            str(chart_date),
                    "territory":       territory,
                    "artist_id":       artist_id,
                    "artist_name":     a["name"],
                    "track_title":     track,
                    "chart_position":  pos,
                    "streams_estimate": position_to_streams(pos, territory),
                    "peak_position":   max(1, base_pos - random.randint(0, 5)),
                    "weeks_on_chart":  random.randint(1, 12),
                })
                if len(chart_rows) + len(chart_fill) >= target:
                    break
            if len(chart_rows) + len(chart_fill) >= target:
                break
        if len(chart_rows) + len(chart_fill) >= target:
            break

    chart_rows.extend(chart_fill[:needed])

# Trim/pad to exactly 300
chart_rows = chart_rows[:300]
while len(chart_rows) < 300:
    # Pad with extra entries from tier 1
    a = ARTISTS[random.randint(0, 4)]
    i = ARTISTS.index(a)
    artist_id = f"ART_{i+1:03d}"
    territory = random.choice(TERRITORIES)
    track = random.choice(a["top_tracks"])
    pos = random.randint(1, 20)
    chart_rows.append({
        "date":            str(weekly_dates[-1]),
        "territory":       territory,
        "artist_id":       artist_id,
        "artist_name":     a["name"],
        "track_title":     track,
        "chart_position":  pos,
        "streams_estimate": position_to_streams(pos, territory),
        "peak_position":   max(1, pos - 2),
        "weeks_on_chart":  random.randint(4, 16),
    })

df_charts = pd.DataFrame(chart_rows)
df_charts.to_csv(os.path.join(DATA_DIR, "spotify_charts.csv"), index=False)

# Build set of territories per artist (from chart data)
artist_territories = {}
for r in chart_rows:
    aid = r["artist_id"]
    if aid.startswith("ART_"):
        artist_territories.setdefault(aid, set()).add(r["territory"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5 — GENERATE kworb_crosschart.csv (100 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLATFORMS = ["Spotify", "Apple Music", "Deezer", "Tidal", "Amazon Music"]
tier_platforms = {1: (4, 5), 2: (3, 4), 3: (2, 3), 4: (1, 2)}
tier_weeks     = {1: (8, 52), 2: (4, 20), 3: (1, 8), 4: (0, 3)}
tier_peak_pos  = {1: (1, 10), 2: (10, 40), 3: (30, 100), 4: (60, 200)}

crosschart_rows = []
for i, a in enumerate(ARTISTS):
    artist_id = f"ART_{i+1:03d}"
    tier = get_tier(i)
    n_platforms = random.randint(*tier_platforms[tier])
    weeks = random.randint(*tier_weeks[tier])
    peak  = random.randint(*tier_peak_pos[tier])
    terrs = list(artist_territories.get(artist_id, {a["country"]}))
    crosschart_rows.append({
        "date":                str(today),
        "artist_id":           artist_id,
        "artist_name":         a["name"],
        "platforms_charting":  ", ".join(random.sample(PLATFORMS, min(n_platforms, len(PLATFORMS)))),
        "peak_position_global": peak,
        "weeks_on_chart":      weeks,
        "territories_charting": ", ".join(sorted(terrs)),
    })

pd.DataFrame(crosschart_rows).to_csv(os.path.join(DATA_DIR, "kworb_crosschart.csv"), index=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6 — GENERATE social_blade_growth.csv (200 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tier_growth = {1: (3.0, 8.0), 2: (2.0, 6.0), 3: (1.0, 4.0), 4: (0.2, 2.0)}

social_rows = []
for i, a in enumerate(ARTISTS):
    artist_id = f"ART_{i+1:03d}"
    tier = get_tier(i)
    g_range = tier_growth[tier]

    for platform, base_followers in [
        ("Instagram", a["ig_followers"]),
        ("YouTube",   a["yt_subs"]),
    ]:
        growth_pct = round(random.uniform(*g_range), 2)
        followers_start = int(base_followers * 0.97)
        followers_end   = int(followers_start * (1 + growth_pct / 100))

        if platform == "Instagram":
            # Inverse relationship with size
            if base_followers > 10_000_000:
                eng = round(random.uniform(2.0, 4.0), 2)
            elif base_followers > 3_000_000:
                eng = round(random.uniform(3.0, 6.0), 2)
            else:
                eng = round(random.uniform(4.5, 8.0), 2)
        else:  # YouTube
            eng = round(random.uniform(3.0, 10.0), 2)

        social_rows.append({
            "date":             str(today),
            "artist_id":        artist_id,
            "artist_name":      a["name"],
            "platform":         platform,
            "followers_start":  followers_start,
            "followers_end":    followers_end,
            "growth_pct":       growth_pct,
            "engagement_rate":  eng,
        })

pd.DataFrame(social_rows).to_csv(os.path.join(DATA_DIR, "social_blade_growth.csv"), index=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7 — GENERATE media_mentions.csv (150 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCES = [
    "Billboard Latin", "MBW (Music Business Worldwide)", "Hypebot",
    "Rolling Stone en Español", "NME Latin", "Variety Latin",
    "Latin Beat Magazine", "El País Cultura", "Reforma Cultura",
    "La Nación Espectáculos",
]

HEADLINE_TEMPLATES = [
    "{artist} dominates {territory} charts with '{track}'",
    "{artist} announces stadium tour across Latin America",
    "'{track}' reaches {streams}M streams on Spotify",
    "{artist} partners with {brand} for regional campaign",
    "{artist} named in top 10 most-streamed artists in {territory}",
    "{artist} collaborates with {collab} on upcoming project",
    "{artist} speaks on youth identity and authentic storytelling",
    "{artist} breaks streaming record in {territory}",
    "{artist} signs multi-year deal with major festival circuit",
    "{artist} visual for '{track}' crosses 100M YouTube views",
]

CULTURAL_TOPICS_POOL = [
    "youth", "authenticity", "celebration", "empowerment", "urban_identity",
    "spiritual", "fashion", "sport", "tech", "family", "regional_pride",
    "nostalgia", "political", "social_justice", "luxury", "street_culture",
]

BRANDS_FOR_MENTIONS = [
    "Nike", "Pepsi", "Red Bull", "Samsung", "Spotify", "TikTok", "Apple Music"
]

tier_mention_count = {1: (6, 10), 2: (2, 5), 3: (1, 2), 4: (0, 1)}

all_artist_names = [a["name"] for a in ARTISTS]
mention_rows = []

for i, a in enumerate(ARTISTS):
    artist_id = f"ART_{i+1:03d}"
    tier = get_tier(i)
    n_mentions_range = tier_mention_count[tier]
    n_mentions = random.randint(*n_mentions_range)
    if n_mentions == 0:
        continue

    for _ in range(n_mentions):
        if len(mention_rows) >= 150:
            break
        track = random.choice(a["top_tracks"])
        territory = random.choice(TERRITORIES)
        streams_m = round(random.uniform(10, 500), 0)
        collab = random.choice([x for x in all_artist_names if x != a["name"]])
        brand = random.choice(BRANDS_FOR_MENTIONS)

        tmpl = random.choice(HEADLINE_TEMPLATES)
        headline = tmpl.format(
            artist=a["name"], track=track, territory=territory,
            streams=int(streams_m), brand=brand, collab=collab
        )

        # Sentiment
        r = random.random()
        if tier == 1 and r < 0.08:
            sentiment = round(random.uniform(0.10, 0.39), 3)  # negative/controversy
        elif r < 0.12:
            sentiment = round(random.uniform(0.40, 0.65), 3)  # neutral
        else:
            sentiment = round(random.uniform(0.65, 0.95), 3)  # positive

        n_topics = random.randint(2, 4)
        topics = ", ".join(random.sample(CULTURAL_TOPICS_POOL, n_topics))

        days_ago = random.randint(0, 90)
        mention_date = today - timedelta(days=days_ago)

        mention_rows.append({
            "date":             str(mention_date),
            "artist_id":        artist_id,
            "artist_name":      a["name"],
            "source":           random.choice(SOURCES),
            "headline":         headline,
            "sentiment_score":  sentiment,
            "cultural_topics":  topics,
        })
    if len(mention_rows) >= 150:
        break

pd.DataFrame(mention_rows[:150]).to_csv(os.path.join(DATA_DIR, "media_mentions.csv"), index=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 8 — GENERATE audience_segments.csv (200 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TERRITORY_WEIGHT = {
    "MX": 0.35, "CO": 0.18, "AR": 0.15, "BR": 0.12,
    "ES": 0.10, "PE": 0.05, "CL": 0.08, "US-Latin": 0.12,
}

AGE_RANGES_BY_GENRE = {
    "corridos tumbados": "18-24",
    "corridos": "18-24",
    "trap latino": "18-24",
    "trap/rap": "18-24",
    "reggaeton/trap": "18-24",
    "dembow/reggaeton": "18-24",
    "reggaeton": "18-34",
    "reggaeton/pop": "18-34",
    "reggaeton/pop latino": "18-34",
    "pop urbano": "18-34",
    "pop": "25-34",
    "pop latino": "25-34",
    "bachata": "25-34",
    "bachata/pop": "25-34",
    "banda": "25-44",
    "banda/norteño": "25-44",
    "banda/pop": "25-44",
    "norteño/sierreño": "25-44",
    "sierreño": "25-44",
    "regional mexicano": "25-44",
    "cumbia": "25-44",
    "cumbia/pop": "25-44",
    "sertanejo": "25-44",
    "forró/axé": "25-44",
}

def get_age_range(genre):
    return AGE_RANGES_BY_GENRE.get(genre, "25-34")

GENDER_BY_GENRE = {
    "corridos tumbados": (40, 60),
    "corridos": (35, 65),
    "reggaeton": (55, 45),
    "pop": (60, 40),
    "pop urbano": (55, 45),
    "bachata": (52, 48),
    "banda": (45, 55),
    "sierreño": (42, 58),
    "regional mexicano": (45, 55),
    "trap latino": (42, 58),
    "sertanejo": (52, 48),
}

def get_gender_split(genre):
    for key, (f, m) in GENDER_BY_GENRE.items():
        if key in genre:
            jitter_f = f + random.randint(-5, 5)
            jitter_f = max(30, min(70, jitter_f))
            return jitter_f, 100 - jitter_f
    return 50, 50

PLATFORM_BY_GENRE = {
    "corridos tumbados": "YouTube",
    "corridos": "YouTube",
    "sierreño": "YouTube",
    "trap latino": "Spotify",
    "reggaeton": "Spotify",
    "pop": "Spotify",
    "sertanejo": "YouTube",
    "funk": "YouTube",
}

def get_platform(genre):
    for key, plat in PLATFORM_BY_GENRE.items():
        if key in genre:
            return plat
    return random.choice(["Spotify", "YouTube", "TikTok"])

SOURCE_BY_TIER = {1: ["first-party", "proxy"], 2: ["first-party", "proxy"], 3: ["proxy"], 4: ["proxy"]}
SOURCE_WEIGHTS  = {1: [0.5, 0.5], 2: [0.2, 0.8], 3: [0.0, 1.0], 4: [0.0, 1.0]}

segment_rows = []
for i, a in enumerate(ARTISTS):
    artist_id = f"ART_{i+1:03d}"
    tier = get_tier(i)
    listeners = artists_rows[i]["spotify_monthly_listeners"]

    # Primary and secondary markets
    primary_country = a["country"]
    if primary_country in TERRITORY_WEIGHT:
        primary_market = primary_country
    elif primary_country in ("PR", "DO", "US-DO", "US-CO", "PA", "VE"):
        primary_market = "US-Latin"
    else:
        primary_market = "MX"

    secondary_pool = [t for t in list(TERRITORY_WEIGHT.keys()) if t != primary_market]
    secondary_market = random.choice(secondary_pool)

    for j, market in enumerate([primary_market, secondary_market]):
        weight = TERRITORY_WEIGHT.get(market, 0.10)
        reach = int(listeners * weight)

        # Source type
        source_types = SOURCE_BY_TIER[tier]
        weights = SOURCE_WEIGHTS[tier]
        if tier <= 2:
            source_type = random.choices(source_types, weights=weights)[0]
        else:
            source_type = "proxy"

        age_range = get_age_range(a["genre"])
        gender_f, gender_m = get_gender_split(a["genre"])
        platform = get_platform(a["genre"])

        segment_name = f"{'Core' if j == 0 else 'Emerging'} {a['genre'].split('/')[0].title()} Fans"

        segment_rows.append({
            "artist_id":        artist_id,
            "artist_name":      a["name"],
            "market":           market,
            "segment_name":     segment_name,
            "age_range":        age_range,
            "gender_split_f":   gender_f,
            "gender_split_m":   gender_m,
            "platform_primary": platform,
            "estimated_reach":  reach,
            "source_type":      source_type,
        })

pd.DataFrame(segment_rows[:200]).to_csv(os.path.join(DATA_DIR, "audience_segments.csv"), index=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 9 — GENERATE client_campaigns.csv (50 rows)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRAND_CATEGORIES = {
    "Beverages": [
        "Red Bull", "Corona", "Tecate", "Pepsi México", "Modelo",
        "Sprite Latam", "Monster Energy Latin", "Bacardi", "Gatorade Latam",
        "Coca-Cola Latam",
    ],
    "Fashion": [
        "Zara Latam", "Nike Latin America", "Adidas Latam",
        "H&M México", "Pull&Bear España", "SHEIN Latam",
        "Levi's Latam", "Converse Latam", "Puma Latam", "Tommy Hilfiger MX",
    ],
    "Tech": [
        "Claro Música", "Telcel", "Movistar Latam", "Apple Music Latam",
        "Samsung Latam", "TikTok for Business", "YouTube Music",
        "Spotify Latinoamérica", "DIRECTV Sports", "Xbox Latam",
    ],
    "Sport": [
        "Nike Training Latam", "Adidas Football", "Liga MX",
        "CONMEBOL", "Puma Sport", "Under Armour Latam",
        "New Balance Latam", "Reebok Latam", "ESPN Latam", "Decathlon MX",
    ],
    "Finance": [
        "Nubank Brasil", "Mercado Pago", "BBVA México",
        "Rappi Pay", "Clip MX", "Kueski", "Kavak", "Oxxo Pay",
        "Scotiabank Latam", "Citibanamex",
    ],
}

# ROI ranges by category and tier
ROI_RANGES = {
    "Beverages": {1: (2.8, 4.2), 2: (1.8, 3.0)},
    "Fashion":   {1: (2.5, 4.0), 2: (1.7, 2.8)},
    "Tech":      {1: (1.8, 2.5), 2: (1.4, 2.2)},
    "Sport":     {1: (2.0, 3.5), 2: (1.5, 2.5)},
    "Finance":   {1: (1.5, 2.2), 2: (1.2, 1.9)},
}

campaign_rows = []
# Tier 1 + Tier 2 artists (indices 0-19)
eligible_artists = [(i, a) for i, a in enumerate(ARTISTS) if i < 20]
categories = list(BRAND_CATEGORIES.keys())

campaign_id = 1
# 10 campaigns per category = 50 total
for category in categories:
    brands = BRAND_CATEGORIES[category]
    for k in range(10):
        brand_name = brands[k % len(brands)]
        i, a = eligible_artists[(campaign_id - 1) % len(eligible_artists)]
        artist_id = f"ART_{i+1:03d}"
        tier = get_tier(i)
        territory = random.choice(TERRITORIES)
        budget = random.randint(80, 500) * 1000

        roi_tier = min(tier, 2)
        roi_low, roi_high = ROI_RANGES[category][roi_tier]
        roi = round(random.uniform(roi_low, roi_high), 3)
        revenue_uplift = int(budget * roi)
        conversions = int(revenue_uplift / random.uniform(25, 80))
        reach_actual = int(artists_rows[i]["spotify_monthly_listeners"]
                           * TERRITORY_WEIGHT.get(territory, 0.10)
                           * random.uniform(0.6, 1.2))
        brand_lift_pts = round(random.uniform(3, 22), 1)

        days_ago_start = random.randint(60, 730)
        campaign_start = today - timedelta(days=days_ago_start)
        duration_weeks = random.randint(8, 16)
        campaign_end = campaign_start + timedelta(weeks=duration_weeks)

        campaign_rows.append({
            "campaign_id":           f"CAMP_{campaign_id:03d}",
            "brand_name":            brand_name,
            "brand_category":        category,
            "artist_id":             artist_id,
            "artist_name":           a["name"],
            "territory":             territory,
            "budget_usd":            budget,
            "actual_revenue_uplift": revenue_uplift,
            "conversions":           conversions,
            "reach_actual":          reach_actual,
            "brand_lift_pts":        brand_lift_pts,
            "campaign_start":        str(campaign_start),
            "campaign_end":          str(campaign_end),
        })
        campaign_id += 1

pd.DataFrame(campaign_rows).to_csv(os.path.join(DATA_DIR, "client_campaigns.csv"), index=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10 — PRINT SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

files = {
    "artists.csv":             "artists.csv",
    "spotify_charts.csv":      "spotify_charts.csv",
    "kworb_crosschart.csv":    "kworb_crosschart.csv",
    "social_blade_growth.csv": "social_blade_growth.csv",
    "media_mentions.csv":      "media_mentions.csv",
    "audience_segments.csv":   "audience_segments.csv",
    "client_campaigns.csv":    "client_campaigns.csv",
}

live_used = len(live_chart_data) > 0
n_live_territories = len(live_chart_data)

top5 = sorted(artists_rows, key=lambda x: x["spotify_monthly_listeners"], reverse=True)[:5]
start_date = str(weekly_dates[0])
end_date = str(weekly_dates[-1])

print("\n" + "━" * 51)
print("  CDX — CSIE Data Generation Complete")
print("━" * 51)
for fname, path in files.items():
    full_path = os.path.join(DATA_DIR, path)
    df_tmp = pd.read_csv(full_path)
    print(f"  {fname:<28} {len(df_tmp):>4} rows")
print()
print(f"  Live Kworb data used: {'YES' if live_used else 'NO'} ({n_live_territories} territories scraped)")
print("  Top 5 artists by listeners:")
for j, art in enumerate(top5, 1):
    ml = art['spotify_monthly_listeners']
    print(f"    {j}. {art['name']:<28} {ml/1_000_000:.1f}M monthly")
print(f"  Territories: {', '.join(TERRITORIES)}")
print(f"  Date range: {start_date} to {end_date}")
print("  Seed: 42")
print("━" * 51)
