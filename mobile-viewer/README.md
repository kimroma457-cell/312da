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
