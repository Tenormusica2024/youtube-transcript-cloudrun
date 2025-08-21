#!/usr/bin/env python3
"""
YouTube字幕抽出機能テストスクリプト
"""

import sys
import traceback


def test_imports():
    """依存関係のインポートテスト"""
    try:
        print("=== 依存関係テスト ===")

        import flask

        print(f"✅ Flask: {flask.__version__}")

        import youtube_transcript_api

        print(f"✅ YouTube Transcript API: インポート成功")

        import requests

        print(f"✅ Requests: インポート成功")

        import qrcode

        print(f"✅ QRCode: インポート成功")

        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        traceback.print_exc()
        return False


def test_transcript_extraction():
    """字幕抽出テスト"""
    try:
        print("\n=== 字幕抽出テスト ===")
        from youtube_transcript_api import YouTubeTranscriptApi

        # テスト用動画ID（日本語字幕付き）
        video_id = "jNQXAC9IVRw"
        print(f"テスト動画ID: {video_id}")

        # 利用可能な字幕の取得
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("✅ 字幕リスト取得成功")

        # 利用可能な言語を表示
        available_languages = []
        for transcript in transcript_list:
            available_languages.append(transcript.language_code)
        print(f"利用可能な言語: {available_languages}")

        # 日本語字幕を試行
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja"])
            if transcript:
                print(f"✅ 日本語字幕取得成功: {len(transcript)}セグメント")
                # 最初の3セグメントを表示
                for i, segment in enumerate(transcript[:3]):
                    print(f"  [{i+1}] {segment['text']}")
                return True
        except Exception as e:
            print(f"⚠️  日本語字幕エラー: {e}")

        # 英語字幕を試行
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            if transcript:
                print(f"✅ 英語字幕取得成功: {len(transcript)}セグメント")
                return True
        except Exception as e:
            print(f"⚠️  英語字幕エラー: {e}")

        # 自動生成字幕を試行
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            if transcript:
                print(f"✅ 自動字幕取得成功: {len(transcript)}セグメント")
                return True
        except Exception as e:
            print(f"❌ 自動字幕エラー: {e}")

        return False

    except Exception as e:
        print(f"❌ 字幕抽出テストエラー: {e}")
        traceback.print_exc()
        return False


def test_api_endpoint():
    """APIエンドポイントテスト"""
    try:
        print("\n=== APIエンドポイントテスト ===")
        import json

        import requests

        # ローカルサーバーをチェック
        try:
            response = requests.get("http://127.0.0.1:8085/health", timeout=5)
            if response.status_code == 200:
                print("✅ サーバー稼働中")

                # 字幕抽出APIテスト
                api_data = {
                    "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
                    "lang": "ja",
                }

                api_response = requests.post(
                    "http://127.0.0.1:8085/api/extract", json=api_data, timeout=30
                )

                if api_response.status_code == 200:
                    result = api_response.json()
                    if result.get("success"):
                        print("✅ API字幕抽出成功")
                        print(f"   タイトル: {result.get('title', 'N/A')}")
                        print(f"   字幕長: {len(result.get('transcript', ''))}")
                        return True
                    else:
                        print(f"❌ API字幕抽出失敗: {result.get('error')}")
                else:
                    print(f"❌ APIエラー: {api_response.status_code}")
                    print(f"   レスポンス: {api_response.text}")
            else:
                print(f"❌ サーバー応答エラー: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("⚠️  サーバーが起動していません")
        except requests.exceptions.Timeout:
            print("⚠️  サーバー応答タイムアウト")

        return False

    except Exception as e:
        print(f"❌ APIテストエラー: {e}")
        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("YouTube字幕抽出ツール - 診断テスト")
    print("=" * 50)

    results = []

    # テスト実行
    results.append(("依存関係", test_imports()))
    results.append(("字幕抽出", test_transcript_extraction()))
    results.append(("APIエンドポイント", test_api_endpoint()))

    # 結果サマリー
    print("\n" + "=" * 50)
    print("=== テスト結果サマリー ===")

    success_count = 0
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1

    print(
        f"\n成功率: {success_count}/{len(results)} ({100*success_count//len(results)}%)"
    )

    if success_count == len(results):
        print("🎉 全テスト成功！")
    else:
        print("⚠️  一部テストが失敗しました。")

    return success_count == len(results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  テスト中断")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        traceback.print_exc()
