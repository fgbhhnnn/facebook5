"""
Cookie管理模块
负责解析和恢复Facebook Cookie
"""
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By


class CookieManager:
    """Cookie管理器"""
    
    @staticmethod
    def parse_cookie_string(cookie_string: str) -> List[Dict]:
        """
        解析Cookie字符串
        
        Args:
            cookie_string: Cookie字符串，格式如: 'key1=value1; key2=value2;'
            
        Returns:
            Cookie字典列表
        """
        cookies = []
        
        if not cookie_string:
            return cookies
        
        # 分割各个cookie
        cookie_pairs = cookie_string.split(';')
        
        for pair in cookie_pairs:
            pair = pair.strip()
            if not pair:
                continue
            
            # 分割键值对
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies.append({
                    'name': key.strip(),
                    'value': value.strip(),
                    'domain': '.facebook.com',
                    'path': '/'
                })
        
        return cookies
    
    @staticmethod
    def restore_cookies(driver: webdriver.Chrome, cookie_string: str) -> bool:
        """
        恢复Cookie到浏览器
        
        Args:
            driver: Selenium WebDriver实例
            cookie_string: Cookie字符串
            
        Returns:
            是否成功
        """
        try:
            cookies = CookieManager.parse_cookie_string(cookie_string)
            
            # 先导航到Facebook域名
            driver.get("https://www.facebook.com")
            
            # 添加所有cookie
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加Cookie失败: {cookie['name']}, 错误: {e}")
                    continue
            
            # 刷新页面以应用cookie
            driver.refresh()
            
            return True
        
        except Exception as e:
            print(f"恢复Cookie时出错: {e}")
            return False
    
    @staticmethod
    def validate_cookie_string(cookie_string: str) -> bool:
        """
        验证Cookie字符串是否有效
        
        Args:
            cookie_string: Cookie字符串
            
        Returns:
            是否有效
        """
        if not cookie_string:
            return False
        
        # 检查是否包含必要的Facebook cookie
        required_cookies = ['c_user', 'xs', 'datr']
        cookies = CookieManager.parse_cookie_string(cookie_string)
        cookie_names = [cookie['name'] for cookie in cookies]
        
        # 至少包含一个必要的cookie
        return any(name in cookie_names for name in required_cookies)