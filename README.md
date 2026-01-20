## 📝 Commit Convention

우리 팀은 [Conventional Commits](https://www.conventionalcommits.org/) 규격을 따릅니다.
커밋 메시지는 아래와 같은 형식을 권장합니다.

`type(scope): subject`

### 1. Type (유형)

| 태그 | 설명 |
|:---:|:---|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 (README.md, 주석 등) |
| `style` | 코드 포맷팅, 세미콜론 누락 등 (로직 변경 없음) |
| `refactor` | 코드 리팩토링 (기능 변경 없음) |
| `test` | 테스트 코드 추가 및 수정 |
| `chore` | 빌드 업무, 패키지 매니저 설정, 에셋 등 기타 변경사항 |
| `perf` | 성능 개선 |
| `ci` | CI/CD 설정 변경 |

### 2. Subject (제목)
- **50자 이내**로 작성합니다.
- 문장 끝에 마침표(`.`)를 찍지 않습니다.
- **문장 맨 뒤에 관련된 Jira 티켓 번호를 대괄호와 함께 명시합니다.**
  - 형식: `type(scope): subject [Jira-Ticket-ID]`
  - 예시: `feat: 로그인 API 구현 [DEV-101]`

### 3. Body (본문 - 선택 사항)
- 제목만으로 설명이 부족할 때 작성합니다.
- 지라 티켓의 상태를 변경하고 싶다면 스마트 커밋 명령어를 사용합니다.
  - 예시: `Resolves [DEV-101]` (티켓을 완료 상태로 변경)

---
**작성 예시**
> feat: 사용자 로그인 API 구현
> fix: JWT 토큰 만료 시간 버그 수정