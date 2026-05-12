Voici un README :

---

### Copiez ce contenu :

```markdown
# Book Generator - Générateur de livres avec Ollama

Un script Python qui utilise l'API d'Ollama pour générer des livres entiers à partir d'un simple thème et d'une description.

## Fonctionnalités

- Génération d'un plan de livre structuré en chapitres
- Rédaction automatique de chaque chapitre via un modèle de langage local
- Assemblage des chapitres en un fichier EPUB final

## Prérequis

- Python 3.x
- [Ollama](https://ollama.com) installé sur votre machine
- Au moins un modèle de langage téléchargé dans Ollama (ex: `llama3`, `mistral`, `gemma`)

## Installation

1. Clonez ce repository :
   ```bash
   git clone git@github.com:UpperGab/book-generator-ollama.git
   cd book-generator-ollama
   ```

2. Lancez le script :
   ```bash
   python script.py
   ```

## Utilisation

1. Lancez le script
2. Entrez un thème (ex: "Les voitures de sport")
3. Entrez une description (ex: "Un guide complet sur les voitures de sport les plus rapides du monde")
4. Le script dialogue avec Ollama pour générer un plan, puis rédige chaque chapitre
5. Retrouvez le fichier EPUB final dans le dossier de sortie

## Exemples de livres générés

- Les voitures de sport
- La magie blanche
- Rick Tombeur

## Technologies utilisées

- **Python** - Langage principal
- **Ollama** - Moteur d'inférence local pour modèles de langage (LLM)
- **EPUB** - Format de sortie des livres

## Auteur

**Gabriel Aubessard**
- BTS Systèmes Numériques option Électronique et Communications
- En recherche de formation en développement logiciel
- [GitHub](https://github.com/UpperGab)
```

---

### Pour l'ajouter à votre repository :

1. Créez un fichier `README.md` dans `C:\temp\book` et collez le contenu ci-dessus
2. Puis dans PowerShell :

```bash
cd C:\temp\book
```
```bash
git add README.md
```
```bash
git commit -m "Ajout du README"
```
```bash
git push
```
