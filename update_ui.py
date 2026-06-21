import os
import re

def update_ui_aesthetic():
    ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    html_files = [f for f in os.listdir(ui_dir) if f.endswith(".html")]
    
    radix_root = """:root {
            /* Radix UI Dark Theme Palette (Iris/Slate base) */
            --bg-primary: #111113;
            --bg-secondary: #18181b;
            --bg-card: rgba(24, 24, 27, 0.7);
            --accent: #5a5edb; /* Radix Iris */
            --accent-green: #30a46c; /* Radix Grass */
            --accent-yellow: #f5d90a; /* Radix Yellow */
            --accent-red: #e5484d; /* Radix Ruby */
            --accent-purple: #8e4ec6; /* Radix Plum */
            --text-primary: #ededef;
            --text-muted: #a09fa6;
            --border: #27272a;
            --glass-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            --glass-border: 1px solid rgba(255, 255, 255, 0.05);
        }"""

    font_import = """<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>"""

    for html_file in html_files:
        filepath = os.path.join(ui_dir, html_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace root CSS variables
        if ":root {" in content:
            # Simple regex to replace the root block
            content = re.sub(r':root\s*\{[^}]+\}', radix_root, content, flags=re.MULTILINE|re.DOTALL)
            
        # Replace font family
        content = re.sub(r'font-family:\s*[^;]+;', "font-family: 'Inter', system-ui, -apple-system, sans-serif;", content)
        
        # Inject Google Fonts if not present
        if "fonts.googleapis.com" not in content and "<style>" in content:
            content = content.replace("<style>", font_import, 1)
            
        # Update specific glassmorphism styling
        if "border-right: 1px solid var(--border);" in content:
            content = content.replace("border-right: 1px solid var(--border);", "border-right: var(--glass-border); box-shadow: var(--glass-shadow);")
            
        # Write back
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Successfully injected Radix aesthetic into all HTML files!")

if __name__ == "__main__":
    update_ui_aesthetic()
