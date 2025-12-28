"""
Facebook好友可见性检查工具 - 打包脚本
"""
import os
import sys
import subprocess
import shutil


def install_requirements():
    """安装所需的依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装依赖包失败: {e}")
        return False


def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装PyInstaller失败: {e}")
        return False


def build_exe():
    """使用PyInstaller构建exe文件"""
    print("正在构建exe文件...")
    try:
        # 检查是否存在spec文件
        if os.path.exists("build.spec"):
            print("使用build.spec配置文件进行打包...")
            cmd = [sys.executable, "-m", "PyInstaller", "build.spec"]
        else:
            print("使用命令行参数进行打包...")
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--name=Facebook好友可见性检查工具",
                "--windowed",  # 不显示控制台窗口
                "--onefile",   # 打包成单个exe文件
                "--add-data=config;config",  # 添加配置目录
                "main.py"
            ]
        
        subprocess.check_call(cmd)
        print("✓ exe文件构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 构建exe文件失败: {e}")
        return False


def create_portable_package():
    """创建可移植的软件包"""
    print("正在创建可移植软件包...")
    
    # 创建发布目录
    release_dir = "FacebookFriendChecker_Release"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 复制exe文件
    exe_source = os.path.join("dist", "Facebook好友可见性检查工具.exe")
    if os.path.exists(exe_source):
        shutil.copy2(exe_source, release_dir)
        print(f"✓ 已复制 {exe_source} 到 {release_dir}")
    else:
        print(f"✗ 未找到exe文件: {exe_source}")
        return False
    
    # 复制示例文件
    if os.path.exists("example_links.txt"):
        shutil.copy2("example_links.txt", release_dir)
        print(f"✓ 已复制示例链接文件到 {release_dir}")
    
    # 创建说明文件
    readme_content = """Facebook好友可见性检查工具 v1.0

使用说明：
1. 运行 FacebookFriendChecker.exe
2. 设置线程数量（默认为1）
3. 在Cookie输入框中填入Facebook Cookie字符串
4. 点击"上传文件"按钮，选择包含Facebook链接的文本文件
5. 点击"开始检查"按钮
6. 等待检查完成，查看结果

链接文件格式：
每行格式为：链接----名字
例如：https://www.facebook.com/profile1----张三

如何获取Facebook Cookie：
1. 在浏览器中登录Facebook
2. 打开开发者工具 (F12)
3. 进入 Application/存储 标签
4. 找到 Cookies -> https://www.facebook.com
5. 复制所有Cookie

注意事项：
- Cookie会过期，需要定期更新
- 建议不要设置过多线程
- 确保网络连接稳定
- 首次运行会自动下载ChromeDriver

技术支持：
如有问题请查看README.md文件

免责声明：
本工具仅供学习和研究使用，请遵守Facebook的服务条款。
"""
    
    with open(os.path.join(release_dir, "使用说明.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✓ 可移植软件包已创建在 {release_dir} 目录中")
    return True


def clean_build_files():
    """清理构建文件"""
    print("正在清理构建文件...")
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 已删除 {dir_name} 目录")
    
    # 删除spec文件（如果存在）
    if os.path.exists("FacebookFriendChecker.spec"):
        os.remove("FacebookFriendChecker.spec")
        print("✓ 已删除 FacebookFriendChecker.spec 文件")


def main():
    """主函数"""
    print("=" * 60)
    print("  Facebook好友可见性检查工具 - 构建脚本")
    print("=" * 60)
    print()
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("✗ 错误：需要Python 3.8或更高版本")
        print(f"  当前版本：Python {sys.version}")
        return False
    
    print(f"✓ Python版本：{sys.version}")
    print()
    
    # 询问是否清理之前的构建文件
    if os.path.exists("build") or os.path.exists("dist"):
        print("检测到之前的构建文件")
        choice = input("是否清理之前的构建文件？(y/n): ").strip().lower()
        if choice == 'y':
            clean_build_files()
            print()
    
    # 安装依赖
    if not install_requirements():
        return False
    
    print()
    
    # 安装PyInstaller
    if not install_pyinstaller():
        return False
    
    print()
    
    # 构建exe文件
    if not build_exe():
        return False
    
    print()
    
    # 创建可移植软件包
    if not create_portable_package():
        return False
    
    print()
    print("=" * 60)
    print("  构建完成！")
    print("=" * 60)
    print()
    print(f"可执行文件位置: {os.path.join('dist', 'FacebookFriendChecker.exe')}")
    print(f"发布包位置: {os.path.abspath('FacebookFriendChecker_Release')}")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\n构建失败，按任意键退出...")
            sys.exit(1)
        else:
            input("\n构建成功，按任意键退出...")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n用户中断构建过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
        sys.exit(1)