---
date created: Monday, June 29th 2026, 10:06:32 am
date modified: Wednesday, July 15th 2026, 1:09:47 pm
status: 출간
post_id: 20260725-wiki-uuid-efbb
---

### 🤖 AI 자동 요약 및 인덱싱
- UUID는 128-bit의 고유 식별자로, 중앙 시스템에 등록 없이 빠르고 간단하게 생성 가능하며 완전히 고유하지 않을 확률은 매우 작습니다.
#데이터 #UUID  

#데이터 #생산성

---

### 본문
Ref. https://docs.tosspayments.com/resources/glossary/uuid

# UUID(Universally Unique Identifier)

- UUID는 128-bit의 고유 식별자에요. 
- 다른 고유 ID 생성 방법과 다르게 UUID는 중앙 시스템에 등록하고 발급하는 과정이 없어서 상대적으로 더 빠르고 간단하게 만들 수 있다는 장점이 있어요.
- 하지만 완전히 고유하지 않을 확률이 있는데요. [RFC 4122](https://datatracker.ietf.org/doc/html/rfc4122) 문서에 정의된 UUID 버전 4 표준 규약을 따르면 1조 개의 UUID 중에 중복이 일어날 확률은 10억 분의 1입니다.
- UUID의 또 다른 장점은 작은 크기입니다. 다른 고유 식별자에 비해 정렬, 차수, 해싱 등 다양한 알고리즘에 사용하기 쉽고 데이터베이스에 보관하기도 용이해요.

## UUID 구조

UUID의 구조를 더 자세히 살펴볼게요. 일단 128-bit의 숫자 문자열이고 총 길이는 36자리입니다. 32개의 16진수 숫자가 4개의 하이픈으로 나누어진 8-4-4-4-12 형태에요. 예를 들어 `9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d`와 같은 형태이죠.

하이픈 사이에 있는 16진수 숫자들은 하나의 필드인데요. 각 필드는 정수로 취급되며 가장 중요한 숫자가 앞에 나옵니다. 예를 들어 아래 이미지에 볼드된 세 번째 필드의 첫 숫자는 `4`인데요, UUID의 버전입니다. 어떤 UUID를 봐도 세 번째 필드의 첫 번째 숫자는 버전 정보를 나타내요.

![UUID 구조](https://static.tosspayments.com/docs/glossary/uuid-img1.png)

**UUID 필드**

각 필드 정보는 아래 표에서 확인할 수 있어요.

| 필드                        | 사이즈            | 설명                                |
| --------------------------- | ----------------- | ----------------------------------- |
| `time-low`                  | 4hexOctet / 32bit | 타임스탬프의 low field              |
| `time-mid`                  | 2hexOctet / 16bit | 타임스탬프의 mid field              |
| `time-high-and-version`     | 2hexOctet / 16bit | 타임스탬프의 high field & UUID 버전 |
| `clock-seq-hi-and-reserved` | hexOctet / 8bit   | 클락 시퀀스의 high field & variant  |
| `clock-seq-low`             | hexOctet / 8bit   | 클락 시퀀스의 low field             |
| `node`                      | 6hexOctet / 48bit | node 식별자                         |

**UUID 버전**

UUID는 총 5개의 버전이 있어요. 버전 1, 2는 보통 타임스탬프(Timestamp) UUID로 부르는데요. 버전 1, 2의 UUID는 만들어진 시점과 기기 정보를 알 수 있어요.
버전 3과 5는 네임스페이스(Namespace) 기반으로 만드는 UUID입니다. 네임스페이스를 해싱 알고리즘으로 암호화해서 UUID를 생성해요. 버전 3, 5의 UUID는 다른 정보와 연결된 값을 만들고 싶을 때 사용하면 좋아요.

가장 흔히 사용하는 UUID는 버전 4인데요. 다른 버전과 달리 외부 정보에 의존하지 않고 완전히 랜덤한 값으로 생성돼요. 시간, 기기 정보, 네임스페이스 등 정보가 없기 때문에 어디서 어떻게 생성됐는지 알 수 없어요. 보안 측면에서 뛰어나고 생성도 빠르기 때문에 대중적으로 사용되고 있어요.

상황에 맞는 UUID 버전을 사용하세요. 완전히 고유하고 랜덤한 값이 필요하다면 버전 4를 사용하세요. 고유하면서 완전히 랜덤한 값보다 특정 정보가 필요하면 다른 버전을 검토해보세요.

## UUID를 만드는 방법

대부분의 언어는 UUID 라이브러리를 지원해요. Java, JavaScript, Python 언어에서 UUID를 만드는 방법을 알아볼게요.

토스페이먼츠는 구매자를 식별하는 `customerKey`와 같은 값을 UUID로 생성하는 것을 추천해요.  

**Java**

[UUID 클래스](https://docs.oracle.com/javase/8/docs/api/java/util/UUID.html)를 불러와요. `randomUUID()`를 호출하면 버전 4 UUID 값을 가진 객체가 반환돼요.

```java theme="grey" copyable="false"
import java.util.UUID;
UUID.randomUUID().toString() // '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d'
```

**JavaScript**

[uuid npm 패키지](https://www.npmjs.com/package/uuid)를 설치하세요. 필요한 UUID 버전을 불러와서 메서드를 호출하세요.

```bash theme="grey" copyable="false"
npm install uuid
```

```js theme="grey" copyable="false"
import { v4 as uuidv4 } from 'uuid';
uuidv4(); // '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d'
```

**Python**

파이썬 [uuid 표준 라이브러리](https://docs.python.org/ko/3/library/uuid.html)를 사용하세요. UUID 객체(UUID 클래스)와 각 버전을 생성할 수 있는 `uuid1()`, `uuid3()`, `uuid4()`, `uuid5()` 메서드를 제공합니다.

```python theme="grey" copyable="false"
import uuid
uuid.uuid4() # UUID('9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d')
```