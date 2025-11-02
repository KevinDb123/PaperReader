# PaperReader
A PaperReader for scientific papers

由于pdf识别库比较简略，目前基本上只能识别单栏的pdf，文章也不能太长。

使用方式：
在终端，进入虚拟环境

```
pip install -r requiresment.txt
uvicorn main:app --reload
```

即可运行，然后打开index.html就可以使用。
