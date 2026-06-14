#!/usr/bin/env python3
# 비-Claude 3번째 가족(GPT/gpt-5.5 via codex) 페어와이즈 검증: Sonnet+v2 vs 맨 Opus.
# gemini와 동일 설계: 중립 프롬프트·익명 A/B·순서 양방향 2회. 객관성 위해 v2/opus 명칭 숨김.
import json, re, subprocess
CAP=700
TP={'H1':'FastAPI 간헐 500 에러 원인·접근 조언','H2':'영수증 자동가계부 앱 공모전 기대효과 350자',
    'H3':'RAG를 컴퓨터공학 학부 2학년에게 설명','H4':'일부 요청만 3초+ 느린 웹서비스 원인 좁히기',
    'H5':'스타트업 백엔드 모놀리식 vs 마이크로서비스 판단','H6':'주문 API p99 지연 200ms→2초 회귀 원인 좁히기'}
SRC={'H1':'v3_raw.json','H4':'v3_raw.json','H5':'v3_raw.json','H6':'v3_raw.json','H2':'v2_raw.json','H3':'v2_raw.json'}
GL=['No task provided','No task was provided','SubagentStop']
def get(task,cond):
    for g in json.load(open(SRC[task]))['gen']:
        if g['taskId']==task and g['condition']==cond and not any(m in g['answer'] for m in GL):
            return g['answer']
    return None
def ask(prompt):
    for _ in range(1):
        try:
            r=subprocess.run(['codex','exec','--skip-git-repo-check',prompt],
                             capture_output=True,text=True,timeout=200).stdout
        except Exception as e: r=f'ERR{e}'
        m=list(re.finditer(r'WINNER\s*=\s*([AB])', r, re.I))
        if m: return m[-1].group(1).upper()
    return None
res={}
for t in ['H1','H2','H3','H4','H5','H6']:
    v2=get(t,'sonnet_v2'); op=get(t,'opus_plain')
    if not v2 or not op: res[t]={'status':'no_data'}; print(t,'데이터없음'); continue
    picks=[]
    for nameA,ansA,nameB,ansB in [('sonnet_v2',v2,'opus_plain',op),('opus_plain',op,'sonnet_v2',v2)]:
        p=(f'두 답변 A·B는 같은 요청에 대한 답이다. 요청: {TP[t]}\n\n'
           f'더 정확하고 실질적으로 유용한 답은? 길다고 좋은 게 아니다. 분량 지정이 있으면 준수도 본다. '
           f'설명·근거 없이 마지막 줄에 딱 한 줄로만 답하라.\n\n'
           f'### A\n{ansA[:CAP]}\n\n### B\n{ansB[:CAP]}\n\n마지막 줄: WINNER=A 또는 WINNER=B')
        w=ask(p)
        if w: picks.append(nameA if w=='A' else nameB)
    if len(picks)==2:
        verdict=picks[0]+' (양방향 일치)' if picks[0]==picks[1] else '무승부/순서편향'
        res[t]={'status':'ok','picks':picks,'verdict':verdict}; print(f'[{t}] {verdict}  picks={picks}')
    else:
        res[t]={'status':'fail','picks':picks}; print(f'[{t}] codex 실패 picks={picks}')
json.dump(res,open('codex_pairwise_scores.json','w'),ensure_ascii=False,indent=2)
ok=[r for r in res.values() if r.get('status')=='ok']
print(f'\n=== GPT(gpt-5.5) 페어와이즈 집계 ({len(ok)}과제) ===')
print(f"  Sonnet+v2 우세: {sum(1 for r in ok if r['verdict'].startswith('sonnet_v2'))} / "
      f"맨Opus 우세: {sum(1 for r in ok if r['verdict'].startswith('opus_plain'))} / "
      f"무승부: {sum(1 for r in ok if '무승부' in r['verdict'])}")
