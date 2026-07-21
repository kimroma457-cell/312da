# PDF·HWP 뷰어 (Android)

기기에 저장된 PDF/HWP 파일을 열거나, 다른 앱의 "공유" 메뉴에서 파일을 받아 바로 볼 수 있는 안드로이드 앱입니다.

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
   - Room DB에 문서 Uri별로 저장. 목록 다이얼로그에서 탭하면 해당 위치로 이동, 삭제 가능.
   - PDF는 폴백 뷰어(`PDF_LEGACY`)에서만 지원합니다 — 공식 `androidx.pdf` 뷰어는 현재 페이지를 읽는 공개 API를 확인하지 못해 그 경로에서는 북마크 버튼을 숨겼습니다.
   - HWP는 스크롤 Y 좌표를 저장합니다(문단 단위가 아님).
   - JSON 내보내기/가져오기는 이번 범위에서 제외했습니다(요청 시 추가 가능).

## 다음에 확인할 것: 공식 androidx.pdf 뷰어 북마크 지원
공식 `PdfViewerFragment`는 `onPdfViewCreated(pdfView: PdfView)` 콜백을 노출하는 것으로 보입니다. Android Studio에서 Gradle sync가 끝난 뒤, `PdfView`의 **공개 API**에 현재 표시 페이지 또는 가시 페이지 범위를 읽을 방법이 있는지 확인해 주세요.

- 공식 공개 API로 확인되면: `TrackingPdfViewerFragment`에 `onPdfViewCreated` 오버라이드를 추가해 위치를 읽고, `ViewerActivity.getCurrentPosition()` / `jumpToPosition()`을 `Mode.PDF_FRAGMENT`에도 연결한 뒤 `bookmarkAddButton`/`bookmarkListButton` 숨김을 해제하면 됩니다.
- 공개 API로 확인되지 않으면: 리플렉션이나 내부(non-public) API로 우회하지 말고, 현재처럼 이 경로에서는 북마크 버튼을 숨긴 채로 둡니다.

해당 지점은 `ViewerActivity.showPdfWithFragment()`와 `TrackingPdfViewerFragment.kt`의 TODO 주석에 표시해 두었습니다.

## 1차 PDF 기능 검증 결과

**이 검증은 코드 리뷰로만 수행되었고, 실제 기기/에뮬레이터 테스트는 수행되지 않았습니다.** 이 세션의 샌드박스에는 Android SDK, 에뮬레이터, 실기기가 없고 Google Maven(`dl.google.com`)을 포함한 구글 소유 도메인 전체가 네트워크 차단되어 있어 Gradle Sync, Debug/Release 빌드, 앱 실행 자체가 불가능합니다. 아래는 항목별로 실제로 무엇을 했고 무엇이 남았는지입니다.

| # | 항목 | 상태 |
|---|------|------|
| 1 | Gradle Sync로 `androidx.pdf`/Room/기존 PDF 뷰어 의존성 해결 확인 | **미수행.** 이 환경에서 Google Maven에 접근할 수 없어 실행 자체가 불가능. Android Studio에서 최초 sync 시 확인 필요 — 특히 `androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19` 좌표. |
| 2 | Debug/Release 빌드, 컴파일 오류·경고·중복 의존성·난독화 오류 확인 | **미수행(빌드 불가).** 대신 전체 소스를 다시 읽으며 정적 검토했고, 실제 컴파일 오류 1건을 발견해 수정함: `ViewerActivity.openFile()`에서 `HWP_MIME_TYPES.contains(mimeType)`에 nullable `String?`을 넘겨 타입 불일치가 나던 부분(`mimeType != null && mimeType in HWP_MIME_TYPES`로 수정). Release 난독화(R8) 동작은 실제 빌드 없이는 확인 불가. |
| 3 | 실기기 PDF 유형별 테스트(일반 텍스트/스캔 이미지/100p+/한영 혼합/암호·손상/공유받은 파일) | **미수행.** 기기가 없어 어떤 PDF도 열어보지 못했습니다. |
| 4 | 검색 결과 이동·하이라이트 위치 정확성 | **미수행.** HWP 쪽 `WebView.findAllAsync`/`findNext`는 표준 플랫폼 API라 동작 자체는 신뢰하지만 실제 하이라이트 좌표는 기기에서 봐야 확인됩니다. PDF 쪽은 `androidx.pdf`의 내장 검색 UI라 저희 코드가 하이라이트를 직접 그리지 않습니다. |
| 5 | 앱 완전 종료 후 재실행 시 북마크·메모 유지 | **코드로는 보장됨, 기기 검증은 안 됨.** Room DB는 `docviewer.db` 파일로 디스크에 저장되고 앱 재시작과 무관하게 유지되는 것이 Room의 표준 동작입니다. 단, 공유로 받은 파일은 URI 권한이 만료되어 그 문서를 다시 열지 못할 수 있음(아래 "알려진 제약" 참고) — 이 경우도 앱이 크래시하지 않고 "다시 선택하기" 안내가 뜨도록 이번에 수정했습니다(#8 참고). |
| 6 | 북마크 목록에서 정확한 페이지 이동, 수정·삭제 정상 동작 | **코드 경로는 존재, 기기 검증은 안 됨.** 이동은 `pdfView.jumpTo()`/`webView.scrollTo()`(둘 다 소스로 시그니처 확인됨), 삭제는 Room `@Delete` 후 목록 갱신. "수정"은 현재 미구현입니다 — 요청하신 항목엔 있었지만 이전 구현에 메모 수정 기능 자체가 없었습니다(삭제 후 재추가만 가능). 필요하시면 별도로 추가하겠습니다. |
| 7 | 같은 파일명/경로가 달라도 북마크가 잘못 연결되지 않는지 | **코드 검토로 확인.** 북마크는 파일명이 아니라 전체 content Uri 문자열(`uri.toString()`)로 키를 잡습니다. 서로 다른 Uri는 절대 같은 키로 매핑되지 않으므로, 이름이 같은 두 파일이나 같은 파일을 다른 앱/경로로 연 경우 모두 별도 버킷으로 분리됩니다(반대로 말하면 "물리적으로 같은 파일"이어도 Uri가 다르면 북마크가 자동으로 합쳐지지는 않습니다 — 안전한 쪽으로 치우친 설계). |
| 8 | 공유 URI 권한 만료 시 크래시 없이 재선택 안내 | **이번에 수정함.** 기존 코드는 `openFile()` 초반의 `contentResolver.getType()`/파일명 조회가 try/catch 없이 호출되어 `SecurityException` 발생 시 크래시할 수 있었습니다. 이번에 `openFile()`, `showPdfLegacy`의 `onError`, `showPdfWithFragment`의 로드 실패 콜백, `showHwp`의 스트림 열기 각각에서 `SecurityException`을 구분해 잡고, "공유받은 파일에 대한 접근 권한이 만료되었습니다. 파일을 다시 선택해주세요." 메시지와 "다시 선택하기" 버튼(MainActivity로 이동)을 보여주도록 했습니다. 다만 AndroidPdfViewer의 내부 오류 전달 경로(`DecodingAsyncTask` → `loadError()` → `onError`)는 소스코드로 확인했지만, 실제 만료된 URI로 어떤 예외가 도달하는지는 기기 테스트 없이는 100% 장담할 수 없습니다. |
| 9 | 회전/백그라운드 복귀/다크모드/저사양 기기에서 페이지·상태 비정상 초기화 없음 | **부분적으로 수정함.** ① 회전: 매니페스트에 `configChanges="orientation\|screenSize\|keyboardHidden"`이 이미 있어 Activity가 재생성되지 않음(기존 그대로). ② 다크모드 전환은 `uiMode` configChange가 빠져 있어 테마 변경 시 Activity가 재생성되고 상태가 날아갈 수 있었던 버그를 발견 — `uiMode`를 추가해 수정함. ③ 백그라운드 복귀는 프로세스가 죽지 않는 한 Android가 Activity를 재생성하지 않으므로 원래도 문제없음(OS 표준 동작, 별도 수정 불필요). ④ 저사양 기기의 백그라운드 프로세스 강제 종료(process death) 후 복원은 기존에 전혀 대비가 없었던 부분이라 `onSaveInstanceState`/`onCreate(savedInstanceState)`로 현재 Uri와 페이지/스크롤 위치를 저장·복원하도록 추가했습니다. `androidx.pdf` 경로는 현재 페이지를 읽는 공개 API가 확인되지 않아 이 복원 대상에서 제외됩니다(위 TODO와 동일한 제약). 이 동작 자체가 실기기에서 의도대로 작동하는지는 검증되지 않았습니다. |
| 10 | 결과를 README에 정리 | 이 섹션이 그 결과입니다. |

**요약:** 기기/빌드 검증(#1–6, #10 일부)은 이 환경의 근본적 제약으로 수행할 수 없었습니다. 대신 코드 정적 검토를 통해 컴파일 오류 1건(#2)과 다크모드 상태 손실 버그(#9)를 실제로 찾아 고쳤고, URI 권한 만료 크래시 방지(#8)와 프로세스 종료 후 상태 복원(#9)을 새로 구현했습니다. #6의 "메모 수정" 기능은 아직 없습니다. 실제 기기 테스트는 Android Studio에서 앱을 빌드해 진행해 주셔야 합니다.

## 알려진 제약
- **북마크 지속성**: 다른 앱의 "공유"로 받은 파일은 보통 임시 URI 권한이라 앱을 재시작하면 그 파일의 URI가 무효화될 수 있습니다 — 이 경우 저장된 북마크가 있어도 파일을 다시 열 수 없습니다. 앱 내 "파일 열기" 버튼(SAF)으로 연 파일은 영구 권한을 요청하므로 재시작 후에도 안정적으로 열립니다.
- **HWP 표시 한계**: 글자 단위 서식(굵기/기울임/색상)과 이미지는 재현되지 않고, 문단·표 구조와 텍스트만 표시됩니다.
- **androidx.pdf 가용성**: 구글 플레이 시스템 업데이트(Mainline) 확장 모듈이 낮은 기기(구형 단말, 일부 커스텀 기기)에서는 이 조건을 만족하지 못해 자동으로 폴백 뷰어를 씁니다.

## 빌드 방법
이 코드는 Android Studio(또는 Android SDK가 설치된 환경)에서 여는 것을 전제로 작성되었습니다.

1. Android Studio로 `mobile-viewer` 폴더를 엽니다.
2. Gradle sync가 끝나면 (Android Studio가 wrapper를 자동 생성합니다) 기기/에뮬레이터에서 실행합니다.

> **참고:** 이 코드를 작성한 샌드박스 환경은 Android SDK와 Google의 Maven 저장소(`dl.google.com`, `android.googlesource.com` 포함)에 대한 네트워크 접근이 전부 막혀 있어, 실제 컴파일/실행 검증을 하지 못했습니다.
>
> - `androidx.pdf:pdf-viewer-fragment:1.0.0-alpha19` 좌표는 Android Developers 문서에서 인용된 조각들로 구성한 것이라 **정확한 artifactId/버전을 이 자리에서 확인하지 못했습니다.** Android Studio에서 Gradle sync 시 [공식 릴리스 노트](https://developer.android.com/jetpack/androidx/releases/pdf)와 대조해 주세요.
> - 같은 이유로 `minSdk`를 24→28로 올렸지만, 실제 라이브러리 매니페스트가 더 높은 minSdk(31)를 요구하면 빌드 시 명확한 병합 오류가 뜹니다 — 그 경우 오류 메시지가 알려주는 값으로 올리면 됩니다.
> - hwplib·AndroidPdfViewer 관련 API(문단/표 구조, `getCurrentPage`/`jumpTo` 등)는 각 라이브러리의 GitHub 소스코드를 직접 읽어 확인했습니다.
