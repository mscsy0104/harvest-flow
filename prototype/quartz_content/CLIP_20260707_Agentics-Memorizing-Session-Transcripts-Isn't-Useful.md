---
status: 출간
date created: Tuesday, July 7th 2026, 2:51:36 pm
date modified: Tuesday, July 7th 2026, 2:56:27 pm
---

### 🤖 AI 자동 요약 및 인덱싱
요약:
- AI 에이전트에게 이전 세션 기록(transcript)을 검색하게 하는 것은 토큰만 낭비하고 성능 저하를 초래할 수 있어 비효율적입니다.
- 에이전트의 성능 향상을 위해서는 휘발성 대화 기록 대신, 인간이 검토하고 정리한 고품질의 문서화 및 아티팩트를 활용하는 것이 핵심입니다.

태그:
#AI에이전트 #LLM아키텍처 #메모리관리

---

### 본문
[ref](https://gemini.google.com/app/596420f3a4370702?is_sa=1&is_sa=1&android-min-version=301356232&ios-min-version=322.0&campaign_id=bkws&utm_source=sem&utm_source=google&utm_medium=paid-media&utm_medium=cpc&utm_campaign=bkws&utm_campaign=2024koKR_gemfeb&pt=9008&mt=8&ct=p-growth-sem-bkws&gclsrc=aw.ds&gad_source=1&gad_campaignid=20437330476&gbraid=0AAAAApk5Bhk98pjT1pmARb7dFRAZjRff1&gclid=CjwKCAjwisnGBhAXEiwA0zEOR5_WYGCZyFvtAOSEgFq77O3Hd71-9eUy5-R6OSYJhMCTnkVRDNLguxoC-_8QAvD_BwE)


이 글은 AI 에이전트 개발에서 흔히 사용되는 **'세션 기록(transcript)의 자동 저장 및 검색' 방식이 실제로는 성능 향상에 도움이 되지 않는다**는 저자의 비판적인 견해를 담고 있습니다.

# 주요 내용 요약

- **비효율적인 기억 방식:** 저자는 SWE(소프트웨어 엔지니어링) 작업 시 AI 에이전트에게 이전 세션 기록을 검색하게 해도 성능상의 이점이 전혀 없음을 발견했습니다. 오히려 불필요한 토큰을 낭비하고 모델의 품질을 저하시키는 결과를 초래했습니다.
    
- **'스크래치'보다 '아티팩트'의 중요성:** AI가 휘발성 메모리(세션 기록)에 의존하는 대신, 잘 작성된 커밋 메시지, PR 설명, 문서화 등 '코드와 함께 저장된 아티팩트'를 참조하게 했을 때 훨씬 더 효과적이었습니다. 이미 코드를 통해 요약된 정보를 다시 검색하는 것은 중복 작업일 뿐이라는 설명입니다.
    
- **맥락 관리의 한계(의도 표류):** 모델은 무엇이 잘못된 정보인지 판단하지 못한 채 모든 입력 값을 '진실(ground truth)'로 받아들입니다. 따라서 검증되지 않은 이전 세션 기록이 누적되면, 잘못된 의도가 계속해서 다음 작업으로 이어지는 '의도 표류(intent drift)' 현상이 발생합니다.
    
- **자동화의 위험성:** 에이전트가 스스로 메모리를 관리(정리)하는 능력은 현재 부족합니다. 저자의 팀에서 진행한 자동 업데이트 테스트 결과, 80% 이상의 자동 제안이 오히려 모델 성능을 떨어뜨렸습니다.
    

# 댓글 반응

- **의견 공유:** 한 댓글 작성자는 "Chesterton's Fence(필요성을 이해하기 전까진 무언가를 제거하지 말라는 원칙)와 '어두운 숲(Dark Forest)' 이론이 합쳐진 것과 같다"며, 복잡한 비즈니스 맥락에서 자동화가 오히려 위험할 수 있다는 저자의 의견에 동조했습니다.
    
- **인간적인 측면:** 다른 사용자는 AI가 스스로 메모리를 관리하지 못하고 혼란을 겪는 모습이 오히려 "가장 인간적인 면모"라고 평했습니다.
    

**핵심 결론:** AI 에이전트의 성능을 높이려면 단순히 모든 대화 기록을 저장하기보다, **인간이 검토하고 정리한 고품질의 문서화(아티팩트)를 에이전트가 학습하도록 유도하는 것이 훨씬 더 효율적**이라는 주장입니다.


---
We have found zero performance benefit on SWE tasks when agents have search access to their previous transcript sessions, provided they have access to other forms of context. We also have not found much benefit in trying to automatically trawl through session transcripts to improve agent context, unless there is a human in the loop.

This was pretty surprising.

Intuitively it feels like there's a lot of valuable information in a transcript between an agent and an engineer. Maybe it would have information about why the code exists, about user intent. Or it might have the other approaches that a user tried and discarded. At the least, it would have some amount of additional context that the agent could use to augment its understanding. I believed this so strongly that my company built an entire product around this concept. I used to tell folks that "session transcripts were the new oil," that they were more valuable than the code itself.

Other people have clearly had similar thoughts, which is why there are so many different tools to do session backed memory, including (of course) Claude Code itself.

I think the most common architecture is to do something like:

- Store all transcripts across an organization in a DB
    
- Put a vector search, an elastic search, or a SQL search layer in front of it. Ambitious teams will use all three. Maybe graphs will be involved.
    
- Make this available to the agent using an MCP, or by exposing a cli with skills.
    

For us, this additional work doesn't seem to make a bit of difference. If anything, based on many months of testing with and without session search access, it may make the models worse.

Why might this be true?

One thing our team cares a lot about is coding artifacts. We don't really write code by hand anymore. In order to make PRs legible, we emphasize good commit messages, good pr messages, and comprehensive documentation. Every code change comes with extensive metadata that is committed alongside the code. When our agents do work on a piece of code, they are instructed to go look at the docs and the previous PRs.

In other words, the agent is already distilling all of the information that is valuable about a transcript, and storing it where it is needed and easily accessible. So when the agent uses a transcript search server, it ends up spending tokens reading things it already knows, while picking up all the stuff that the agent decided _not_ to write down in the first place. Maybe, every now and then, there's some useful nugget of information in there. But most of the time, the agent is just looking at a pseudo nonsensical scratch pad and wasting precious tokens to do so.

The agents are also terrible at actually removing context, which is a critical capability for maintaining long term memory. I mean, across literal thousands of sessions, I've never seen it happen even once.

This is not a trait that can be removed with some clever prompt engineering. Agents don't have state, so they have to assume everything in their input context window is the ground truth. Every line of code, every existing bit of memory, every token is treated as an expression of _intent_ -- even if that code or that memory was generated from a random decision made by some previous agent session, never reviewed or even understood by a human. This _intent drift_ compounds the more the agent tries to autonomously build up a memory base.

As far as I am aware, there are _zero_ coding benchmarks that assume the input data is corrupt. In fact, the models are penalized for assuming that the input data is wrong. This is partially an alignment issue too -- we don't want to have agents doing unintended things, and there isn't an easy way to thread the needle of “don't delete the codebase” and “do delete some of the input context.”

Since models can't actually garden their own memory, automatic memorization ends up in the same place: a load of garbage eating tokens, bloating bills, and degrading model quality.

Net net, I've become really bearish on tools that index and store and surface in session transcripts to an agent. The session transcript may be useful for team observability, but it won't make your agents better.

That doesn't mean that agents have no role in learning context over time. We use our internal nori bots to review everything that happened at the company each week across PRs, slack, drive, etc. And they then propose a set of changes to our built in nori skillsets, tagging the team in slack. These are all default rejected. In order to accept a change, you have to go in and actually look at the diff and make sure it fits the intent.

We accept less than 20% of these. Which means 80% of these “automatic” updates would've made the model worse. I can't imagine how much more unsustainable that would be if a multi-hundred person org were all saving these “updates” automatically all the time.

---

- So there’s an interesting question of “how broad was the business context that led to a line of code or a TODO.” And this can vary between businesses! Sometimes it’s sufficient to have a comment link back to a well maintained story tracker etc., or a motivating slack thread, which a modern LLM is incentivized to follow. But sometimes that motivating example is just part of a broad exploration of numerous experiences and insights, which might have gone through many colleagues exploring the space over time. A future iteration would over-index on the one example. We see this a lot in our curated marketplace, where a fix to an integration exists in the context of dozens of times listings were manually patched or overridden beforehand. And if I were fixing that fix, would I find everything that motivated the old code? It’s like Chesterton’s Fence meets the Dark Forest. I wouldn’t give up on your product just yet!

- In this way it is most human.