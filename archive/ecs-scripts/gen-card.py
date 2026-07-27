import json, sys, subprocess, os, tempfile

report_file = sys.argv[1]
with open(report_file) as f:
    report = json.load(f)

branches = report.get('branches', [])
alerts = [b for b in branches if b['level'] in ('CRITICAL', 'WARN')]
oks = [b for b in branches if b['level'] == 'OK']

if not alerts:
    print('')
    sys.exit()

MIRROR = "/opt/pi-orchestrator/drift-mirrors/aetheris"

def analyze_conflicts(branch_name, conflicts):
    """对冲突文件做语义分析,返回人话描述"""
    analyses = []
    for f in conflicts:
        fname = os.path.basename(f)
        if 'work-ledger' in f or 'coordination' in f:
            analyses.append({
                'file': f,
                'type': '协调记录',
                'human': '两边各自追加了工作流水记录(谁做了什么),互不矛盾,取并集即可,不丢数据',
                'risk': '无风险',
                'action': 'Pi可自动解决(取并集)'
            })
        elif f.endswith('.tsx') or f.endswith('.ts'):
            # 代码文件,看 commit message 判断改动性质
            analyses.append({
                'file': f,
                'type': '代码文件',
                'human': f'前后端代码 `{fname}` 两边都有修改,需对应Agent判断保留哪边',
                'risk': '需人工判断',
                'action': '交对应Agent处理'
            })
        elif f.endswith('.md'):
            analyses.append({
                'file': f,
                'type': '文档',
                'human': f'文档 `{fname}` 两边都有更新,内容不冲突则合并',
                'risk': '低风险',
                'action': '可合并'
            })
        else:
            analyses.append({
                'file': f,
                'type': '其他',
                'human': f'文件 `{fname}` 两边都有改动',
                'risk': '需判断',
                'action': '交Agent检查'
            })
    return analyses

def get_commit_summaries(branch, limit=5):
    """获取分支领先master的commit摘要"""
    try:
        ref = f"refs/remotes/origin/{branch}"
        master = "refs/remotes/origin/master"
        result = subprocess.check_output(
            ["git", "rev-list", "--oneline", f"{master}..{ref}"],
            cwd=MIRROR, text=True
        ).strip().split('\n')[:limit]
        return result if result != [''] else []
    except:
        return []

# 构造每个分支的人话描述
alert_lines = []
auto_resolvable = 0
needs_human = 0

for b in alerts:
    icon = '🔴' if b['level'] == 'CRITICAL' else '🟡'
    name = b['branch'].replace('agent/', '')
    ahead = b['ahead']
    behind = b['behind']
    conflicts = b.get('conflicts', [])
    
    # 分支领先master的工作摘要
    commits = get_commit_summaries(b['branch'])
    
    # 冲突分析
    conflict_descs = []
    branch_auto = 0
    branch_human = 0
    for c in conflicts:
        analysis = analyze_conflicts(name, [c])
        a = analysis[0]
        conflict_descs.append(f"  • `{c}` — {a['human']} ({a['action']})")
        if '自动' in a['action']:
            auto_resolvable += 1
            branch_auto += 1
        else:
            needs_human += 1
            branch_human += 1
    
    # 分支总结(人话)
    if ahead > 0 and behind > 0:
        summary = f"{icon} **{name}** — 这个分支有 {ahead} 个新工作还没合入主线,同时落后主线 {behind} 个更新"
    elif ahead > 0:
        summary = f"{icon} **{name}** — 有 {ahead} 个新工作待合入主线"
    elif behind > 0:
        summary = f"{icon} **{name}** — 落后主线 {behind} 个更新,Pi可安全同步"
    
    # 冲突影响(人话)
    if branch_auto > 0 and branch_human == 0:
        impact = f"  影响: 全部冲突都可自动解决,不丢数据"
    elif branch_auto > 0 and branch_human > 0:
        impact = f"  影响: {branch_auto}个可自动解决,{branch_human}个需{name}Agent人工判断"
    elif branch_human > 0:
        impact = f"  影响: {branch_human}个冲突需{name}Agent人工判断"
    else:
        impact = ""
    
    # 最近改了什么(人话,从commit message)
    if commits:
        recent = commits[0].split(' ', 1)[1] if ' ' in commits[0] else commits[0]
        impact += f"\n  最近工作: {recent[:60]}"
    
    block = summary
    if conflict_descs:
        block += "\n冲突文件:\n" + '\n'.join(conflict_descs)
    if impact:
        block += f"\n{impact}"
    alert_lines.append(block)

ok_str = '、'.join(b['branch'].replace('agent/','') for b in oks) if oks else '无'
alert_md = '\n\n'.join(alert_lines)

# 总体影响评估
if needs_human == 0:
    overall = "✅ 所有冲突Pi都能自动解决,不丢数据,不需要你操心"
elif auto_resolvable > 0:
    overall = f"⚠️ {auto_resolvable}个冲突Pi可自动解决,{needs_human}个需对应Agent处理。你不需要手动操作"
else:
    overall = f"⚠️ {needs_human}个冲突需对应Agent处理。建议点击「通知各Agent处理」"

card = {
    'schema': '2.0',
    'config': {'update_multi': True, 'width_mode': 'default'},
    'header': {
        'title': {'tag': 'plain_text', 'content': '⚠️ Pi 漂移体检报告'},
        'subtitle': {'tag': 'plain_text', 'content': f'{len(alerts)}个分支需关注 · {report.get("timestamp","")[:16]}'},
        'template': 'red'
    },
    'body': {
        'elements': [
            {'tag': 'markdown', 'content': alert_md},
            {'tag': 'hr'},
            {'tag': 'markdown', 'content': f'<font color="grey">{overall}</font>'},
            {'tag': 'markdown', 'content': f'<font color="grey">✅ 已同步: {ok_str}</font>'},
            {'tag': 'column_set', 'flex_mode': 'stretch', 'columns': [
                {'tag': 'column', 'width': 'weighted', 'weight': 1, 'elements': [{'tag': 'button', 'element_id': 'btnNotify', 'text': {'tag': 'plain_text', 'content': '📋 通知各Agent处理'}, 'type': 'primary_filled', 'width': 'fill', 'behaviors': [{'type': 'callback', 'value': {'action': 'notify_agents'}}]}]},
                {'tag': 'column', 'width': 'weighted', 'weight': 1, 'elements': [{'tag': 'button', 'element_id': 'btnAuto', 'text': {'tag': 'plain_text', 'content': '🔧 自动解决可解决的'}, 'type': 'default', 'width': 'fill', 'behaviors': [{'type': 'callback', 'value': {'action': 'auto_ledger'}}]}]},
                {'tag': 'column', 'width': 'weighted', 'weight': 1, 'elements': [{'tag': 'button', 'element_id': 'btnView', 'text': {'tag': 'plain_text', 'content': '👁 查看详情'}, 'type': 'default', 'width': 'fill', 'behaviors': [{'type': 'open_url', 'default_url': 'https://aetherisonline.xyz/pi-drift-report'}]}]}
            ]}
        ]
    }
}
print(json.dumps(card, ensure_ascii=False))
