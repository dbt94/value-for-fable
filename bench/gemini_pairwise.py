#!/usr/bin/env python3
# 비-Claude(gemini) 페어와이즈 검증: Sonnet+v2 vs 맨 Opus. 순환 채점 비판을 깨는 독립 검증.
# 각 과제마다 순서 양방향(v2먼저/opus먼저)으로 2회 → 일관되면 신뢰. 답변 1400자 캡(긴 프롬프트 침묵 회피).
import json, re, subprocess, random
random.seed(7)
CAP=1400
TP={'H1':'FastAPI 간헐 500 에러 원인·접근 조언','H2':'영수증 자동가계부 앱 공모전 기대효과 350자',
    'H3':'RAG를 컴퓨터공학 학부 2학년에게 설명','H4':'일부 요청만 3초+ 느린 웹서비스 원인 좁히기',
    'H5':'스타트업 백엔드 모놀리식 vs 마이크로서비스 판단','H6':'주문 API p99 지연 200ms→2초 회귀 원인 좁히기'}
SRC={'H1':'v3_raw.json','H4':'v3_raw.json','H5':'v3_raw.json','H6':'v3_raw.json','H2':'v2_raw.json','H3':'v2_raw.json'}
GL=['No task provided','No task was provided','SubagentStop']
def get(task,cond):
    d=json.load(open(SRC[task]))['gen']
    for g in d:
        if g['taskId']==task and g['condition']==cond and not any(m in g['answer'] for m in GL):
            return g['answer']
    return None
def ask(prompt):
    for _ in range(3):
        try: r=subprocess.run(['gemini','-p',prompt],capture_output=True,text=True,timeout=150).stdout
        except Exception as e: r=f'ERR{e}'
        m=re.search(r'WINNER\s*=\s*([AB])', r, re.I)
        if m: return m.group(1).upper()
    return None
res={}
for t in ['H1','H2','H3','H4','H5','H6']:
    v2=get(t,'sonnet_v2'); op=get(t,'opus_plain')
    if not v2 or not op: res[t]={'status':'no_data'}; print(t,'데이터없음'); continue
    picks=[]
    for order in [('sonnet_v2',v2,'opus_plain',op),('opus_plain',op,'sonnet_v2',v2)]:
        nameA,ansA,nameB,ansB=order
        p=(f'두 답변 A·B는 같은 요청에 대한 답이다. 요청: {TP[t]}\n\n'
           f'더 정확하고 실질적으로 유용한 답은? 길다고 좋은 게 아니다. 분량 지정이 있으면 준수도 본다.\n\n'
           f'### A\n{ansA[:CAP]}\n\n### B\n{ansB[:CAP]}\n\n한 줄로만: WINNER=A 또는 WINNER=B')
        w=ask(p)
        if w: picks.append(nameA if w=='A' else nameB)
    if len(picks)==2:
        if picks[0]==picks[1]: verdict=picks[0]+' (양방향 일치)'
        else: verdict='무승부/순서편향'
        res[t]={'status':'ok','picks':picks,'verdict':verdict}
        print(f'[{t}] {verdict}  (picks={picks})')
    else:
        res[t]={'status':'fail','picks':picks}; print(f'[{t}] gemini 실패(picks={picks})')
json.dump(res,open('gemini_pairwise_scores.json','w'),ensure_ascii=False,indent=2)
# 집계
ok=[r for r in res.values() if r.get('status')=='ok']
v2w=sum(1 for r in ok if r['verdict'].startswith('sonnet_v2'))
opw=sum(1 for r in ok if r['verdict'].startswith('opus_plain'))
tie=sum(1 for r in ok if '무승부' in r['verdict'])
print(f'\n=== 비-Claude 페어와이즈 집계 ({len(ok)}과제) ===')
print(f'  Sonnet+v2 우세: {v2w} / 맨Opus 우세: {opw} / 무승부(순서편향): {tie}')
