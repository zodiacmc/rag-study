"""
获取配置文件信息
"""
import configparser
from pathlib import Path


class GetProperties:
    default_setting_file = "config.properties"

    def __init__(self, setting_file: str = default_setting_file):
        """
        初始化配置文件
        :param setting_file: 配置文件名
        """
        project_root = Path(__file__).resolve().parent.parent
        self.setting_file_path = project_root / "resources" / setting_file
        if not self.setting_file_path.is_file():
            raise FileNotFoundError(f"配置文件不存在: {self.setting_file_path}")
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # 保留 key 的原始大小写
        self.config.read(self.setting_file_path, encoding='utf-8')

    def get_property(self, section: str, key: str, fallback: str | None = None) -> str:
        """
        获取属性值
        :param section: 配置文件 section
        :param key: 配置文件 key
        :param fallback: key 不存在时的默认值，为 None 时抛异常
        :return: 属性值
        """
        if not self.config.has_section(section):
            raise KeyError(f"配置文件中不存在 section: [{section}]")
        if not self.config.has_option(section, key):
            if fallback is not None:
                return fallback
            raise KeyError(f"配置文件中不存在键: {section}.{key}")
        return self.config.get(section, key)

