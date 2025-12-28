"""
好友可见性检查模块
负责检查Facebook用户主页的好友列表是否可见
"""
import re
import time
from typing import Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .cookie_manager import CookieManager
from .browser_automation import BrowserAutomation


class FriendChecker:
    """好友可见性检查器"""
    
    def __init__(self, cookie_string: str, headless: bool = False, thread_index: int = 0, total_threads: int = 1):
        """
        初始化好友检查器
        
        Args:
            cookie_string: Facebook Cookie字符串
            headless: 是否使用无头模式
            thread_index: 当前线程索引（从0开始）
            total_threads: 总线程数
        """
        self.cookie_string = cookie_string
        self.browser = BrowserAutomation(headless=headless, thread_index=thread_index, total_threads=total_threads)
        self.driver: Optional[webdriver.Chrome] = None
        self.cookie_restored = False  # 标记Cookie是否已恢复
    
    def initialize_browser(self) -> bool:
        """
        初始化浏览器并恢复Cookie（只执行一次）
        
        Returns:
            是否成功
        """
        try:
            # 如果浏览器已初始化且Cookie已恢复，直接返回
            if self.driver is not None and self.cookie_restored:
                return True
            
            # 创建浏览器驱动
            if self.driver is None:
                self.driver = self.browser.create_driver()
            
            # 导航到Facebook主页
            self.browser.navigate_to_facebook()
            self.browser.wait_for_page_load()
            
            # 恢复Cookie
            if not CookieManager.restore_cookies(self.driver, self.cookie_string):
                return False
            
            # 等待页面加载
            time.sleep(3)
            self.cookie_restored = True
            
            return True
        except Exception as e:
            print(f"初始化浏览器失败: {e}")
            return False
    
    def check_friend_visibility(self, profile_url: str, profile_name: str) -> Tuple[bool, str, bool]:
        """
        检查用户主页的好友列表是否可见
        
        Args:
            profile_url: 用户主页URL
            profile_name: 用户名称
            
        Returns:
            (是否可见, 结果描述, 链接是否有效)
        """
        try:
            # 初始化浏览器（如果还未初始化）
            if not self.initialize_browser():
                return False, f"{profile_name}: 浏览器初始化失败", False
            
            # 导航到用户主页
            if not self.browser.navigate_to_url(profile_url):
                return False, f"{profile_name}: 无法访问用户主页", False
            
            # 等待页面加载
            self.browser.wait_for_page_load()
            time.sleep(3)
            
            # 检查链接是否有效
            is_valid, valid_message = self._check_link_validity()
            if not is_valid:
                return False, f"{profile_name}: {valid_message}", False
            
            # 检查好友列表是否可见
            is_visible, message = self._check_friends_section()
            
            if is_visible:
                return True, f"{profile_name}: 好友列表可见", True
            else:
                return False, f"{profile_name}: {message}", True
        
        except Exception as e:
            return False, f"{profile_name}: 检查过程中出错 - {str(e)}", False
    
    def _check_link_validity(self) -> Tuple[bool, str]:
        """
        检查链接是否有效
        
        Returns:
            (是否有效, 消息)
        """
        try:
            # 获取所有span元素的文本内容（比获取整个DOM快得多）
            try:
                span_elements = self.driver.find_elements(By.TAG_NAME, 'span')
                page_text = ' '.join([span.text.lower() for span in span_elements if span.text])
            except:
                # 如果获取失败，返回有效
                return True, "链接有效"
            
            # 检查无效链接的提示（精确匹配）
            invalid_indicators = [
                '没有好友可显示',
                '内容暂时无法显示',
                'this content isn\'t available right now',
                'this page isn\'t available',
                '链接可能已损坏',
                '链接可能已被删除',
                'page not found',
                '404',
                'sorry, something went wrong'
            ]
            
            # 检查是否包含无效提示
            for indicator in invalid_indicators:
                if indicator in page_text:
                    return False, f"链接无效（检测到：{indicator}）"
            
            # 如果没有无效提示，则认为链接有效
            return True, "链接有效"
        
        except Exception as e:
            return False, f"检查链接有效性时出错: {str(e)}"
    
    def _check_friends_section(self) -> Tuple[bool, str]:
        """
        检查页面中的好友部分
        
        Returns:
            (是否可见, 消息)
        """
        try:
            # 获取所有span元素的文本内容（比获取整个DOM快得多）
            try:
                span_elements = self.driver.find_elements(By.TAG_NAME, 'span')
                page_text = ' '.join([span.text.lower() for span in span_elements if span.text])
            except:
                return False, "未找到好友列表"
            
            # 检查常见的"好友"相关文本
            friend_keywords = [
                'friends',
                '好友',
                'friend list',
                'friends list',
                'see all friends',
                '查看所有好友'
            ]
            
            # 检查是否有好友相关的链接或按钮
            for keyword in friend_keywords:
                if keyword in page_text:
                    # 进一步检查是否真的可以访问好友列表
                    if self._verify_friends_accessible():
                        return True, "好友列表可见"
            
            # 检查是否有"好友"限制提示
            restriction_indicators = [
                'only friends can see',
                '只有好友可见',
                'friends only',
                'restricted',
                'private'
            ]
            
            for indicator in restriction_indicators:
                if indicator in page_text:
                    return False, "好友列表受限"
            
            return False, "未找到好友列表"
        
        except Exception as e:
            return False, f"检查好友部分时出错: {str(e)}"
    
    def _verify_friends_accessible(self) -> bool:
        """
        验证好友列表是否真的可以访问
        
        Returns:
            是否可以访问
        """
        try:
            # 尝试查找好友相关的链接
            friend_selectors = [
                "//a[contains(text(), 'Friends')]",
                "//a[contains(text(), '好友')]",
                "//span[contains(text(), 'Friends')]",
                "//span[contains(text(), '好友')]",
                "//div[contains(@aria-label, 'Friends')]",
                "//div[contains(@aria-label, '好友')]"
            ]
            
            for selector in friend_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        # 找到了好友相关的元素
                        return True
                except:
                    continue
            
            return False
        
        except Exception:
            return False
    
    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
            self.driver = None
            self.cookie_restored = False
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()