import re

import unicodedata


class TextCleaner:
    """RAG 文档文本清洗器，一键 clean()"""

    HEADING_PATTERN = re.compile(r"^第[一二三四五六七八九十百千零0-9]+(条|节|章|编|款|部分)")
    BOILER_PATTERNS = [
        re.compile(r"^\s*[-—–]?\s*\d+\s*[-—–]?\s*$"),
        re.compile(r"^\s*第\s*\d+\s*页\s*共\s*\d+\s*页\s*$"),
        re.compile(r"^\s*Copyright|©|版权所有|All Rights Reserved\s*$", re.I),
    ]

    def __init__(self, merge_short_lines=True, heading_pattern=None):
        self.merge_short_lines = merge_short_lines
        self.heading_pattern = heading_pattern or self.HEADING_PATTERN

    def normalize_unicode(self, text):
        return unicodedata.normalize("NFKC", text)

    def basic_clean(self, text):
        text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\u3000", " ")
        text = "".join(ch for ch in text if ch in "\n\t"
                       or not unicodedata.category(ch).startswith("C"))
        return text

    def fix_hyphenation(self, text):
        return re.sub(r"([a-zA-Z])-\n([a-zA-Z])", r"\1\2", text)

    def remove_boilerplate(self, text):
        kept = []
        for line in text.split("\n"):
            s = line.strip()
            if not s or any(p.match(s) for p in self.BOILER_PATTERNS):
                continue
            kept.append(line)
        return "\n".join(kept)

    def _merge_short_lines(self, text):
        result, buf = [], ""
        for line in [l.strip() for l in text.split("\n")]:
            if not line:
                continue
            if self.heading_pattern.match(line):
                if buf: result.append(buf)
                buf = line
            else:
                buf += line
        if buf: result.append(buf)
        return "\n\n".join(result)

    def clean_cjk_spaces(self, text):
        prev = None
        while prev != text:
            prev = text
            text = re.sub(r"([\u4e00-\u9fa5])[ \t]+([\u4e00-\u9fa5])", r"\1\2", text)
        text = re.sub(r"([\u4e00-\u9fa5])[ \t]+([，。；：、！？（）《》])", r"\1\2", text)
        text = re.sub(r"([，。；：、！？（）《》])[ \t]+([\u4e00-\u9fa5])", r"\1\2", text)
        return re.sub(r"[ \t]{2,}", " ", text)

    def compress_blank_lines(self, text):
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def clean(self, text):
        text = self.normalize_unicode(text)
        text = self.basic_clean(text)
        text = self.fix_hyphenation(text)
        text = self.remove_boilerplate(text)
        if self.merge_short_lines:
            text = self._merge_short_lines(text)
        text = self.clean_cjk_spaces(text)
        text = self.compress_blank_lines(text)
        return text
