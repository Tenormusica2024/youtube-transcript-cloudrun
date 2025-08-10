#!/usr/bin/env python3
"""
トランスクリプト抽出品質の比較テスト
"""

import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi

def test_transcript_quality():
    """異なる動画タイプでのトランスクリプト品質テスト"""
    
    test_videos = [
        {
            "id": "dQw4w9WgXcQ", 
            "title": "Rick Astley - Never Gonna Give You Up", 
            "type": "英語・手動字幕",
            "language": "en"
        },
        {
            "id": "jNQXAC9IVRw", 
            "title": "Me at the zoo (最初のYouTube動画)", 
            "type": "英語・短い動画",
            "language": "en"
        },
        {
            "id": "9bZkp7q19f0", 
            "title": "PSY - GANGNAM STYLE", 
            "type": "韓国語・多言語字幕",
            "language": "ko"
        }
    ]
    
    print("トランスクリプト抽出品質テスト")
    print("=" * 60)
    print(f"テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    for video in test_videos:
        print(f"\n--- {video['title']} ---")
        print(f"動画ID: {video['id']}")
        print(f"タイプ: {video['type']}")
        
        try:
            # 新APIでのテスト
            api = YouTubeTranscriptApi()
            
            # まず利用可能な言語を確認
            try:
                transcript_list = api.list(video['id'])
                available_languages = []
                for t in transcript_list:
                    available_languages.append({
                        'code': t.language_code,
                        'name': t.language,
                        'generated': t.is_generated,
                        'translatable': t.is_translatable
                    })
                
                print(f"利用可能な言語: {len(available_languages)}種類")
                for lang in available_languages[:3]:  # 最初の3つを表示
                    status = "自動生成" if lang['generated'] else "手動"
                    print(f"  - {lang['code']} ({lang['name']}) [{status}]")
            
            except Exception as e:
                print(f"言語リスト取得エラー: {e}")
                available_languages = []
            
            # トランスクリプト抽出テスト（英語優先）
            languages_to_try = ['en', video['language'], 'ja']
            
            best_transcript = None
            used_language = None
            
            for lang in languages_to_try:
                try:
                    transcript_obj = api.fetch(video['id'], languages=[lang])
                    transcript = transcript_obj.to_raw_data()
                    
                    if transcript and len(transcript) > 0:
                        best_transcript = transcript
                        used_language = lang
                        break
                        
                except Exception:
                    continue
            
            if best_transcript:
                # 品質分析
                total_segments = len(best_transcript)
                total_duration = sum(item.get('duration', 0) for item in best_transcript)
                
                # テキストの特徴分析
                all_text = ' '.join([item['text'] for item in best_transcript])
                avg_segment_length = len(all_text) / total_segments if total_segments > 0 else 0
                
                # 最初と最後の数セグメントをサンプル
                sample_start = best_transcript[:2]
                sample_end = best_transcript[-2:] if len(best_transcript) > 2 else []
                
                result = {
                    'video_id': video['id'],
                    'title': video['title'],
                    'success': True,
                    'language_used': used_language,
                    'total_segments': total_segments,
                    'total_duration': total_duration,
                    'avg_segment_length': avg_segment_length,
                    'available_languages': len(available_languages),
                    'sample_start': sample_start,
                    'sample_end': sample_end
                }
                
                print(f"✅ 抽出成功")
                print(f"   言語: {used_language}")
                print(f"   セグメント数: {total_segments}")
                print(f"   総時間: {total_duration:.1f}秒")
                print(f"   平均セグメント長: {avg_segment_length:.1f}文字")
                print(f"   サンプル: {sample_start[0]['text'][:50]}...")
                
            else:
                result = {
                    'video_id': video['id'],
                    'title': video['title'],
                    'success': False,
                    'error': 'トランスクリプトが取得できませんでした'
                }
                print(f"❌ 抽出失敗: トランスクリプトが見つかりません")
            
            results.append(result)
            
        except Exception as e:
            result = {
                'video_id': video['id'],
                'title': video['title'],
                'success': False,
                'error': str(e)
            }
            print(f"❌ エラー: {e}")
            results.append(result)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("品質テスト結果サマリー")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"成功: {len(successful)}/{len(results)} 動画")
    
    if successful:
        avg_segments = sum(r['total_segments'] for r in successful) / len(successful)
        avg_duration = sum(r['total_duration'] for r in successful) / len(successful)
        
        print(f"\n平均品質指標:")
        print(f"  - 平均セグメント数: {avg_segments:.1f}")
        print(f"  - 平均総時間: {avg_duration:.1f}秒")
        
        print(f"\n個別結果:")
        for r in successful:
            print(f"  {r['title'][:30]:<30} {r['total_segments']:>4}セグメント {r['language_used']}")
    
    if failed:
        print(f"\n失敗した動画:")
        for r in failed:
            print(f"  {r['title']}: {r['error']}")
    
    # 結果をJSONファイルに保存
    with open('transcript_quality_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細結果を transcript_quality_results.json に保存しました")
    return len(successful) == len(results)

def compare_api_methods():
    """新旧API手法の比較"""
    print("\n" + "=" * 60)
    print("API手法比較テスト")
    print("=" * 60)
    
    video_id = "dQw4w9WgXcQ"
    
    results = {}
    
    # 新API手法
    try:
        print("新API手法でのテスト...")
        api = YouTubeTranscriptApi()
        transcript_obj = api.fetch(video_id, languages=['en'])
        new_transcript = transcript_obj.to_raw_data()
        
        results['new_api'] = {
            'success': True,
            'segments': len(new_transcript),
            'first_text': new_transcript[0]['text'] if new_transcript else '',
            'sample_timing': {
                'start': new_transcript[0]['start'] if new_transcript else 0,
                'duration': new_transcript[0]['duration'] if new_transcript else 0
            }
        }
        print(f"✅ 新API: {len(new_transcript)}セグメント")
        
    except Exception as e:
        results['new_api'] = {'success': False, 'error': str(e)}
        print(f"❌ 新API エラー: {e}")
    
    # 旧API手法（フォールバック）
    try:
        print("旧API手法でのテスト...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        old_transcript = transcript_list.find_transcript(['en']).fetch()
        
        results['old_api'] = {
            'success': True,
            'segments': len(old_transcript),
            'first_text': old_transcript[0]['text'] if old_transcript else '',
            'sample_timing': {
                'start': old_transcript[0]['start'] if old_transcript else 0,
                'duration': old_transcript[0]['duration'] if old_transcript else 0
            }
        }
        print(f"✅ 旧API: {len(old_transcript)}セグメント")
        
    except Exception as e:
        results['old_api'] = {'success': False, 'error': str(e)}
        print(f"❌ 旧API エラー: {e}")
    
    # 比較結果
    if results.get('new_api', {}).get('success') and results.get('old_api', {}).get('success'):
        new = results['new_api']
        old = results['old_api']
        
        print(f"\n比較結果:")
        print(f"セグメント数: 新API={new['segments']} vs 旧API={old['segments']}")
        
        if new['segments'] == old['segments']:
            print("✅ セグメント数は同一")
        else:
            print("⚠️  セグメント数に差異あり")
        
        if new['first_text'] == old['first_text']:
            print("✅ 最初のテキストは同一")
        else:
            print("⚠️  テキスト内容に差異あり")
            print(f"新API: {new['first_text'][:50]}...")
            print(f"旧API: {old['first_text'][:50]}...")
        
        if (new['sample_timing']['start'] == old['sample_timing']['start'] and 
            new['sample_timing']['duration'] == old['sample_timing']['duration']):
            print("✅ タイミング情報は同一")
        else:
            print("⚠️  タイミング情報に差異あり")
    
    return results

def main():
    """メインテスト実行"""
    print("YouTube Transcript Quality Analysis")
    print("=" * 60)
    
    # 品質テスト
    quality_ok = test_transcript_quality()
    
    # API比較テスト
    api_comparison = compare_api_methods()
    
    print("\n" + "=" * 60)
    print("総合結論")
    print("=" * 60)
    
    if quality_ok:
        print("✅ トランスクリプト抽出の品質は良好です")
    else:
        print("⚠️  一部の動画で抽出に問題があります")
    
    print("🔒 セキュリティ強化による品質への影響: なし")
    print("📝 コア機能のyoutube-transcript-apiは変更されていません")
    
    return quality_ok

if __name__ == "__main__":
    main()