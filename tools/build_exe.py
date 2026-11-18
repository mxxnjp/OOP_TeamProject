"""게임을 실행 파일(.exe) 하나로 묶는 도구 (PyInstaller).

사용법 (maze_runner 폴더에서):
    pip install -r requirements-dev.txt      (처음 한 번)
    python tools/build_exe.py

결과: dist/HUFS_RUN.exe  ← 이 파일 하나만 있으면 파이썬이 없는 컴퓨터에서도 더블클릭으로 실행
- assets/ 폴더(그림)는 .exe 안에 같이 묶임 (themes.ASSET_DIR이 실행 중 임시 폴더에서 찾음)
- 콘솔(검은 창) 없이 게임 창만 뜸. 오류를 보고 싶으면: python tools/build_exe.py --console
- build/ dist/ 폴더는 .gitignore에 들어 있어서 GitHub에 안 올라감 (.exe는 따로 전달)
"""
import os
import sys

import PyInstaller.__main__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "HUFS_RUN"


def main():
    os.chdir(ROOT)
    args = [
        "main.py",
        "--name", NAME,
        "--onefile",                                         # .exe 파일 하나로
        # 그림 폴더 같이 묶기 (설정 파일을 build/spec에 두므로 경로는 절대 경로로)
        "--add-data", f"{os.path.join(ROOT, 'assets')}{os.pathsep}assets",
        "--noconfirm", "--clean",                            # 이전 결과 덮어쓰기
        "--specpath", os.path.join("build", "spec"),         # 설정 파일(.spec)도 build/ 안에
    ]
    if "--console" not in sys.argv:
        args.append("--windowed")                            # 검은 콘솔 창 안 띄움
    PyInstaller.__main__.run(args)
    print(f"\n완성: {os.path.join(ROOT, 'dist', NAME + '.exe')}")


if __name__ == "__main__":
    main()
