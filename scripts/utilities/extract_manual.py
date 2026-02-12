from pypdf import PdfReader
from pathlib import Path

def extract_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    pdf_path = repo_root / "assets" / "reference" / "Manuel de Vente d'Élite _ Stratégies Avancées pour Professionnels Chevronnés.pdf"
    print(f"Extraction for: {pdf_path}")
    content = extract_text(str(pdf_path))
    if not content.strip():
        print("WARNING: Extracted text is empty. PDF might be image-based or protected.")
    else:
        print(content)
