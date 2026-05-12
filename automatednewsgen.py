#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import uuid
import time
import json
from datetime import datetime
import ollama
from ebooklib import epub
from PIL import Image, ImageDraw, ImageFont
import textwrap
from pygooglenews import GoogleNews

# ========== CONFIGURATION ==========
MODEL_NAME = "llama3.2:latest"
FONT_PATH = "fonts/cnr.otf"            # Votre police OTF
OUTPUT_DIR = "rendu"
AUTHOR_NAME = "Astin Java"
LANG = 'fr'
COUNTRY = 'FR'
# ===================================

def ensure_output_dir():
    abs_path = os.path.abspath(OUTPUT_DIR)
    os.makedirs(abs_path, exist_ok=True)
    print(f"📁 Dossier de sortie : {abs_path}")
    return abs_path

def fetch_news(query=None, max_articles=5):
    """Récupère les actualités depuis Google News."""
    gn = GoogleNews(lang=LANG, country=COUNTRY)
    if query:
        print(f"🔍 Recherche d'actualités sur : {query}")
        search = gn.search(query)
        entries = search['entries']
    else:
        print("📰 Récupération des top actualités du jour...")
        top = gn.top_news()
        entries = top['entries']
    articles = []
    for item in entries[:max_articles]:
        articles.append({
            "title": item.title,
            "link": item.link,
            "published": item.published,
            "summary": item.summary if hasattr(item, 'summary') else ""
        })
    print(f"✅ {len(articles)} articles récupérés.")
    return articles

def generate_book_structure(articles):
    """Demande à l'IA de générer un titre de livre et un plan chapitres à partir des articles."""
    articles_text = "\n\n".join([f"Titre: {a['title']}\nRésumé: {a['summary']}" for a in articles])
    prompt = f"""
Voici une sélection d'actualités récentes :
{articles_text}

À partir de ces informations, propose un titre de livre pertinent (environ 5-10 mots) et une structure de chapitres (5 chapitres max). Chaque chapitre doit avoir un titre évocateur. Le livre est de type essai ou analyse d'actualité.

Retourne au format JSON strict :
{{"title": "titre du livre", "chapters": ["Titre chapitre 1", "Titre chapitre 2", ...]}}
Ne mets rien d'autre que ce JSON.
"""
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        content = resp['message']['content']
        # Nettoyer la réponse (parfois l'IA ajoute du texte autour)
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        data = json.loads(content.strip())
        title = data.get('title', 'Actualités du jour')
        chapters = data.get('chapters', [f"Chapitre {i+1}" for i in range(len(articles))])
        return title, chapters
    except Exception as e:
        print(f"⚠️ Erreur génération structure : {e}")
        return "Actualités récentes", [f"Analyse {i+1}" for i in range(len(articles))]

def generate_chapter_content(chapter_title, articles, chapter_num, total_chapters):
    """Génère le contenu d'un chapitre à partir des articles."""
    articles_summary = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"""
Tu écris un livre d'actualité. Chapitre {chapter_num}/{total_chapters} : '{chapter_title}'.

Actualités disponibles :
{articles_summary}

Rédige un chapitre de 600-1000 mots, style essai / analyse journalistique. Structure : commence par un sous-titre ##, puis des paragraphes.
Utilise les faits des articles, tu peux les synthétiser. Ajoute une réflexion personnelle (neutre, factuelle). 
Ne mentionne pas explicitement les dates de publication. Écris uniquement le contenu.
"""
    print(f"  ✍️ Génération chapitre {chapter_num} : {chapter_title}")
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        return resp['message']['content']
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return f"## {chapter_title}\n\nContenu non généré.\n\n"

def generate_back_cover_text(book_title, articles):
    """Génère la quatrième de couverture."""
    prompt = f"""
Rédige un texte de quatrième de couverture (150-200 mots) pour le livre "{book_title}", basé sur les actualités suivantes :
{', '.join([a['title'] for a in articles])}
Le ton doit être engageant, donner envie de lire l'analyse.
"""
    try:
        resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        return resp['message']['content']
    except:
        return f"Plongez dans l'analyse des événements qui façonnent notre monde. {book_title} décrypte l'actualité avec profondeur. Signé {AUTHOR_NAME}."

def create_cover_image(book_title, output_path):
    """Crée une image de couverture avec le titre et l'auteur."""
    abs_path = os.path.abspath(output_path)
    parent = os.path.dirname(abs_path)
    os.makedirs(parent, exist_ok=True)
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='#1e3c5c')  # Bleu nuit
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 55)
        author_font = ImageFont.truetype("arial.ttf", 40)
    except:
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    # Décoration : lignes et cercles
    for _ in range(80):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(1, 3)
        draw.ellipse([x-r, y-r, x+r, y+r], fill='#ffb347')
    wrapped = textwrap.wrap(book_title, width=25)
    y = height // 2 - 50
    for line in wrapped:
        bbox = draw.textbbox((0,0), line, font=title_font)
        w = bbox[2] - bbox[0]
        draw.text((width//2 - w//2, y), line, fill='white', font=title_font)
        y += 70
    author_text = f"par {AUTHOR_NAME}"
    bbox = draw.textbbox((0,0), author_text, font=author_font)
    w = bbox[2] - bbox[0]
    draw.text((width//2 - w//2, height - 130), author_text, fill='#ffb347', font=author_font)
    img.save(abs_path)
    print(f"🖌️ Couverture créée : {abs_path}")
    return abs_path

def create_epub(book_title, chapters_data, back_text, cover_path, font_path):
    print("   - Création du livre EPUB...")
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(book_title)
    book.set_language('fr')
    book.add_author(AUTHOR_NAME)
    book.add_metadata('DC', 'date', datetime.now().isoformat())
    
    # Couverture
    if os.path.exists(cover_path):
        with open(cover_path, 'rb') as f:
            book.set_cover("cover.jpg", f.read())
        print("   - Couverture ajoutée.")
    else:
        print("   ⚠️ Couverture manquante.")
    
    # Police
    if os.path.exists(font_path):
        with open(font_path, 'rb') as f:
            font_item = epub.EpubItem(f'fonts/{os.path.basename(font_path)}',
                                      media_type='application/vnd.ms-opentype',
                                      content=f.read())
            book.add_item(font_item)
        print("   - Police intégrée.")
    else:
        print(f"   ⚠️ Police {font_path} introuvable.")
    
    # CSS
    css = f'''
    @font-face {{ font-family: "CustomFont"; src: url(fonts/{os.path.basename(font_path)}) format("opentype"); }}
    body {{ font-family: "CustomFont", serif; margin: 5%; text-align: justify; }}
    h1 {{ text-align: center; margin-top: 20%; }}
    h2 {{ margin-top: 1.5em; }}
    '''
    book.add_item(epub.EpubItem('style/main.css', media_type='text/css', content=css))
    
    # Pages
    title_page = epub.EpubHtml('Titre', 'title_page.xhtml', lang='fr')
    title_page.content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body><h1>{book_title}</h1><p style="text-align:center;">par {AUTHOR_NAME}</p></body></html>'
    book.add_item(title_page)
    
    copyright_page = epub.EpubHtml('Copyright', 'copyright.xhtml', lang='fr')
    copyright_page.content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body><div class="copyright"><p>© {datetime.now().year} {AUTHOR_NAME}</p><p>Généré par IA à partir d\'actualités.</p><p>{datetime.now().strftime("%d/%m/%Y")}</p></div></body></html>'
    book.add_item(copyright_page)
    
    spine = ['nav', title_page, copyright_page]
    toc = []
    
    # Chapitres
    print(f"   - Ajout de {len(chapters_data)} chapitres...")
    for i, (title, content) in enumerate(chapters_data, 1):
        if not content or len(content.strip()) < 50:
            print(f"   ⚠️ Chapitre {i} '{title}' a un contenu très court ou vide.")
        chap = epub.EpubHtml(title, f'chap_{i:02d}.xhtml', lang='fr')
        html_body = content.replace('## ', '<h2>').replace('\n\n', '</p><p>')
        if not html_body.startswith('<h2>'):
            html_body = f'<h2>{title}</h2><p>' + html_body
        html_body += '</p>'
        chap.content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body>{html_body}</body></html>'
        book.add_item(chap)
        spine.append(chap)
        toc.append(chap)
    
    # Quatrième couverture
    back_page = epub.EpubHtml('Quatrième de couverture', 'backcover.xhtml', lang='fr')
    back_page.content = f'<html><head><link rel="stylesheet" href="style/main.css"/></head><body><div class="backcover"><h2>À propos</h2><p>{back_text.replace(chr(10), "</p><p>")}</p><p>— {AUTHOR_NAME}</p></div></body></html>'
    book.add_item(back_page)
    spine.append(back_page)
    toc.append(back_page)
    
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine
    
    # Sauvegarde
    epub_path = os.path.join(OUTPUT_DIR, f"{book_title}.epub")
    try:
        epub.write_epub(epub_path, book, {})
        print(f"   ✅ Fichier écrit : {epub_path} ({os.path.getsize(epub_path)} octets)")
    except Exception as e:
        print(f"   ❌ Erreur d'écriture EPUB : {e}")
        raise
    return epub_path

def main():
    print("=" * 60)
    print("📰 Générateur automatique de livre à partir des actualités")
    print("=" * 60)
    ensure_output_dir()
    
    # Choix : top stories ou recherche par mot-clé
    choice = input("Voulez-vous (1) les top actualités ou (2) rechercher un mot-clé ? (1/2) : ").strip()
    if choice == '2':
        query = input("Mot-clé à rechercher : ").strip()
        if not query:
            print("Mot-clé invalide, utilisation des top actualités.")
            articles = fetch_news(max_articles=6)
        else:
            articles = fetch_news(query=query, max_articles=6)
    else:
        articles = fetch_news(max_articles=6)
    
    if not articles:
        print("Aucun article trouvé. Abandon.")
        sys.exit(1)
    
    print("\n📚 Génération de la structure du livre...")
    book_title, chapter_titles = generate_book_structure(articles)
    # On s'assure que le nombre de chapitres n'excède pas 6 (ou égal au nombre d'articles)
    if len(chapter_titles) > len(articles):
        chapter_titles = chapter_titles[:len(articles)]
    if len(chapter_titles) < 2:
        chapter_titles = [f"Chapitre {i+1}" for i in range(len(articles))]
    
    print(f"📖 Titre du livre : {book_title}")
    print(f"📑 Chapitres prévus : {chapter_titles}")
    
    chapters_data = []
    print("\n📝 Génération des chapitres (peut être long)...")
    for idx, chap_title in enumerate(chapter_titles, 1):
        content = generate_chapter_content(chap_title, articles, idx, len(chapter_titles))
        chapters_data.append((chap_title, content))
        time.sleep(1)
    
    print("\n📖 Génération de la quatrième de couverture...")
    back_text = generate_back_cover_text(book_title, articles)
    
    cover_path = os.path.join(OUTPUT_DIR, "temp_cover.jpg")
    print("\n🎨 Création de la couverture...")
    create_cover_image(book_title, cover_path)
    
    print("\n📚 Assemblage de l'EPUB...")
    epub_file = create_epub(book_title, chapters_data, back_text, cover_path, FONT_PATH)
    
    print(f"\n✨ Terminé ! Le livre '{book_title}' a été généré.")
    print(f"   Fichier : {epub_file}")

if __name__ == "__main__":
    try:
        ollama.list()
    except Exception as e:
        print("❌ Ollama non accessible. Assurez-vous qu'il tourne (commande 'ollama serve').")
        sys.exit(1)
    main()