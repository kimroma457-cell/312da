# PDF·HWP 뷰어 (Android)

기기에 저장된 PDF/HWP 파일을 열거나, 다른 앱의 "공유" 메뉴에서 파일을 받아 바로 볼 수 있는 안드로이드 앱입니다.

## ✅ 빌드 성공 확인됨 (GitHub Actions CI)
아래 환경 조합으로 **`assembleDebug`가 실제로 통과**했고, 결과물 APK까지 생성됐습니다 — 이 저장소의 샌드박스는 네트워크 제약으로 직접 빌드할 수 없어, GitHub Actions(실제 인터넷 접근 가능한 러너)에서 검증했습니다.

- **AGP**: 8.9.1
- **Gradle**: 8.11.1
- **compileSdk**: 36 (**compileSdkExtension**: 19)
- **Kotlin**: 2.1.20
- **Room**: 2.7.1
- **SDK Platform**: `platforms;android-36` 설치 확인됨
- **androidx.pdf**: `pdf-viewer-fragment:1.0.0-alpha19` 및 전이 의존성(`pdf-core`, `pdf-viewer`, `pdf-document-service`) 전부 정상 해결
- minSdk 28 / targetSdk 34 (변경 없음)

**검증 근거**: [워크플로 실행 #4 (run 29810295767)](https://github.com/kimroma457-cell/312da/actions/runs/29810295767) — 커밋 `a900324`, conclusion `success`. `app-debug` APK 아티팩트(약 19MB)가 실제로 생성·업로드되었습니다. 이 초록불이 나오기까지 실제 컴파일러가 잡아준 문제들을 순서대로 고쳤습니다:
1. Kotlin 메타데이터 비호환(androidx.pdf가 Kotlin 2.1.0으로 컴파일됨) → Kotlin 1.9.24 → 2.1.20
2. hwplib의 실제 패키지 세그먼트 `object`가 Kotlin 예약어라 이스케이프 필요(`` `object` ``) — 문법 버그, 로직 변경 없음
3. Room 2.6.1의 kapt 프로세서가 Kotlin 2.1 메타데이터(버전 2.1.0)를 못 읽음 → Room 2.7.1
4. `TrackingPdfViewerFragment.onLoadDocumentSuccess()`가 실제로는 `onLoadDocumentSuccess(document: PdfDocument)` 시그니처였음(문서 요약만으로 추측했던 부분을 실제 컴파일러가 정정) — 시그니처만 수정, 로직 변경 없음

CI 워크플로 자체는 `.github/workflows/android-build.yml`에 있으며, 이 브랜치에 푸시할 때마다 자동으로 재실행됩니다.

## 구성
- `MainActivity` — 파일 선택 버튼(SAF `ACTION_OPEN_DOCUMENT`)
- `ViewerActivity` — 다른 앱의 공유(`ACTION_SEND`)/열기(`ACTION_VIEW`) 요청을 받는 진입점이자 뷰어 화면
- `bookmark/` — Room 기반 북마크(페이지·스크롤 위치)+메모 저장
- `pdf/TrackingPdfViewerFragment` — 공식 `androidx.pdf` 뷰어 로드 성공/실패 콜백 래퍼

### PDF 렌더링 (하이브리드)
기기가 `SdkExtensions.getExtensionVersion(Build.VERSION_CODES.S) >= 13` 조건을 만족하면 Google 공식 `androidx.pdf` (`PdfViewerFragment`)를 사용해 텍스트 검색+하이라이트가 가능합니다. 조건을 만족하지 않으면 [AndroidPdfViewer](https://github.com/mhiew/AndroidPdfViewer) (`com.github.mhiew:android-pdf-viewer`)로 자동 폴백합니다 — 다만 이 폴백 라이브러리는 텍스트 검색 API가 전혀 없어 검색/북마크 버튼이 숨겨집니다.

### HWP 렌더링
[hwplib](https://github.com/neolord0/hwplib) (`kr.dogfoot:hwplib`)로 파싱 후 문단/표 구조를 HTML로 변환해 WebView에 표시합니다. 검색은 `WebView.findAllAsync()`로 구현되어 있습니다.

## 이번에 추가된 기능
1. **전체 텍스트 검색 + 하이라이트**
   - HWP: 검색창 입력 → `findAllAsync` / `findNext`로 이전·다음 이동, 일치 개수 표시. 모든 기기에서 동작.
   - PDF: `androidx.pdf` 사용 가능 기기에서만 지원(뷰어 자체 내장 검색 UI 토글). 폴백 뷰어에서는 검색 버튼이 보이지 않습니다.
2. **북마크(페이지/스크롤 위치) + 메모**
   - Room DB에 문서 Uri별로 저장. 목록 다이얼로그에서 탭하면 해당 위치로 이동, 수정·삭제 가능.
   - **메모 수정**: 목록의 각 항목에 `수정`/`삭제` 버튼이 있습니다. `수정`을 누르면 기존 메모가 채워진 다이얼로그가 뜨고, 저장 시 `BookmarkDao.updateMemo(id, memo, updatedAt)`로 **동일 레코드의 memo/updatedAt 컬럼만** 갱신합니다(삭제 후 재생성하지 않음 — id·docUri·position·createdAt 유지). 취소하면 아무것도 바뀌지 않습니다. 공백만 입력한 메모는 저장 시 빈 문자열로 정리됩니다(`normalizeMemo`).
   - PDF는 폴백 뷰어(`PDF_LEGACY`)에서만 지원합니다 — 공식 `androidx.pdf` 뷰어는 현재 페이지를 읽는 공개 API를 확인하지 못해 그 경로에서는 북마크 버튼을 숨겼습니다.
   - HWP는 스크롤 Y 좌표를 저장합니다(문단 단위가 아님).
   - JSON 내보내기/가져오기는 이번 범위에서 제외했습니다(요청 시 추가 가능).

## 다음에 확인할 것: 공식 androidx.pdf 뷰어 북마크 지원
공식 `PdfViewerFragment`는 `onPdfViewCreated(pdfView: PdfView)` 콜백을 노출하는 것으로 보입니다. Android Studio에서 Gradle sync가 끝난 뒤, `PdfView`의 **공개 API**에 현재 표시 페이지 또는 가시 페이지 범위를 읽을 방법이 있는지 확인해 주세요.

- 공식 공개 API로 확인되면: `TrackingPdfViewerFragment`에 `onPdfViewCreated` 오버라이드를 추가해 위치를 읽고, `ViewerActivity.getCurrentPosition()` / `jumpToPosition()`을 `Mode.PDF_FRAGMENT`에도 연결한 뒤 `bookmarkAddButton`/`bookmarkListButton` 숨김을 해제하면 됩니다.
- 공개 API로 확인되지 않으면: 리플렉션이나 내부(non-public) API로 우회하지 말고, 현재처럼 이 경로에서는 북마크 버튼을 숨긴 채로 둡니다.

해당 지점은 `ViewerActivity.showPdfWithFragment()`와 `TrackingPdfViewerFragment.kt`의 TODO 주석에 표시해 두었습니다.

## 1차 PDF 기능 검증 결과

**이 세션의 샌드박스 자체는 Android SDK/에뮬레이터가 없고 Google Maven(`dl.google.com`) 등 네트워크가 차단되어 있어 직접 빌드할 수 없지만, 위 "빌드 성공 확인됨" 섹션에 있는 GitHub Actions CI로 #1·#2는 실제로 통과했습니다.** 나머지 항목은 여전히 실기기가 필요합니다.

| # | 항목 | 상태 |
|---|------|------|
| 1 | Gradle Sync로 `androidx.pdf`/Room/기존 PDF 뷰어 의존성 해결 확인 | **✅ 실제 CI로 확인됨.** [run 29810295767](https://github.com/kimroma457-cell/312da/actions/runs/29810295767)에서 `androidx.pdf:pdf-core/pdf-viewer/pdf-document-service/pdf-viewer-fragment:1.0.0-alpha19`, `androidx.room:*:2.7.1`, `com.github.mhiew:android-pdf-viewer:3.2.0-beta.3`, `kr.dogfoot:hwplib:1.1.10` 전부 정상 해결됨(`:app:dependencies` 출력으로 확인). |
| 2 | Debug/Release 빌드, 컴파일 오류·경고·중복 의존성·난독화 오류 확인 | **✅ Debug는 CI로 확인됨(`assembleDebug` 성공, APK 아티팩트 생성).** 이 과정에서 실제 컴파일 오류 4건을 발견해 고쳤습니다: ① `HWP_MIME_TYPES.contains(mimeType)` nullable 타입 불일치, ② hwplib의 `object` 패키지 세그먼트 Kotlin 예약어 충돌, ③ Room 2.6.1이 Kotlin 2.1 메타데이터를 못 읽음, ④ `TrackingPdfViewerFragment.onLoadDocumentSuccess()`의 실제 시그니처가 `(document: PdfDocument)`였음. **Release 빌드(`assembleRelease`)와 R8 난독화 동작은 CI 워크플로에 아직 포함되지 않아 미확인**입니다 — 필요하시면 워크플로에 단계를 추가하겠습니다. |
| 3 | 실기기 PDF 유형별 테스트(일반 텍스트/스캔 이미지/100p+/한영 혼합/암호·손상/공유받은 파일) | **미수행.** 기기가 없어 어떤 PDF도 열어보지 못했습니다. |
| 4 | 검색 결과 이동·하이라이트 위치 정확성 | **미수행.** HWP 쪽 `WebView.findAllAsync`/`findNext`는 표준 플랫폼 API라 동작 자체는 신뢰하지만 실제 하이라이트 좌표는 기기에서 봐야 확인됩니다. PDF 쪽은 `androidx.pdf`의 내장 검색 UI라 저희 코드가 하이라이트를 직접 그리지 않습니다. |
| 5 | 앱 완전 종료 후 재실행 시 북마크·메모 유지 | **코드로는 보장됨, 기기 검증은 안 됨.** Room DB는 `docviewer.db` 파일로 디스크에 저장되고 앱 재시작과 무관하게 유지되는 것이 Room의 표준 동작입니다. 메모 수정(`updateMemo`)도 같은 DB 파일에 대한 UPDATE라 동일하게 재시작 후에도 유지됩니다. 단, 공유로 받은 파일은 URI 권한이 만료되어 그 문서를 다시 열지 못할 수 있음(아래 "알려진 제약" 참고) — 이 경우도 앱이 크래시하지 않고 "다시 선택하기" 안내가 뜨도록 이번에 수정했습니다(#8 참고). |
| 6 | 북마크 목록에서 정확한 페이지 이동, 수정·삭제 정상 동작 | **코드 경로는 존재, 기기 검증은 안 됨.** 이동은 `pdfView.jumpTo()`/`webView.scrollTo()`(둘 다 소스로 시그니처 확인됨), 삭제는 Room `@Delete` 후 목록 갱신. **메모 수정 기능을 새로 추가**: 목록 각 항목의 `수정` 버튼 → 기존 메모가 채워진 다이얼로그 → 저장 시 `BookmarkDao.updateMemo(id, memo, updatedAt)`로 같은 레코드의 memo/updatedAt만 갱신(삭제 후 재생성 아님) → `refresh()`로 목록 즉시 반영. 취소는 DB에 아무 영향 없음. Room 스키마에 `updatedAt` 컬럼이 추가되어 `@Database version`을 1→2로 올리고 `fallbackToDestructiveMigration()`을 적용했습니다(아직 배포 전이라 기존 dev 빌드의 북마크가 있다면 이 업그레이드 1회에 한해 초기화됨 — 실제 마이그레이션 동작은 기기에서 확인 필요). |
| 7 | 같은 파일명/경로가 달라도 북마크가 잘못 연결되지 않는지 | **코드 검토로 확인.** 북마크는 파일명이 아니라 전체 content Uri 문자열(`uri.toString()`)로 키를 잡습니다. 서로 다른 Uri는 절대 같은 키로 매핑되지 않으므로, 이름이 같은 두 파일이나 같은 파일을 다른 앱/경로로 연 경우 모두 별도 버킷으로 분리됩니다(반대로 말하면 "물리적으로 같은 파일"이어도 Uri가 다르면 북마크가 자동으로 합쳐지지는 않습니다 — 안전한 쪽으로 치우친 설계). |
| 8 | 공유 URI 권한 만료 시 크래시 없이 재선택 안내 | **이번에 수정함.** 기존 코드는 `openFile()` 초반의 `contentResolver.getType()`/파일명 조회가 try/catch 없이 호출되어 `SecurityException` 발생 시 크래시할 수 있었습니다. 이번에 `openFile()`, `showPdfLegacy`의 `onError`, `showPdfWithFragment`의 로드 실패 콜백, `showHwp`의 스트림 열기 각각에서 `SecurityException`을 구분해 잡고, "공유받은 파일에 대한 접근 권한이 만료되었습니다. 파일을 다시 선택해주세요." 메시지와 "다시 선택하기" 버튼(MainActivity로 이동)을 보여주도록 했습니다. 다만 AndroidPdfViewer의 내부 오류 전달 경로(`DecodingAsyncTask` → `loadError()` → `onError`)는 소스코드로 확인했지만, 실제 만료된 URI로 어떤 예외가 도달하는지는 기기 테스트 없이는 100% 장담할 수 없습니다. |
| 9 | 회전/백그라운드 복귀/다크모드/저사양 기기에서 페이지·상태 비정상 초기화 없음 | **부분적으로 수정함.** ① 회전: 매니페스트에 `configChanges="orientation\|screenSize\|keyboardHidden"`이 이미 있어 Activity가 재생성되지 않음(기존 그대로). ② 다크모드 전환은 `uiMode` configChange가 빠져 있어 테마 변경 시 Activity가 재생성되고 상태가 날아갈 수 있었던 버그를 발견 — `uiMode`를 추가해 수정함. ③ 백그라운드 복귀는 프로세스가 죽지 않는 한 Android가 Activity를 재생성하지 않으므로 원래도 문제없음(OS 표준 동작, 별도 수정 불필요). ④ 저사양 기기의 백그라운드 프로세스 강제 종료(process death) 후 복원은 기존에 전혀 대비가 없었던 부분이라 `onSaveInstanceState`/`onCreate(savedInstanceState)`로 현재 Uri와 페이지/스크롤 위치를 저장·복원하도록 추가했습니다. `androidx.pdf` 경로는 현재 페이지를 읽는 공개 API가 확인되지 않아 이 복원 대상에서 제외됩니다(위 TODO와 동일한 제약). 이 동작 자체가 실기기에서 의도대로 작동하는지는 검증되지 않았습니다. |
| 10 | 결과를 README에 정리 | 이 섹션이 그 결과입니다. |

**요약:** #1(Gradle Sync/의존성 해결)과 #2(assembleDebug 컴파일)는 GitHub Actions CI로 실제로 그린을 확인했습니다 — 그 과정에서 컴파일 오류 4건(위 표 참고)을 실제로 찾아 고쳤습니다. #8(URI 권한 만료 크래시 방지)과 #9(다크모드/프로세스 종료 상태 복원)의 코드도 이 그린 빌드에 포함되어 컴파일은 통과했지만, 그 동작이 "의도한 대로 실행되는지"(실기기에서 크래시 안 뜨는지, 회전 시 페이지가 유지되는지 등)는 여전히 실기기 테스트가 필요합니다. #3·#4·#10 나머지 실기기 테스트도 이 세션에서는 할 수 없습니다.

### 메모 수정 기능 — 빌드 확인됨
`::refresh` 로컬 함수 참조, `Bookmark.updatedAt` 추가, Room `version = 2` + `fallbackToDestructiveMigration()`, `BookmarkListAdapter`의 `onEdit` 콜백까지 전부 위 그린 CI 빌드(`assembleDebug`)에 포함되어 **컴파일 통과가 실제로 확인됐습니다.** 다만 "저장 후 목록에 즉시 반영되는지", "앱 재시작 후 수정 내용이 남아있는지" 같은 **런타임 동작**은 여전히 실기기/에뮬레이터에서 확인이 필요합니다(컴파일 성공 ≠ 기능이 화면에서 의도대로 동작함).

## 알려진 제약
- **북마크 지속성**: 다른 앱의 "공유"로 받은 파일은 보통 임시 URI 권한이라 앱을 재시작하면 그 파일의 URI가 무효화될 수 있습니다 — 이 경우 저장된 북마크가 있어도 파일을 다시 열 수 없습니다. 앱 내 "파일 열기" 버튼(SAF)으로 연 파일은 영구 권한을 요청하므로 재시작 후에도 안정적으로 열립니다.
- **HWP 표시 한계**: 글자 단위 서식(굵기/기울임/색상)과 이미지는 재현되지 않고, 문단·표 구조와 텍스트만 표시됩니다.
- **androidx.pdf 가용성**: 구글 플레이 시스템 업데이트(Mainline) 확장 모듈이 낮은 기기(구형 단말, 일부 커스텀 기기)에서는 이 조건을 만족하지 못해 자동으로 폴백 뷰어를 씁니다.

## 빌드 방법
이 코드는 Android Studio(또는 Android SDK가 설치된 환경)에서 여는 것을 전제로 작성되었습니다. Gradle 래퍼(`gradlew`, `gradlew.bat`, `gradle/wrapper/*`)가 프로젝트에 포함되어 있어 Android Studio가 별도 생성 없이 바로 인식합니다.

1. Android Studio로 `mobile-viewer` 폴더를 엽니다("Open" → 이 폴더 선택).
2. "Trust Project" 확인 후 Gradle Sync가 자동으로 시작됩니다. **AGP 8.9.1 / Gradle 8.11.1 / Kotlin 2.1.20 / Room 2.7.1 / compileSdk 36 (extension 19) / minSdk 28 / targetSdk 34** 조합이며, 이 조합으로 CI에서 `assembleDebug`가 실제로 통과했습니다(맨 위 "빌드 성공 확인됨" 참고).
3. Sync가 끝나면 기기(안드로이드 9 Pie 이상, USB 디버깅 활성화) 또는 에뮬레이터를 선택해 ▶ Run(또는 `./gradlew assembleDebug`)으로 실행합니다.

### 빌드 환경 업그레이드 이력 (AGP/compileSdk/extension/Kotlin/Room)
`androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19`가 **AGP 8.9.1+, compileSdk 36+, SDK Extension 19+**를 요구한다는 게 확인되어 빌드 환경을 올렸고, 그 여파로 Kotlin·Room도 함께 올려야 했습니다(전부 GitHub Actions CI로 실제 컴파일까지 확인됨):

| 항목 | 이전 | 변경 후 | 변경 이유 |
|---|---|---|---|
| AGP | 8.6.0 | 8.9.1 | androidx.pdf alpha19 요구사항 |
| Gradle | 8.9 | 8.11.1 | AGP 8.9.x의 공식 최소 요구 버전 |
| compileSdk | 35 | 36 | androidx.pdf alpha19 요구사항 |
| compileSdkExtension | (미지정) | 19 | androidx.pdf alpha19 요구사항 |
| Kotlin | 1.9.24 | 2.1.20 | androidx.pdf alpha19가 Kotlin 2.1.0 메타데이터로 컴파일되어 있어, 이를 읽을 수 있는 컴파일러가 필요 |
| Room | 2.6.1 | 2.7.1 | Room 2.6.1의 kapt 프로세서가 Kotlin 2.1 메타데이터(버전 2.1.0)를 못 읽음(Kotlin 2.1.20으로 올린 데 따른 연쇄) |
| minSdk / targetSdk | 28 / 34 | 변경 없음 | — |

> **참고:** 이 버전 조합은 GitHub Actions CI(`.github/workflows/android-build.yml`)에서 `assembleDebug` 성공으로 실제 검증되었습니다 — [run 29810295767](https://github.com/kimroma457-cell/312da/actions/runs/29810295767). 이 세션의 샌드박스 자체는 여전히 Google Maven(`dl.google.com`) 등에 네트워크 접근이 막혀 있어 로컬 재현은 못 했지만, CI가 실제 인터넷 접근이 되는 GitHub 러너에서 돌기 때문에 이 결과는 추정이 아닌 실측입니다.
>
> - `androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19` 좌표 자체(버전 문자열)는 그대로 유지했습니다 — 이 라이브러리가 요구하는 환경 쪽을 맞추는 것이 목적이었기 때문입니다.
> - Release 빌드(`assembleRelease`)와 R8 난독화는 아직 CI에 포함되지 않아 미확인입니다.
> - hwplib·AndroidPdfViewer 관련 API(문단/표 구조, `getCurrentPage`/`jumpTo` 등)는 각 라이브러리의 GitHub 소스코드를 직접 읽어 확인했습니다.
> - `local.properties`(SDK 경로)는 Android Studio가 최초 오픈 시 자동 생성합니다 — `.gitignore`에 이미 제외 처리되어 있어 직접 만들 필요 없습니다.
