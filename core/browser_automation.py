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
    
    def __init__(self, headless: bool = False, thread_index: int = 0, total_threads: int = 1):
        """
        初始化浏览器自动化
        
        Args:
            headless: 是否使用无头模式
            thread_index: 当前线程索引（从0开始）
            total_threads: 总线程数
        """
        self.driver: Optional[uc.Chrome] = None
        self.headless = headless
        self.thread_index = thread_index
        self.total_threads = total_threads
    
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
        
        # 设置无头模式
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # 只有在非无头模式下才计算和设置浏览器窗口大小和位置
        if not self.headless:
            # 根据线程数量计算浏览器窗口大小和位置
            window_width, window_height, window_x, window_y = self._calculate_window_position()
            
            # 设置窗口大小
            chrome_options.add_argument(f'--window-size={window_width},{window_height}')
            
            # 设置窗口位置
            chrome_options.add_argument(f'--window-position={window_x},{window_y}')
        
        # 禁用一些不必要的功能
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        # 移除 --start-maximized，避免与自定义窗口大小冲突
        
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
            # 添加更多参数来避免版本检测问题
            self.driver = uc.Chrome(
                options=chrome_options,
                version_main=None,  # 自动检测Chrome版本
                use_subprocess=True,  # 使用子进程
                keep_alive=True,  # 保持连接
                driver_executable_path=None,  # 让undetected-chromedriver自动管理driver
                browser_executable_path=None,  # 自动查找Chrome浏览器
                suppress_welcome=True,  # 抑制欢迎信息
                no_sandbox=True,  # 禁用沙箱
                disable_gpu=True  # 禁用GPU
            )
            
            # 设置隐式等待
            self.driver.implicitly_wait(BROWSER_CONFIG['implicit_wait'])
            self.driver.set_page_load_timeout(BROWSER_CONFIG['page_load_timeout'])
            
            # 在浏览器启动后设置窗口大小和位置（更可靠，仅在非无头模式下）
            if not self.headless:
                # 重新计算窗口位置和大小（确保与启动时一致）
                window_width, window_height, window_x, window_y = self._calculate_window_position()
                self.driver.set_window_position(window_x, window_y)
                self.driver.set_window_size(window_width, window_height)
                print(f"浏览器窗口已设置: 位置=({window_x}, {window_y}), 大小=({window_width}x{window_height})")
            else:
                print("无头模式：不设置浏览器窗口位置和大小")
            
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
    
    def _calculate_window_position(self) -> tuple:
        """
        根据线程数量计算浏览器窗口的大小和位置
        
        Returns:
            (width, height, x, y) 窗口宽高和位置
        """
        try:
            # 获取屏幕尺寸
            from selenium import webdriver
            temp_driver = webdriver.Chrome(options=Options())
            screen_width = temp_driver.execute_script("return window.screen.width")
            screen_height = temp_driver.execute_script("return window.screen.height")
            temp_driver.quit()
        except:
            # 如果获取失败，使用默认值
            screen_width = 1920
            screen_height = 1080
        
        # 计算网格布局（行数和列数）
        cols = int((self.total_threads ** 0.5) + 0.5)  # 列数约为线程数的平方根
        rows = (self.total_threads + cols - 1) // cols  # 行数向上取整
        
        # 计算每个浏览器窗口的大小
        margin = 10  # 窗口之间的间距
        window_width = (screen_width - margin * (cols + 1)) // cols
        window_height = (screen_height - margin * (rows + 1)) // rows
        
        # 确保窗口大小合理
        window_width = max(window_width, 300)
        window_height = max(window_height, 300)
        
        # 计算当前窗口的位置
        col = self.thread_index % cols
        row = self.thread_index // cols
        
        window_x = margin + col * (window_width + margin)
        window_y = margin + row * (window_height + margin)
        
        print(f"浏览器 {self.thread_index + 1}/{self.total_threads}: 位置=({window_x}, {window_y}), 大小=({window_width}x{window_height})")
        
        return (window_width, window_height, window_x, window_y)
    
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