import os, json

# List all template folders
dirs = sorted([d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('Mẫu')])
with open('_template_list.txt', 'w', encoding='utf-8') as f:
    for d in dirs:
        f.write(d + '\n')
