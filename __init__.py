import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import glob

class TextRenderNode:
    # クラス変数としてキャッシュ
    _font_cache = None
    
    @classmethod
    def get_font_family_name(cls, font_path):
        """フォントファイルからフォントファミリー名を取得（日本語優先）"""
        try:
            from fontTools import ttLib
            font = ttLib.TTFont(font_path)
            
            # name tableからフォント名を取得
            name_table = font['name']
            
            japanese_name = None
            english_name = None
            
            # フォントファミリー名を探す（nameID=1 または 16）
            for record in name_table.names:
                # nameID 16 = Typographic Family name (優先)
                # nameID 1 = Font Family name
                if record.nameID in [16, 1]:
                    try:
                        # 日本語名を探す (languageID 0x0411 = 日本語)
                        if record.platformID == 3 and record.langID == 0x0411:
                            japanese_name = record.string.decode('utf-16-be')
                        # 英語名を探す (languageID 0x0409 = 英語)
                        elif record.platformID == 3 and record.langID == 0x0409:
                            english_name = record.string.decode('utf-16-be')
                        # その他のWindows platform
                        elif record.platformID == 3 and english_name is None:
                            english_name = record.string.decode('utf-16-be')
                        # Mac platform
                        elif record.platformID == 1 and english_name is None:
                            english_name = record.string.decode('mac-roman')
                    except:
                        continue
            
            font.close()
            
            # 日本語名があれば日本語名を、なければ英語名を返す
            if japanese_name:
                return japanese_name
            elif english_name:
                return english_name
        except:
            pass
        
        # フォント名が取得できない場合はファイル名を返す
        return os.path.splitext(os.path.basename(font_path))[0]
    
    @classmethod
    def get_system_fonts(cls):
        """システムにインストールされているフォントを取得"""
        # キャッシュがあれば返す
        if cls._font_cache is not None:
            return cls._font_cache
        
        fonts = []
        
        if os.name == 'nt':  # Windows
            font_dirs = [
                "C:/Windows/Fonts/",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
            ]
        elif os.uname().sysname == 'Darwin':  # macOS
            font_dirs = [
                "/System/Library/Fonts/",
                "/Library/Fonts/",
                os.path.expanduser("~/Library/Fonts/")
            ]
        else:  # Linux
            font_dirs = [
                "/usr/share/fonts/",
                "/usr/local/share/fonts/",
                os.path.expanduser("~/.fonts/"),
                os.path.expanduser("~/.local/share/fonts/")
            ]
        
        # フォントファイルを検索
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF', '*.ttc', '*.TTC']:
                    fonts.extend(glob.glob(os.path.join(font_dir, '**', ext), recursive=True))
        
        # フォントファミリー名とパスのマッピングを作成
        font_mapping = {}
        for font_path in fonts:
            family_name = cls.get_font_family_name(font_path)
            # 重複する名前の場合はファイル名も追加
            display_name = family_name
            counter = 1
            while display_name in font_mapping:
                display_name = f"{family_name} ({counter})"
                counter += 1
            font_mapping[display_name] = font_path
        
        # フォント名をソート
        font_names = sorted(font_mapping.keys())
        
        # デフォルトフォントを追加
        if not font_names:
            font_names = ["default"]
            font_mapping = {"default": None}
        else:
            font_names.insert(0, "default")
            font_mapping["default"] = None
        
        cls._font_cache = (font_names, font_mapping)
        return cls._font_cache
    
    @classmethod
    def INPUT_TYPES(cls):
        font_names, _ = cls.get_system_fonts()
        
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello World"}),
                "font_size": ("INT", {"default": 48, "min": 8, "max": 500, "step": 1}),
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "font_name": (font_names, ),
                "text_color": (["white", "black", "red", "blue", "green", "yellow", "cyan", "magenta"], ),
                "bg_color": (["black", "white", "transparent", "red", "blue", "green", "gray"], ),
                "align": (["left", "center", "right"], ),
                "outline_width": ("INT", {"default": 0, "min": 0, "max": 20, "step": 1}),
                "outline_color": (["black", "white", "red", "blue", "green", "yellow", "cyan", "magenta"], ),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "render_text"
    CATEGORY = "image/text"

    def render_text(self, text, font_size, width, height, font_name, text_color, bg_color, align, outline_width, outline_color):
        # 背景色の設定
        color_map = {
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
            "red": (255, 0, 0, 255),
            "blue": (0, 0, 255, 255),
            "green": (0, 255, 0, 255),
            "yellow": (255, 255, 0, 255),
            "cyan": (0, 255, 255, 255),
            "magenta": (255, 0, 255, 255),
            "gray": (128, 128, 128, 255),
            "transparent": (0, 0, 0, 0),
        }
        
        # RGBA画像を作成
        if bg_color == "transparent":
            image = Image.new('RGBA', (width, height), color_map[bg_color])
        else:
            image = Image.new('RGBA', (width, height), color_map[bg_color])
        
        draw = ImageDraw.Draw(image)
        
        # フォントの読み込み
        try:
            _, font_mapping = self.get_system_fonts()
            
            if font_name == "default" or font_name not in font_mapping or font_mapping[font_name] is None:
                font = ImageFont.load_default()
            else:
                font_path = font_mapping[font_name]
                font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
            font = ImageFont.load_default()
        
        # テキストの位置計算
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 水平位置
        if align == "center":
            x = (width - text_width) // 2
        elif align == "right":
            x = width - text_width - 10
        else:  # left
            x = 10
        
        # 垂直位置(中央)
        y = (height - text_height) // 2
        
        # テキスト描画（アウトラインあり）
        if outline_width > 0:
            # アウトラインを描画
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), text, fill=color_map[outline_color], font=font)
        
        # メインテキストを描画
        draw.text((x, y), text, fill=color_map[text_color], font=font)
        
        # PIL ImageをComfyUI形式のテンソルに変換
        # ComfyUIはRGB形式を期待し、形状は [batch, height, width, channels]
        image_rgb = image.convert('RGB')
        image_np = np.array(image_rgb).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]
        
        return (image_tensor,)

NODE_CLASS_MAPPINGS = {
    "TextRenderNode": TextRenderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextRenderNode": "Render Text to Image"
}