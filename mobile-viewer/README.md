# PDF·HWP 뷰어 (Android)

기기에 저장된 PDF/HWP 파일을 열거나, 다른 앱의 "공유" 메뉴에서 파일을 받아 바로 볼 수 있는 안드로이드 앱입니다.

## 구성
- `MainActivity` — 파일 선택 버튼(SAF `ACTION_OPEN_DOCUMENT`)
- `ViewerActivity` — 다른 앱의 공유(`ACTION_SEND`)/열기(`ACTION_VIEW`) 요청을 받는 진입점이자 뷰어 화면
  - PDF: [AndroidPdfViewer](https://github.com/mhiew/AndroidPdfViewer) (`com.github.mhiew:android-pdf-viewer`)로 렌더링
  - HWP: [hwplib](https://github.com/neolord0/hwplib) (`kr.dogfoot:hwplib`)로 파싱 후 문단/표 구조를 HTML로 변환해 WebView에 표시

## HWP 표시 관련 제약
HWP는 비공개 바이너리 포맷이라 공식 안드로이드 라이브러리가 없습니다. `hwplib`로 문단과 표 구조는 재현하지만, 글자 단위 서식(굵기/기울임/색상)과 이미지는 표시되지 않습니다. 변환 중 오류가 나면 순수 텍스트 추출로 자동 폴백합니다.

## 빌드 방법
이 코드는 Android Studio(또는 Android SDK가 설치된 환경)에서 여는 것을 전제로 작성되었습니다.

1. Android Studio로 `mobile-viewer` 폴더를 엽니다.
2. Gradle sync가 끝나면 (Android Studio가 wrapper를 자동 생성합니다) 기기/에뮬레이터에서 실행합니다.

> **참고:** 이 코드를 작성한 샌드박스 환경은 Android SDK와 Google의 Maven 저장소(`dl.google.com`)에 대한 네트워크 접근이 막혀 있어, 이 자리에서 실제 컴파일/실행 검증을 하지 못했습니다. AndroidX, AGP, `androidx.activity` 등 Google Maven 의존성은 Android Studio에서 정상적으로 받아지지만, 실제 빌드에서 사소한 API 시그니처 차이가 발견될 수 있습니다.
