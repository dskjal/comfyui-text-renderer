# ComfyUI Text Renderer
Text render node for ComfyUI

![screenshot](assets/screenshot.png)

fonttools required if you want to show font names instead of font file name.

```
python_embeded\python -m pip install fonttools
```

See this blog for details(In Japanese).  
https://nowokay.hatenablog.com/entry/2026/01/05/110344

## パラメータ

|項目|説明|
|:---:|:---|
|extract_double_quoted_text|二重引用符で囲んだテキストのみレンダリングする。<br/>プロンプトからテキストのみを抜き出す手間がなくなる|
|direction|horizontal で横書き<br/>vertical で縦書き|
