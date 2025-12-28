"""
浏览器自动化模块
负责创建和管理浏览器实例
"""
import time
import random
from typing import Optional
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config import BROWSER_CONFIG, FACEBOOK_URL


class FingerprintGenerator:
    """浏览器指纹生成器"""
    
    # 常见的User-Agent列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    # 常见的屏幕分辨率
    SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1600, 900),
        (2560, 1440),
        (1280, 720),
    ]
    
    # 常见的语言设置
    LANGUAGES = [
        'zh-CN,zh;q=0.9,en;q=0.8',
        'en-US,en;q=0.9',
        'zh-CN,zh;q=0.9',
        'en-GB,en;q=0.9',
    ]
    
    # 常见的时区
    TIMEZONES = [
        'Asia/Shanghai',
        'America/New_York',
        'Europe/London',
        'Asia/Tokyo',
        'Europe/Paris',
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """获取随机User-Agent"""
        return random.choice(FingerprintGenerator.USER_AGENTS)
    
    @staticmethod
    def get_random_resolution() -> tuple:
        """获取随机屏幕分辨率"""
        return random.choice(FingerprintGenerator.SCREEN_RESOLUTIONS)
    
    @staticmethod
    def get_random_language() -> str:
        """获取随机语言设置"""
        return random.choice(FingerprintGenerator.LANGUAGES)
    
    @staticmethod
    def get_random_timezone() -> str:
        """获取随机时区"""
        return random.choice(FingerprintGenerator.TIMEZONES)
    
    @staticmethod
    def generate_random_fingerprint() -> dict:
        """生成随机浏览器指纹"""
        return {
            'user_agent': FingerprintGenerator.get_random_user_agent(),
            'resolution': FingerprintGenerator.get_random_resolution(),
            'language': FingerprintGenerator.get_random_language(),
            'timezone': FingerprintGenerator.get_random_timezone(),
        }


class BrowserAutomation:
    """浏览器自动化类"""
    
    def __init__(self, headless: bool = False):
        """
        初始化浏览器自动化
        
        Args:
            headless: 是否使用无头模式
        """
        self.driver: Optional[uc.Chrome] = None
        self.headless = headless
    
    def create_driver(self) -> uc.Chrome:
        """
        创建Chrome浏览器驱动（使用undetected-chromedriver）
        
        Returns:
            Chrome WebDriver实例
        """
        chrome_options = Options()
        
        # 生成随机浏览器指纹
        fingerprint = FingerprintGenerator.generate_random_fingerprint()
        print(f"使用随机浏览器指纹: {fingerprint['user_agent'][:50]}...")
        
        # 设置无头模式（始终为False，显示浏览器窗口）
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # 设置随机窗口大小
        width, height = fingerprint['resolution']
        chrome_options.add_argument(f'--window-size={width},{height}')
        
        # 禁用一些不必要的功能
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--start-maximized')
        
        # 设置随机用户代理
        chrome_options.add_argument(f'user-agent={fingerprint["user_agent"]}')
        
        # 设置随机语言
        chrome_options.add_argument(f'--lang={fingerprint["language"]}')
        
        # 设置随机时区
        chrome_options.add_argument(f'--timezone={fingerprint["timezone"]}')
        
        # 添加更多反检测参数（undetected-chromedriver兼容）
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # 随机设置一些Chrome偏好设置
        prefs = {
            'profile.default_content_setting_values': {
                'notifications': 2,
                'geolocation': 2,
            },
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2,
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        try:
            # 使用undetected-chromedriver创建驱动
            print("正在初始化Chrome浏览器（使用undetected-chromedriver）...")
            
            # 创建驱动，undetected-chromedriver会自动处理ChromeDriver的下载和配置
            self.driver = uc.Chrome(
                options=chrome_options,
                version_main=None,  # 自动检测Chrome版本
                use_subprocess=True,  # 使用子进程
                keep_alive=True  # 保持连接
            )
            
            # 设置隐式等待
            self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
            self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
            
            print("Chrome浏览器启动成功")
            return self.driver
            
        except Exception as e:
            error_msg = str(e)
            print(f"创建Chrome驱动失败: {error_msg}")
            raise Exception(
                f"无法启动Chrome浏览器。请确保：\n"
                f"1. 已安装Chrome浏览器\n"
                f"2. 网络连接正常（需要下载ChromeDriver）\n"
                f"3. 没有防火墙阻止程序运行\n"
                f"错误详情: {error_msg}"
            )
    
    def navigate_to_facebook(self) -> bool:
        """
        导航到Facebook主页
        
        Returns:
            是否成功
        """
        try:
            self.driver.get(FACEBOOK_URL)
            return True
        except Exception as e:
            print(f"导航到Facebook失败: {e}")
            return False
    
    def navigate_to_url(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            
        Returns:
            是否成功
        """
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"导航到URL失败: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            是否加载完成
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            return True
        except Exception as e:
            print(f"等待页面加载超时: {e}")
            return False
    
    def get_page_source(self) -> str:
        """
        获取页面源代码
        
        Returns:
            页面源代码
        """
        return self.driver.page_source
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.create_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()