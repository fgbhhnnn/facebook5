"""
ChromeDriver修复脚本
用于清理缓存并重新安装依赖
"""
import os
import shutil
import subprocess
import sys


def clean_chromedriver_cache():
    """清理ChromeDriver缓存"""
    print("=" * 60)
    print("清理ChromeDriver缓存")
    print("=" * 60)
    
    cache_dir = os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'chromedriver')
    
    if os.path.exists(cache_dir):
        print(f"找到缓存目录: {cache_dir}")
        try:
            shutil.rmtree(cache_dir)
            print("✓ ChromeDriver缓存已清理")
        except Exception as e:
            print(f"✗ 清理缓存失败: {e}")
            return False
    else:
        print("未找到ChromeDriver缓存目录")
    
    return True


def reinstall_dependencies():
    """重新安装依赖"""
    print("\n" + "=" * 60)
    print("重新安装依赖包")
    print("=" * 60)
    
    try:
        print("正在卸载webdriver-manager...")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "webdriver-manager"], 
                      capture_output=True)
        
        print("正在安装webdriver-manager...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        print("✓ webdriver-manager安装成功")
        
        print("正在安装selenium...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        print("✓ selenium安装成功")
        
        return True
    except Exception as e:
        print(f"✗ 安装依赖失败: {e}")
        return False


def check_chrome_browser():
    """检查Chrome浏览器是否安装"""
    print("\n" + "=" * 60)
    print("检查Chrome浏览器")
    print("=" * 60)
    
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.path.expanduser('~'), r"AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ 找到Chrome浏览器: {path}")
            return True
    
    print("✗ 未找到Chrome浏览器")
    print("请先安装Chrome浏览器: https://www.google.com/chrome/")
    return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  ChromeDriver修复工具")
    print("=" * 60)
    print()
    
    # 检查Chrome浏览器
    if not check_chrome_browser():
        input("\n按任意键退出...")
        return False
    
    # 清理缓存
    if not clean_chromedriver_cache():
        input("\n按任意键退出...")
        return False
    
    # 重新安装依赖
    if not reinstall_dependencies():
        input("\n按任意键退出...")
        return False
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
    print("\n现在可以重新运行程序了。")
    print("如果还有问题，请确保：")
    print("1. Chrome浏览器是最新版本")
    print("2. 网络连接正常")
    print("3. 没有防火墙阻止下载")
    
    input("\n按任意键退出...")
    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
        sys.exit(1)