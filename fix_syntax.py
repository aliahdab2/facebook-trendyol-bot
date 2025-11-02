#!/usr/bin/env python3
"""
Fix syntax errors in source files caused by Arabic removal
"""

from pathlib import Path
import re

def fix_indentation(content):
    """Fix indentation issues"""
    lines = content.split('\n')
    fixed_lines = []
    indent_level = 0
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append('')
            continue
        
        # Determine correct indentation
        if stripped.startswith('class '):
            indent_level = 0
        elif stripped.startswith('def ') or stripped.startswith('async def '):
            if i > 0 and 'class ' in ''.join(lines[max(0, i-10):i]):
                indent_level = 1
            else:
                indent_level = 0
        elif stripped.startswith('"""'):
            # Keep current indentation for docstrings
            pass
        
        # Count expected indentation from previous line
        if i > 0:
            prev_line = lines[i-1].strip()
            if prev_line.endswith(':'):
                # Should be indented more
                current_indent = len(line) - len(stripped)
                if current_indent == 0 or current_indent == 1:
                    line = '    ' * (indent_level + 1) + stripped
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(filepath):
    """Fix a single file"""
    print(f"Fixing {filepath}...")
    
    content = Path(filepath).read_text(encoding='utf-8')
    original_content = content
    
    # Fix specific patterns
    
    # Fix broken docstrings at line 1-4
    content = re.sub(
        r'^"""\n([^\n]+)([^\n]+)\n([^\n]+)\n"""',
        r'"""\n\1\n\2\n\3\n"""',
        content,
        flags=re.MULTILINE
    )
    
    # Remove stray Arabic text that wasn't removed properly
    content = re.sub(r'[\u0600-\u06FF]+', '', content)
    
    # Fix common syntax patterns
    # Fix: "Args:" followed by parameter without newline
    content = re.sub(r'Args:\s*(\w+):', r'Args:\n        \1:', content)
    
    # Fix: "Returns:" without proper spacing
    content = re.sub(r'(\w+)Returns:', r'\1\n        Returns:', content)
    
    # Fix broken triple quotes
    content = re.sub(r'"""([^"]+)$', r'"""\1"""', content, flags=re.MULTILINE)
    
    # Fix unmatched parentheses/braces
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        print(f"  ⚠️  Warning: Unmatched parentheses ({open_parens} open, {close_parens} close)")
    
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        print(f"  ⚠️  Warning: Unmatched braces ({open_braces} open, {close_braces} close)")
    
    if content != original_content:
        Path(filepath).write_text(content, encoding='utf-8')
        print(f"  ✅ Fixed")
    else:
        print(f"  ℹ️  No changes needed")

def main():
    files = [
        'src/database.py',
        'src/facebook_collector.py',
        'src/content_analyzer.py',
        'src/trendyol_matcher.py',
        'src/content_processor.py',
        'src/publisher.py',
        'src/scheduler.py',
        'main.py',
    ]
    
    print("🔧 Starting syntax fixes...\n")
    
    for filepath in files:
        if Path(filepath).exists():
            fix_file(filepath)
        else:
            print(f"❌ File not found: {filepath}")
    
    print("\n✅ Done! Run pytest to verify.")

if __name__ == '__main__':
    main()
