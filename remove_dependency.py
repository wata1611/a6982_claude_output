#!/usr/bin/env python3
"""
指定ライブラリへの依存を Claude API を使って除去する。

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    python3 remove_dependency.py <source_dir> [options]

Example:
    python3 remove_dependency.py \\
        CF_88comit_LibImpactResults/success/a698299490d70ce07b7af6e29ebf4627d412f4dd/original \\
        --group org.springframework \\
        --artifact spring-context \\
        --version 5.3.23 \\
        --output-dir ./claude_output
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

# --------------------------------------------------------------------------- #
# プロンプト構築
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """\
あなたはJavaのリファクタリングを行うエキスパートです。
指定されたライブラリへの依存を除去し、コンパイルが通る状態に修正してください。
出力は必ずJSON形式のみとし、余分な説明文は含めないでください。
"""

def build_user_prompt(files: dict[str, str], group: str, artifact: str, version: str) -> str:
    file_sections = "\n\n".join(
        f"### {name}\n```java\n{content}\n```"
        for name, content in files.items()
    )

    return f"""\
以下のJavaソースファイルから `{group}:{artifact}:{version}` ライブラリへの依存を除去してください。

## 除去方針
- このライブラリのimport文をすべて削除する
- このライブラリのアノテーション（@Component, @Service 等）を削除または代替する
- このライブラリのAPI（クラス・メソッド）への参照を削除または代替する
- コンパイルエラーが発生しないように修正する
- 変更は依存箇所の最小限にとどめる

## 入力ファイル

{file_sections}

## 出力形式（厳守）
以下のJSONスキーマで出力してください。JSONのみ出力し、コードブロックやMarkdownは不要です。

{{
  "files": {{
    "<ファイル名>": "<修正済みコード全体>",
    ...
  }},
  "summary": {{
    "<ファイル名>": ["変更点1", "変更点2", ...],
    ...
  }},
  "unchanged_files": ["変更不要だったファイル名", ...]
}}
"""


# --------------------------------------------------------------------------- #
# レスポンス解析
# --------------------------------------------------------------------------- #

def parse_response(text: str) -> dict:
    # JSON ブロック（```json ... ```）が混入した場合にも対応
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(text)


# --------------------------------------------------------------------------- #
# メイン処理
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Claude API を使ってJavaソースのライブラリ依存を除去する"
    )
    parser.add_argument("source_dir", help="Javaソースファイルが置かれたディレクトリ")
    parser.add_argument("--group",    default="org.springframework", help="groupId")
    parser.add_argument("--artifact", default="spring-context",      help="artifactId")
    parser.add_argument("--version",  default="5.3.23",              help="バージョン")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="修正ファイルの出力先（省略時は標準出力に表示）")
    parser.add_argument("--model", default="claude-sonnet-4-6",
                        help="使用するClaudeモデル (default: claude-sonnet-4-6)")
    args = parser.parse_args()

    # ソースファイル読み込み
    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"Error: {source_dir} はディレクトリではありません", file=sys.stderr)
        sys.exit(1)

    files: dict[str, str] = {}
    for java_file in sorted(source_dir.glob("*.java")):
        files[java_file.name] = java_file.read_text(encoding="utf-8")

    if not files:
        print("Javaファイルが見つかりませんでした。", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 対象ファイル: {', '.join(files.keys())}", file=sys.stderr)
    print(f"[INFO] 除去対象ライブラリ: {args.group}:{args.artifact}:{args.version}", file=sys.stderr)
    print(f"[INFO] モデル: {args.model}", file=sys.stderr)

    # Claude API 呼び出し
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY 環境変数が設定されていません", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("[INFO] Claude API を呼び出し中...", file=sys.stderr)
    message = client.messages.create(
        model=args.model,
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(
                    files, args.group, args.artifact, args.version
                ),
            }
        ],
    )

    raw_response = message.content[0].text

    # JSON 解析
    try:
        result = parse_response(raw_response)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSONの解析に失敗しました: {e}", file=sys.stderr)
        print("[RAW RESPONSE]", file=sys.stderr)
        print(raw_response, file=sys.stderr)
        sys.exit(1)

    # 結果出力
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, code in result.get("files", {}).items():
            out_path = output_dir / filename
            out_path.write_text(code, encoding="utf-8")
            print(f"[WRITE] {out_path}")

        # 変更サマリー表示
        print("\n--- 変更サマリー ---")
        for filename, changes in result.get("summary", {}).items():
            print(f"\n{filename}:")
            for change in changes:
                print(f"  - {change}")

        unchanged = result.get("unchanged_files", [])
        if unchanged:
            print(f"\n変更なし: {', '.join(unchanged)}")

    else:
        # 標準出力にJSON全体を整形して出力
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
