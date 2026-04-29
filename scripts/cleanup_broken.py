import yaml, re, os

mi_dir = r'C:\Users\lduan\.copilot\agents\skills\kql-templates\mi'

def is_valid_kql(query):
    if not query or len(str(query)) < 20:
        return False
    q = str(query)
    has_table = bool(re.search(r'\b(Mon\w+|Alr\w+|SqlFailovers|OutageReasons)\b', q))
    has_pipe = '|' in q
    starts_let = q.strip().startswith('let ')
    if not has_table and not starts_let:
        return False
    if not has_pipe and not (starts_let and has_table):
        return False
    return True

total_removed = 0
total_kept = 0

for cat in ['performance', 'availability', 'backup-restore', 'networking', 'general']:
    filepath = os.path.join(mi_dir, cat, f'{cat}.yaml')
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data or 'SqlSkills' not in data:
        continue
    
    valid_skills = []
    removed = 0
    for skill in data['SqlSkills']:
        kqs = skill.get('KustoQueries', [])
        if kqs and is_valid_kql(kqs[0].get('ExecutedQuery', '')):
            valid_skills.append(skill)
        else:
            removed += 1
    
    # Re-number IDs
    cat_id = cat.replace("-", "_")
    for i, skill in enumerate(valid_skills):
        skill['id'] = f'MI-{cat_id}-{i+1}'
    
    data['SqlSkills'] = valid_skills
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
    
    total_removed += removed
    total_kept += len(valid_skills)
    print(f'{cat}: kept {len(valid_skills)}, removed {removed}')

print(f'\nTotal: kept {total_kept}, removed {total_removed}')
