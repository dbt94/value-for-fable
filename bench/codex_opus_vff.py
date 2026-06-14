#!/usr/bin/env python3
# GPT(gpt-5.5 via codex)가 심판: Opus+v2 vs 맨 Opus. "VFF가 Opus엔 마진 작은가"를 비-Claude로 재확인.
import json, re, subprocess
CAP=700
TP={'H1':'FastAPI 간헐 500 에러 원인·접근 조언','H4':'일부 요청만 3초+ 느린 웹서비스 원인 좁히기',
    'H5':'스타트업 백엔드 모놀리식 vs 마이크로서비스 판단','H6':'주문 API p99 지연 200ms→2초 회귀 원인 좁히기'}
GL=['No task provided','SubagentStop']
v2=json.load(open('opus_v2_answers.json'))
d=json.load(open('v3_raw.json'))['gen']
def bare(t): return next((g['answer'] for g in d if g['taskId']==t and g['condition']=='opus_plain' and not any(m in g['answer'] for m in GL)),None)
def ask(p):
    try: r=subprocess.run(['codex','exec','--skip-git-repo-check',p],capture_output=True,text=True,timeout=200).stdout
    except Exception as e: r=f'ERR{e}'
    m=list(re.finditer(r'WINNER\s*=\s*([AB])',r,re.I)); return m[-1].group(1).upper() if m else None
res={}
for t in ['H1','H4','H5','H6']:
    a_v2=v2.get(t); a_op=bare(t)
    if not a_v2 or not a_op: res[t]={'status':'no_data'}; print(t,'데이터없음'); continue
    picks=[]
    for nA,aA,nB,aB in [('opus_v2',a_v2,'opus_bare',a_op),('opus_bare',a_op,'opus_v2',a_v2)]:
        p=(f'두 답변 A·B는 같은 요청에 대한 답이다. 요청: {TP[t]}\n\n더 정확하고 실질적으로 유용한 답은? '
           f'길다고 좋은 게 아니다. 어느 게 어느 설정인지 모른다. 마지막 줄에 한 줄로만.\n\n'
           f'### A\n{aA[:CAP]}\n\n### B\n{aB[:CAP]}\n\n마지막 줄: WINNER=A 또는 WINNER=B')
        w=ask(p)
        if w: picks.append(nA if w=='A' else nB)
    if len(picks)==2:
        verdict=picks[0]+' (양방향일치)' if picks[0]==picks[1] else '무승부/순서편향'
        res[t]={'status':'ok','picks':picks,'verdict':verdict}; print(f'[{t}] {verdict} picks={picks}')
    else: res[t]={'status':'fail','picks':picks}; print(f'[{t}] codex 실패 picks={picks}')
json.dump(res,open('codex_opus_vff_scores.json','w'),ensure_ascii=False,indent=2)
ok=[r for r in res.values() if r.get('status')=='ok']
print(f"\n=== GPT 심판: Opus+v2 vs 맨Opus ({len(ok)}과제) ===")
print(f"  Opus+v2 우세: {sum(1 for r in ok if r['verdict'].startswith('opus_v2'))} / "
      f"맨Opus 우세: {sum(1 for r in ok if r['verdict'].startswith('opus_bare'))} / "
      f"무승부: {sum(1 for r in ok if '무승부' in r['verdict'])}")
