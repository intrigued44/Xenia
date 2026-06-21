import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        except_indent = match.group(1)
        pass_indent = match.group(2)
        return f"{except_indent}except Exception as e:\n{pass_indent}import logging\n{pass_indent}logging.error(f\"context: {{e}}\", exc_info=True)"

    # Match multiline: except...:\n  pass
    pattern = re.compile(r'(^[ \t]*)except[^:]*:\n([ \t]+)pass', re.MULTILINE)
    new_content = pattern.sub(replacer, content)

    def replacer_inline(match):
        except_indent = match.group(1)
        return f"{except_indent}except Exception as e: import logging; logging.error(f\"context: {{e}}\", exc_info=True)"

    # Match inline: except...: pass
    pattern_inline = re.compile(r'(^[ \t]*)except[^:]*:\s*pass', re.MULTILINE)
    new_content = pattern_inline.sub(replacer_inline, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('.'):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') and file != 'fix_except.py':
            process_file(os.path.join(root, file))
