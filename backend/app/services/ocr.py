"""
OCR识别服务 - 使用Tesseract识别跑步截图数据
支持高驰(CorOS)、佳明(Garmin)、华为(Huawei Health)等截图
"""

import re
import os
from typing import Optional
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


@dataclass
class RunningData:
    distance: Optional[float] = None
    time: Optional[str] = None
    date: Optional[str] = None
    heart_rate: Optional[int] = None
    raw_text: Optional[str] = None
    success: bool = False
    error_msg: Optional[str] = None


class ImagePreprocessor:
    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> Image.Image:
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        width, height = image.size
        if width < 800:
            new_size = (int(width * 1.5), int(height * 1.5))
            image = image.resize(new_size, Image.LANCZOS)

        gray = image.convert('L')
        denoised = gray.filter(ImageFilter.MedianFilter(size=3))
        enhancer = ImageEnhance.Contrast(denoised)
        high_contrast = enhancer.enhance(3.0)

        import numpy as np
        img_array = np.array(high_contrast)
        threshold = np.mean(img_array)
        binary_array = (img_array > threshold).astype(np.uint8) * 255
        binary = Image.fromarray(binary_array)
        sharpened = ImageEnhance.Sharpness(binary).enhance(2.0)

        return sharpened


class DataExtractor:
    DISTANCE_PATTERNS = [
        r"(\d+\.?\d*)\s*[kK][mM](?![a-zA-Z])",
        r"(\d+\.?\d*)[^\d]*[kK][nN](?![a-zA-Z])",
        r"(\d+\.?\d*)[^\d]*[kK][iI](?![a-zA-Z])",
        r"(\d+\.?\d*)[^\d]*[iI][nN](?![a-zA-Z])",
        r"(\d+\.?\d*)[^\d]*[kK](?![a-zA-Z])",
        r"(\d+\.\d{2})[\.⋯·…]+\s*[iI](?![a-zA-Z])",
        r"(\d+\.?\d*)\s*公里",
        r"距离[：:\s]*(\d+\.?\d*)",
        r"总距离[：:\s]*(\d+\.?\d*)",
        r"里程[：:\s]*(\d+\.?\d*)",
        r"跑了\s*(\d+\.?\d*)",
        r"(\d+\.?\d*)\s*['\"]?\s*[@]?\s*[kK][mM]?\s*[目,，]?\s*[,.]?",
        r"(\d+\.\d{2})\s*['\"]?\s*[@]?\s*[kK]\s*[mM]?\s*[目,，]?",
        r"(\d+\.?\d*)\s*['\"]",
        # un是km的OCR误识别
        r"(\d+\.?\d*)\s*[uU][nN]",
        # i是km的OCR误识别（如1.19 i. 实际是1.19km）
        r"(\d+\.\d{2})\s*[iI]\s*[.,。]?(?!\d)",
        r"(\d+\.\d{2})[iI](?![a-zA-Z])",
        # 余是km的OCR误识别（如21.12 余 实际是21.12km）
        r"(\d+\.\d{2})\s*余(?![员])",
        r"(\d+\.\d{2})余(?![员])",
    ]

    TIME_PATTERNS = [
        r'(\d{1,2}):(\d{2}):(\d{2})(?!\d)',
        r'(\d{1,2})[":](\d{2})[":](\d{2})(?!\d)',
        r'用时[：:]?\s*(\d{1,2}):(\d{2}):(\d{2})',
        r'总用时[：:]?\s*(\d{1,2}):(\d{2}):(\d{2})',
        r'(\d{1,2}):(\d{2})[，,](\d{1,2})',
        r'(\d{1,2})["\s:](\d{2})["\s:]?(?!\d)',
        r'(\d{1,2}):(\d{2})(?!\d)',
        r'时长[：:]?\s*(\d{1,2}):(\d{2})',
    ]

    DATE_PATTERNS = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})[/\-年](\d{1,2})[/\-月](\d{1,2})',
        r'(\d{2})/(\d{2})/(\d{4})',
        r'(\d{4})(\d{2})(\d{2})',
    ]

    HEART_RATE_PATTERNS = [
        r"(\d{2,3})\s*[bB][pP][mM](?![0-9])",
        r"\D(\d{2,3})\s*[bB][pP][mM]\D",
        r"\D(\d{2,3})\s*[bB][pP][mM](?![0-9])",
        r"心率[：:\s]*(\d{2,3})(?![0-9])",
        r"平均心率[：:\s]*(\d{2,3})(?![0-9])",
        r"\D(\d{2,3})\s*(?:次|次/分)",
        r"平\s*均\s*心\s*率[：:\s]*(\d{2,3})(?![0-9])",
        r"心\s*率[：:\s]*(\d{2,3})(?![0-9])",
        r"\D(\d{2,3})\s*[bB]\s*[pP]\s*[mM]\D",
        r"[bB][pP][mM]\s*(\d{2,3})(?![0-9])",
    ]

    @classmethod
    def _fix_double_decimal_pattern(cls, text: str) -> str:
        """
        预处理校正：检测XX.X.Xkm模式（如191.5.20km被误识为两个距离合并）
        转换为XX.Xkm X.Xkm格式，保留两位小数
        例如: 191.5.20km -> 191.5km 5.20km
              5.20.20km -> 5.20km 5.20km
        """
        # 匹配模式：数字.数字.数字后跟km（两个小数点的情况）
        # (\d+\.\d{1,2})\.(\d{1,2})(?=km)
        # 第一组: \d+\.\d{1,2} 匹配如 191.5 或 5.20
        # 第二组: \d{1,2} 匹配如 20 或 6
        pattern = r'(\d+\.\d{1,2})\.(\d{1,2})(?=km)'

        def replacer(match):
            first_num = match.group(1)  # 如 191.5 或 5.20
            second_num = match.group(2)  # 如 20 或 6

            # 尝试还原第二个数字：如果second_num是两位数，说明可能丢失了前导数字
            # 例如 .20 可能是 .5.20 的误识，即真实值是 5.20
            # 如果second_num是1-2位数字，前面可能丢失了前导数字
            if len(second_num) <= 2:
                # second_num可能是 .X.XXkm 中的 XX，需要还原为 X.XX
                # 提取first_num的最后一位数字作为second_num的前缀
                # 但这需要判断first_num是否有小数部分
                if '.' in first_num:
                    parts = first_num.rsplit('.', 1)
                    if len(parts) == 2 and len(parts[1]) >= 1:
                        # first_num = "191.5", parts[1] = "5"
                        # second_num = "20", 还原为 "5.20"
                        leading_digit = parts[1][0]  # 取小数部分的第一位
                        restored_second = f"{leading_digit}.{second_num}"
                        return f"{first_num}km {restored_second}km"

            return f"{first_num}km {second_num}km"

        return re.sub(pattern, replacer, text)

    @classmethod
    def extract_distance(cls, text: str) -> Optional[float]:
        clean_text = re.sub(r'\s+', '', text)

        # 预处理：校正XX.X.Xkm模式
        clean_text = cls._fix_double_decimal_pattern(clean_text)

        # 第一步：在"距离"或"总距离"关键字之前查找数字（最优先）
        distance_keyword_match = re.search(r'距离|总距离', clean_text)
        if distance_keyword_match:
            kw_pos = distance_keyword_match.start()
            before_region = clean_text[max(0, kw_pos-50):kw_pos]
            print(f"[OCR DEBUG] 距离关键字前区域: '{before_region}'")
            candidates = []

            # 优先匹配两位小数格式的数字（如12.00, 5.20），即使后面有省略号等分隔符
            for num_match in re.finditer(r'(\d+\.\d{2})', before_region):
                try:
                    num_str = num_match.group(1)
                    distance = float(num_str)
                    print(f"[OCR DEBUG] 候选数字(两位小数): {num_str} -> {distance}")
                    if 0.5 <= distance <= 50:
                        candidates.append((num_match.start(), distance, num_str, 2))  # 优先级2最高
                except ValueError:
                    continue

            # 匹配其他带小数点的数字
            for num_match in re.finditer(r'(\d+\.\d{1})(?!\d)', before_region):
                try:
                    num_str = num_match.group(1)
                    if any(c[2] == num_str for c in candidates):
                        continue  # 已在两位小数中找到
                    distance = float(num_str)
                    print(f"[OCR DEBUG] 候选数字(一位小数): {num_str} -> {distance}")
                    if 0.5 <= distance <= 50:
                        candidates.append((num_match.start(), distance, num_str, 1))
                except ValueError:
                    continue

            # 匹配整数
            for num_match in re.finditer(r'(?<!\d)(\d+)(?!\d)', before_region):
                try:
                    num_str = num_match.group(1)
                    distance = float(num_str)
                    print(f"[OCR DEBUG] 候选数字(整数): {num_str} -> {distance}")
                    if 0.5 <= distance <= 50:
                        candidates.append((num_match.start(), distance, num_str, 0))
                except ValueError:
                    continue
            if candidates:
                # 按优先级排序（优先级高的在前），同优先级按位置排序（最后的在前）
                candidates.sort(key=lambda x: (-x[3], x[0]))
                print(f"[OCR DEBUG] 距离匹配（距离关键字前）: {candidates[0][1]}")
                return round(candidates[0][1], 2)

        # 第二步：匹配 "数字.数字 km" 格式（如 5.20 km、5.20km）
        # 支持数字和km之间有各种分隔符（引号、@、空格等）
        km_pattern_match = re.search(r'(\d+\.\d{1,2})[^0-9a-zA-Z]*[@\s"\']*[kK][mM]', clean_text)
        if km_pattern_match:
            distance = float(km_pattern_match.group(1))
            if 0.5 <= distance <= 50:
                print(f"[OCR DEBUG] 距离匹配（x.xx km格式）: {distance}")
                return round(distance, 2)

        # 第三步：在km标记附近查找（排除风速）
        for km_match in re.finditer(r'[kK][mM](?![a-zA-Z])', clean_text):
            km_pos = km_match.start()
            # 排除 km/h 风速
            if km_pos + 2 < len(clean_text) and clean_text[km_pos + 2] in '/\\':
                continue
            # 排除"风"字后面的km
            immediate_before = clean_text[max(0, km_pos-15):km_pos]
            if '风' in immediate_before:
                print(f"[OCR DEBUG] 跳过风速区域 at {km_pos}: '{immediate_before}'")
                continue
            # km前面的数字
            search_region = clean_text[max(0, km_pos-15):km_pos+3]
            for pattern in cls.DISTANCE_PATTERNS[:4]:
                match = re.search(pattern, search_region)
                if match:
                    try:
                        distance = float(match.group(1))
                        if 0.5 <= distance <= 50:
                            print(f"[OCR DEBUG] 距离匹配（km标记）: {distance}")
                            return round(distance, 2)
                    except (ValueError, IndexError):
                        continue

        # 第三步半：匹配 X.XX un 格式（km的OCR误识别，如7.68 un35:31）
        for pattern in [r'(\d+\.\d{2})\s*[uU][nN]',
                       r'(\d+\.\d{2})[uU][nN]']:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    distance = float(match.group(1))
                    if 0.5 <= distance <= 50:
                        print(f"[OCR DEBUG] 距离匹配（X.XX un格式）: {distance}")
                        return round(distance, 2)
                except (ValueError, IndexError):
                    pass

        # 第三步四分之三：匹配 X.XX i. 格式（km的OCR误识别，如1.19 i.）
        for pattern in [r'(\d+\.\d{2})\s*[iI]\s*[.,。]',
                       r'(\d+\.\d{2})[iI]\s*[.,。](?!\d)',
                       r'(\d+\.\d{2})\s*[iI](?![a-zA-Z0-9])']:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    distance = float(match.group(1))
                    if 0.5 <= distance <= 50:
                        print(f"[OCR DEBUG] 距离匹配（X.XX i.格式）: {distance}")
                        return round(distance, 2)
                except (ValueError, IndexError):
                    pass

        # 第四步：检查25.00... i模式（支持各种省略号）
        for pattern in [r'(\d+\.\d{2})[.⋯·…]+\s*[iI](?![a-zA-Z])',
                       r'(\d+\.\d{2})\.\.\.\s*[iI](?![a-zA-Z])',
                       r'(\d+\.\d{2})\s*\.\.\.\s*[iI]']:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    distance = float(match.group(1))
                    if 0.5 <= distance <= 50:
                        print(f"[OCR DEBUG] 距离匹配（...i模式）: {distance}")
                        return round(distance, 2)
                except (ValueError, IndexError):
                    pass

        # 第四步半：匹配XX.XX...格式（如12.00...、5.20...），忽略后续任何字符
        for pattern in [r'(\d+\.\d{2})[.⋯·…]+',
                       r'(\d+\.\d{2})\.\.\.',
                       r'(\d+\.\d{2})\s*\.\.\.']:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    distance = float(match.group(1))
                    if 0.5 <= distance <= 50:
                        print(f"[OCR DEBUG] 距离匹配（XX.XX...格式）: {distance}")
                        return round(distance, 2)
                except (ValueError, IndexError):
                    pass

        # 第五步：兜底 - 找最大距离值
        matches = []
        for pattern in cls.DISTANCE_PATTERNS:
            for match in re.finditer(pattern, clean_text):
                try:
                    distance = float(match.group(1))
                    if 0.5 <= distance <= 50:
                        match_start = match.start()
                        after_text = clean_text[match_start:match_start+30]
                        before_text = clean_text[max(0, match_start-10):match_start+10]

                        # 排除 kcal
                        if re.search(r'k[aA][lL]|千卡|卡路里', after_text, re.IGNORECASE):
                            continue
                        # 排除风速 km/h
                        if re.search(r'[kK][mM]/[hH]', after_text):
                            continue
                        # 排除"风"字前面的数字（风速）
                        if re.search(r'风.{0,10}\d+', before_text) or re.search(r'\d+.{0,5}风', before_text):
                            continue
                        # 排除明显是小数点后的百位（如25.00被误读为2500）
                        if distance > 100:
                            continue
                        matches.append(distance)
                except (ValueError, IndexError):
                    continue
        if matches:
            print(f"[OCR DEBUG] 兜底候选: {matches}")
            min_dist = min(matches)
            print(f"[OCR DEBUG] 距离匹配（兜底最小值）: {min_dist}")
            return round(min_dist, 2)

        return None

    @classmethod
    def extract_time(cls, text: str) -> Optional[str]:
        clean_text = re.sub(r'\s+', '', text)

        # 第一步：查找"运动时间"关键字，优先在其后面查找时间
        time_keyword_match = re.search(r'运动时间|运动时长', clean_text)
        if time_keyword_match:
            tk_pos = time_keyword_match.start()
            # 优先在关键字后面查找（OCR顺序可能颠倒）
            after_region = clean_text[tk_pos:min(tk_pos+100, len(clean_text))]
            print(f"[OCR DEBUG] 运动时间后面区域: '{after_region[:60]}'")

            # 先在后面找 hh:mm:ss
            for pattern in cls.TIME_PATTERNS[:3]:
                match = re.search(pattern, after_region)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        h, m, s = groups
                        if len(s) == 3 and s[0] == s[1]:
                            s = s[1:]
                        if int(h) > 0 or int(m) >= 10:  # 排除明显是手机时间的情况
                            print(f"[OCR DEBUG] 时间匹配（运动时间后）: {h}:{m}:{s}")
                            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            # 在后面找 mm:ss
            match = re.search(r'(\d{1,2})[:\s]+(\d{2})', after_region)
            if match:
                m, s = match.groups()
                m, s = int(m), int(s)
                if 1 <= m <= 59 and 0 <= s <= 59:
                    if m >= 10:  # 跑步时间通常 > 10分钟
                        print(f"[OCR DEBUG] 时间匹配（mm:ss后）: 00:{m:02d}:{s:02d}")
                        return f"00:{m:02d}:{s:02d}"

            # 如果后面没找到，才在前面找
            before_region = clean_text[max(0, tk_pos-100):tk_pos]
            print(f"[OCR DEBUG] 运动时间前面区域: '{before_region[-60:]}'")

            # 在前面找 mm:ss 格式（27:48 是 mm:ss）
            match = re.search(r'(\d{1,2})[^\d]*(\d{2})(?!\d)', before_region)
            if match:
                m, s = match.groups()
                m, s = int(m), int(s)
                if 1 <= m <= 59 and 0 <= s <= 59 and m >= 10:
                    print(f"[OCR DEBUG] 时间匹配（运动时间前:mm:ss）: 00:{m:02d}:{s:02d}")
                    return f"00:{m:02d}:{s:02d}"

            # 在前面找 hh:mm:ss
            for pattern in cls.TIME_PATTERNS[:3]:
                match = re.search(pattern, before_region)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        h, m, s = groups
                        if len(s) == 3 and s[0] == s[1]:
                            s = s[1:]
                        if int(h) > 0:
                            print(f"[OCR DEBUG] 时间匹配（运动时间前:hh:mm:ss）: {h}:{m}:{s}")
                            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

        # 第二步：全文搜索（排除开头部分）
        # 跳过前50个字符（避免匹配到手机截图时间）
        search_text = clean_text[50:] if len(clean_text) > 50 else clean_text

        for pattern in cls.TIME_PATTERNS[:3]:
            match = re.search(pattern, search_text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    h, m, s = groups
                    if len(s) == 3 and s[0] == s[1]:
                        s = s[1:]
                    if int(h) > 0:
                        print(f"[OCR DEBUG] 时间候选: {h}:{m}:{s}")
                        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

        # 第三步：匹配 mm:ss（从50字符后）
        match = re.search(r'(\d{1,2})[:\s]+(\d{2})', search_text)
        if match:
            m, s = match.groups()
            m, s = int(m), int(s)
            if 1 <= m <= 59 and 0 <= s <= 59:
                print(f"[OCR DEBUG] mm:ss匹配: 00:{m:02d}:{s:02d}")
                return f"00:{m:02d}:{s:02d}"

        return None

    @classmethod
    def extract_date(cls, text: str) -> Optional[str]:
        clean_text = re.sub(r'\s+', '', text)

        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, clean_text)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:
                    y, m, d = groups
                elif len(groups[2]) == 4:
                    m, d, y = groups
                else:
                    y, m, d = groups[0][:4], groups[0][4:6], groups[0][6:8]
                try:
                    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                except ValueError:
                    continue
        return None

    @classmethod
    def extract_heart_rate(cls, text: str) -> Optional[int]:
        for pattern in cls.HEART_RATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    hr = int(match.group(1))
                    if 40 <= hr <= 220:
                        return hr
                except (ValueError, IndexError):
                    continue

        hr_keyword_match = re.search(r'平均心率|平\s*均\s*心\s*率', text)
        if hr_keyword_match:
            hr_pos = hr_keyword_match.start()
            before_region = text[max(0, hr_pos-80):hr_pos]
            candidates = []
            for num_match in re.finditer(r'(?<!\d)(\d{2,3})(?!\d)', before_region):
                try:
                    hr = int(num_match.group(1))
                    if 40 <= hr <= 220:
                        candidates.append(hr)
                except ValueError:
                    continue
            if candidates:
                return candidates[-1]

        return None

    @classmethod
    def extract_all(cls, text: str) -> RunningData:
        data = RunningData()
        data.distance = cls.extract_distance(text)
        data.time = cls.extract_time(text)
        data.date = cls.extract_date(text)
        data.heart_rate = cls.extract_heart_rate(text)
        data.raw_text = text
        data.success = any([data.distance, data.time, data.date, data.heart_rate])

        if data.distance is not None:
            print(f"[OCR DEBUG] 距离提取结果: {data.distance} km")
        return data


class OCRService:
    def __init__(self, tesseract_path: Optional[str] = None, lang: str = 'eng+chi_sim'):
        self.tesseract_path = tesseract_path
        self.lang = lang
        self.preprocessor = ImagePreprocessor()
        self.extractor = DataExtractor()
        self._tesseract_available = None
        self._configure_tesseract()

    def _configure_tesseract(self):
        if self._tesseract_available is not None:
            return

        try:
            import pytesseract
            possible_paths = []

            if self.tesseract_path:
                possible_paths.append(self.tesseract_path)

            possible_paths.extend([
                os.environ.get('TESSERACT_PATH', ''),
                r'D:\tesseract\tesseract.exe',
                r'D:\Tesseract\tesseract.exe',
                r'D:\Program Files\Tesseract-OCR\tesseract.exe',
                r'D:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
            ])

            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_path = path
                    self._tesseract_available = True
                    print(f"[OCR] Tesseract已配置: {path}")
                    return

            pytesseract.pytesseract.tesseract_cmd = 'tesseract'
            self._tesseract_available = True

        except ImportError:
            self._tesseract_available = False
            print("[OCR] 错误: pytesseract未安装，请运行: pip install pytesseract")

    def _time_to_seconds(self, time_str: str) -> Optional[int]:
        if not time_str:
            return None
        parts = time_str.split(':')
        try:
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
        except ValueError:
            return None
        return None

    async def recognize_run_data(self, image_path: str) -> dict:
        result = {
            "distance": None,
            "duration": None,
            "heart_rate": None,
            "date": None,
            "success": False,
            "message": ""
        }

        if not os.path.exists(image_path):
            result["message"] = "图片文件不存在"
            return result

        if not self._tesseract_available:
            result["message"] = "Tesseract/pytesseract未安装或未配置"
            return result

        try:
            import pytesseract

            image = Image.open(image_path)
            width, height = image.size
            if width < 1000:
                new_size = (int(width * 2), int(height * 2))
                image = image.resize(new_size, Image.LANCZOS)

            processed = self.preprocessor.preprocess_for_ocr(image)

            text = pytesseract.image_to_string(processed, lang=self.lang, config='--psm 6')
            print(f"[OCR DEBUG] 识别文本:\n{text}")

            data = self.extractor.extract_all(text)

            if data.success:
                result["success"] = True
                result["distance"] = data.distance
                result["duration"] = self._time_to_seconds(data.time)
                result["heart_rate"] = data.heart_rate
                result["date"] = data.date
                result["message"] = "识别成功"
                print(f"[OCR] 日期: {data.date}, 距离: {data.distance} km, 时间: {data.time}, 心率: {data.heart_rate} bpm")
            else:
                result["message"] = "未能从图片中提取到有效数据，请手动填写"
                print(f"[OCR] 识别失败")

            result["_raw_text"] = text

        except Exception as e:
            result["message"] = f"OCR识别异常: {str(e)}"
            print(f"[OCR] 识别异常: {e}")

        return result


ocr_service = OCRService()
