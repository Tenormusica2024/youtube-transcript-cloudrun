#!/usr/bin/env python3
"""
YouTube Transcript Extractor - アイコン自動生成スクリプト
SVGベースでPNGアイコンを生成（16, 32, 48, 128px）
"""

import io
import os

from PIL import Image, ImageDraw, ImageFont


def create_youtube_transcript_icon(size):
    """YouTube字幕抽出アイコンを生成"""

    # 背景色（YouTubeの赤）
    bg_color = "#FF0000"
    text_color = "#FFFFFF"

    # 画像作成
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 背景の角丸長方形
    corner_radius = size // 8
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)], radius=corner_radius, fill=bg_color
    )

    # アイコンのサイズに応じてフォントサイズ調整
    if size >= 128:
        # 大きいアイコン: 詳細な字幕アイコン
        draw_detailed_subtitle_icon(draw, size, text_color)
    elif size >= 48:
        # 中サイズ: 簡略字幕アイコン
        draw_medium_subtitle_icon(draw, size, text_color)
    else:
        # 小サイズ: シンプル文字アイコン
        draw_simple_text_icon(draw, size, text_color)

    return img


def draw_detailed_subtitle_icon(draw, size, color):
    """詳細な字幕アイコン（128px用）"""
    margin = size // 6

    # プレイヤー枠
    player_rect = [margin, margin, size - margin, size // 2]
    draw.rectangle(player_rect, outline=color, width=3)

    # 再生ボタン
    play_size = size // 8
    play_center = (size // 2, margin + (size // 2 - margin) // 2)
    play_points = [
        (play_center[0] - play_size // 2, play_center[1] - play_size // 2),
        (play_center[0] - play_size // 2, play_center[1] + play_size // 2),
        (play_center[0] + play_size // 2, play_center[1]),
    ]
    draw.polygon(play_points, fill=color)

    # 字幕行（3行）
    subtitle_y_start = size // 2 + margin // 2
    line_height = (size - subtitle_y_start - margin) // 4

    for i in range(3):
        y = subtitle_y_start + i * line_height
        # 行の長さを変える（自然な字幕のように）
        line_width = size - 2 * margin - (i * margin // 3)
        draw.rectangle(
            [margin, y, margin + line_width, y + line_height // 2], fill=color
        )


def draw_medium_subtitle_icon(draw, size, color):
    """中サイズ字幕アイコン（48px用）"""
    margin = size // 5

    # プレイヤー枠
    player_rect = [margin, margin, size - margin, size // 2]
    draw.rectangle(player_rect, outline=color, width=2)

    # 再生ボタン
    play_size = size // 10
    play_center = (size // 2, margin + (size // 2 - margin) // 2)
    play_points = [
        (play_center[0] - play_size // 2, play_center[1] - play_size // 2),
        (play_center[0] - play_size // 2, play_center[1] + play_size // 2),
        (play_center[0] + play_size // 2, play_center[1]),
    ]
    draw.polygon(play_points, fill=color)

    # 字幕行（2行）
    subtitle_y_start = size // 2 + margin // 3
    line_height = (size - subtitle_y_start - margin) // 3

    for i in range(2):
        y = subtitle_y_start + i * line_height
        line_width = size - 2 * margin - (i * margin // 4)
        draw.rectangle(
            [margin, y, margin + line_width, y + line_height // 3], fill=color
        )


def draw_simple_text_icon(draw, size, color):
    """シンプル文字アイコン（16-32px用）"""
    # "字" の文字を簡略化した図形で表現
    margin = size // 6

    # 縦線
    center_x = size // 2
    draw.rectangle([center_x - 1, margin, center_x + 1, size - margin], fill=color)

    # 横線 (3本)
    line_positions = [margin + size // 6, size // 2, size - margin - size // 6]

    for y in line_positions:
        draw.rectangle([margin, y - 1, size - margin, y + 1], fill=color)


def generate_all_icons():
    """全サイズのアイコンを生成"""
    sizes = [16, 32, 48, 128]
    icons_dir = os.path.dirname(os.path.abspath(__file__))

    print("YouTube字幕抽出アイコン生成開始...")

    for size in sizes:
        print(f"  {size}x{size}px アイコン生成中...")

        # アイコン生成
        icon = create_youtube_transcript_icon(size)

        # ファイル保存
        filename = f"icon-{size}.png"
        filepath = os.path.join(icons_dir, filename)
        icon.save(filepath, "PNG", optimize=True)

        print(f"  {filename} 保存完了")

    print("全アイコンファイル生成完了！")
    print(f"保存場所: {icons_dir}")

    # ファイル一覧確認
    print("\n生成されたファイル:")
    for size in sizes:
        filename = f"icon-{size}.png"
        filepath = os.path.join(icons_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"  OK {filename} ({file_size:,} bytes)")
        else:
            print(f"  NG {filename} (生成失敗)")


if __name__ == "__main__":
    try:
        generate_all_icons()
    except Exception as e:
        print(f"アイコン生成エラー: {e}")
        print("PIL（Pillow）がインストールされていない可能性があります")
        print("インストール: pip install Pillow")
