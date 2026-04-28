import re

def process(file):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    def repl(m):
        cls = m.group(1)
        
        # Text colors
        cls = re.sub(r'\btext-white/([0-9]+)\b', lambda x: f'text-slate-500 dark:text-white/{x.group(1)}', cls)
        cls = re.sub(r'\btext-white(?!\/)\b', 'text-slate-900 dark:text-white', cls)
        
        # Backgrounds
        cls = re.sub(r'\bbg-white/\[([0-9.]+)\]\b', lambda x: f'bg-slate-200/50 dark:bg-white/[{x.group(1)}]', cls)
        cls = re.sub(r'\bbg-white/([0-9]+)\b', lambda x: f'bg-slate-200 dark:bg-white/{x.group(1)}', cls)
        cls = re.sub(r'\bbg-black/([0-9]+)\b', lambda x: f'bg-white/80 dark:bg-black/{x.group(1)}', cls)
        
        # Borders
        cls = re.sub(r'\bborder-white/([0-9]+)\b', lambda x: f'border-slate-200 dark:border-white/{x.group(1)}', cls)
        cls = re.sub(r'\bborder-white/\[([0-9.]+)\]\b', lambda x: f'border-slate-200 dark:border-white/[{x.group(1)}]', cls)

        return 'className=\"' + cls + '\"'

    new_content = re.sub(r'className=\"([^\"]+)\"', repl, content)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)

process('src/components/HistoryPanel.tsx')
process('src/components/PlanSkeleton.tsx')
