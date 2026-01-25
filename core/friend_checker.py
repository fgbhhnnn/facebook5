"""
好友可见性检查模块
负责检查Facebook用户主页的好友列表是否可见
"""
import re
import time
import requests
from typing import Tuple, Optional, List
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
        检查用户主页的链接是否有效
        
        Args:
            profile_url: 用户主页URL
            profile_name: 用户名称
            
        Returns:
            (是否有效, 结果描述, 链接是否有效)
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
            
            if is_valid:
                # 检查好友链接数量
                has_enough_friends, friend_count, friend_message = self._check_friend_links_count(profile_url)
                
                if has_enough_friends:
                    return True, f"{profile_name}: 链接有效，检测到 {friend_count} 个好友链接", True
                else:
                    return False, f"{profile_name}: {friend_message}", False
            else:
                return False, f"{profile_name}: {valid_message}", False
        
        except Exception as e:
            return False, f"{profile_name}: 检查过程中出错 - {str(e)}", False
    
    def _check_link_validity(self) -> Tuple[bool, str]:
        """
        检查链接是否有效
        
        Returns:
            (是否有效, 消息)
        """
        try:
            # 获取所有span元素的文本内容
            try:
                span_elements = self.driver.find_elements(By.TAG_NAME, 'span')
                page_text = ' '.join([span.text for span in span_elements if span.text])
            except:
                # 如果获取失败，返回有效
                return True, "链接有效"
            
            # 检查无效链接的提示
            invalid_indicators = [
                '粉丝名单不公开',
                '你暂时被禁止使用此功能',
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
    
    def _parse_name_from_url(self, profile_url: str) -> Tuple[str, str]:
        """
        从URL中解析名字
        
        Args:
            profile_url: 用户主页URL，格式如 https://www.facebook.com/Ted.Sandlin/friends/
            
        Returns:
            (firstname, lastname)
        """
        try:
            # 提取URL中的用户名部分
            # 格式: https://www.facebook.com/Ted.Sandlin/friends/
            match = re.search(r'facebook\.com/([^/]+)/friends', profile_url)
            if match:
                username = match.group(1)
                # 按点分割名字
                parts = username.split('.')
                if len(parts) >= 2:
                    firstname = parts[0]
                    lastname = parts[1]
                elif len(parts) == 1:
                    firstname = parts[0]
                    lastname = ''
                else:
                    firstname = ''
                    lastname = ''
                return firstname, lastname
            return '', ''
        except Exception as e:
            print(f"解析名字失败: {e}")
            return '', ''
    
    def _upload_friend_links_to_api(self, profile_url: str, friend_links: List[str]) -> bool:
        """
        上传好友链接到API
        
        Args:
            profile_url: 本身访问链接
            friend_links: 获取到的所有好友链接列表
            
        Returns:
            是否上传成功
        """
        try:
            # 解析名字
            firstname, lastname = self._parse_name_from_url(profile_url)
            
            # 去重
            unique_links = list(set(friend_links))
            
            # 构建请求数据
            data = {
                "url": profile_url,
                "urllist": unique_links,
                "firstname": firstname,
                "lastname": lastname
            }
            
            # 发送POST请求
            api_url = "https://ywgdhm.qpon/api/facebookurl"
            headers = {
                "Content-Type": "application/json"
            }
            
            print(f"正在上传数据到API: {api_url}")
            print(f"URL: {profile_url}")
            print(f"Firstname: {firstname}, Lastname: {lastname}")
            print(f"链接数量: {len(unique_links)}")
            
            response = requests.post(api_url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print(f"上传成功! 响应: {response.text}")
                return True
            else:
                print(f"上传失败! 状态码: {response.status_code}, 响应: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("上传超时")
            return False
        except requests.exceptions.RequestException as e:
            print(f"上传请求异常: {e}")
            return False
        except Exception as e:
            print(f"上传数据时出错: {e}")
            return False
    
    def _check_friend_links_count(self, profile_url: str) -> Tuple[bool, int, str]:
        """
        检查好友链接数量
        
        Args:
            profile_url: 用户主页URL
            
        Returns:
            (是否有足够好友, 好友数量, 消息)
        """
        try:
            max_scroll_attempts = 10  # 最大滚动次数
            min_friend_count = 60    # 最小好友数量要求
            friend_pattern = re.compile(r'https://www\.facebook\.com/[^/?]+$')  # 匹配 https://www.facebook.com/用户名 格式
            all_friend_links = []    # 存储所有找到的好友链接
            
            for attempt in range(max_scroll_attempts):
                # 获取所有a标签
                try:
                    a_elements = self.driver.find_elements(By.TAG_NAME, 'a')
                except:
                    return False, 0, "无法获取页面链接"
                
                # 提取所有href属性
                all_links = []
                for a in a_elements:
                    try:
                        href = a.get_attribute('href')
                        if href:
                            all_links.append(href)
                    except:
                        continue
                
                # 匹配符合格式的好友链接
                friend_links = []
                for link in all_links:
                    if friend_pattern.match(link):
                        # 排除一些非好友的链接
                        if not any(exclude in link for exclude in [
                            '/pages/',
                            '/groups/',
                            '/events/',
                            '/marketplace/',
                            '/watch/',
                            '/messages/',
                            '/notifications/',
                            '/settings/',
                            '/help/',
                            '/bookmarks/',
                            '/saved/',
                            '/games/',
                            '/fundraisers/',
                            '/jobs/',
                            '/memories/',
                            '/offers/',
                            '/places/',
                            '/reels/',
                            '/stories/',
                            '/ads/',
                            '/business/',
                            '/developers/',
                            '/privacy/',
                            '/terms/',
                            '/login/',
                            '/reg/',
                            '/r.php',
                            '/sharer/',
                            '/dialog/'
                        ]):
                            friend_links.append(link)
                
                # 累加到总列表
                all_friend_links.extend(friend_links)
                
                # 去重
                all_friend_links = list(set(all_friend_links))
                friend_count = len(all_friend_links)
                
                print(f"第 {attempt + 1} 次检测: 找到 {friend_count} 个好友链接")
                
                # 如果好友数量达到要求，返回成功
                if friend_count >= min_friend_count:
                    # 上传数据到API
                    self._upload_friend_links_to_api(profile_url, all_friend_links)
                    return True, friend_count, f"检测到 {friend_count} 个好友链接"
                
                # 如果不是最后一次尝试，滚动页面
                if attempt < max_scroll_attempts - 1:
                    try:
                        # 滚动到页面底部
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(5)  # 等待内容加载
                        
                        # 再向上滚动一点，触发懒加载
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                        time.sleep(5)
                    except:
                        pass
            
            # 滚动多次后仍未达到要求，但仍然上传找到的链接
            if all_friend_links:
                self._upload_friend_links_to_api(profile_url, all_friend_links)
            
            return False, friend_count, f"好友数量不足（仅检测到 {friend_count} 个，需要至少 {min_friend_count} 个）"
        
        except Exception as e:
            return False, 0, f"检查好友链接数量时出错: {str(e)}"
    
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