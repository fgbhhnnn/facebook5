"""
文件解析工具模块
用于解析用户上传的Facebook链接文件
"""
import re
import os
from typing import List, Tuple


class FileParser:
    """文件解析器"""
    
    @staticmethod
    def parse_links_file(file_path: str) -> List[Tuple[str, str]]:
        """
        解析链接文件
        格式: 链接----名字
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含(链接, 名字)元组的列表
        """
        links = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析格式: 链接----名字
                    if '----' in line:
                        parts = line.split('----', 1)
                        if len(parts) == 2:
                            url = parts[0].strip()
                            name = parts[1].strip()
                            links.append((url, name))
                    else:
                        # 如果没有分隔符，尝试提取URL
                        url_match = re.search(r'https?://[^\s]+', line)
                        if url_match:
                            url = url_match.group()
                            name = line.replace(url, '').strip()
                            links.append((url, name))
        
        except Exception as e:
            print(f"解析文件时出错: {e}")
            return []
        
        return links
    
    @staticmethod
    def remove_checked_link(file_path: str, url: str) -> bool:
        """
        从文件中删除已检查的链接
        
        Args:
            file_path: 文件路径
            url: 要删除的链接
            
        Returns:
            是否成功删除
        """
        try:
            # 读取所有行
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 过滤掉要删除的链接
            new_lines = []
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    new_lines.append(line)
                    continue
                
                # 检查是否是要删除的链接
                if '----' in line_stripped:
                    url_in_line = line_stripped.split('----', 1)[0].strip()
                    if url_in_line == url:
                        continue  # 跳过这个链接
                else:
                    url_match = re.search(r'https?://[^\s]+', line_stripped)
                    if url_match and url_match.group() == url:
                        continue  # 跳过这个链接
                
                new_lines.append(line)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        
        except Exception as e:
            print(f"删除链接时出错: {e}")
            return False
    
    @staticmethod
    def validate_facebook_url(url: str) -> bool:
        """
        验证是否为有效的Facebook URL
        
        Args:
            url: 待验证的URL
            
        Returns:
            是否有效
        """
        pattern = r'https?://(www\.)?facebook\.com/.*'
        return bool(re.match(pattern, url))