# Facebook好友可见性检查工具

一个基于PyQt5和Selenium的Facebook用户主页好友列表可见性检查工具。

## 功能特性

- 🖥️ 友好的图形用户界面
- 🔄 支持多线程检查
- 🍪 支持多个Cookie账号轮询使用
- 📁 批量导入Facebook用户链接
- 📊 实时显示检查进度和结果
- 📦 可打包成单个可执行文件

## 项目结构

```
facebook5/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包列表
├── build.spec             # PyInstaller打包配置
├── config/                # 配置模块
│   ├── __init__.py
│   └── settings.py
├── core/                  # 核心功能模块
│   ├── __init__.py
│   ├── cookie_manager.py  # Cookie管理
│   ├── browser_automation.py  # 浏览器自动化
│   └── friend_checker.py  # 好友可见性检查
├── gui/                   # GUI界面模块
│   ├── __init__.py
│   └── main_window.py     # 主窗口
├── utils/                 # 工具模块
│   ├── __init__.py
│   └── file_parser.py     # 文件解析
└── logs/                  # 日志目录
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 运行程序

```bash
python main.py
```

### 2. 准备链接文件

创建一个文本文件，每行格式为：`链接----名字`

示例：
```
https://www.facebook.com/profile1----张三
https://www.facebook.com/profile2----李四
https://www.facebook.com/profile3----王五
```

### 3. 获取Facebook Cookie

1. 在浏览器中登录Facebook
2. 打开开发者工具 (F12)
3. 进入 Application/存储 标签
4. 找到 Cookies -> https://www.facebook.com
5. 复制所有Cookie，格式如：
   ```
   datr=hxFAaaXmlgTZvHrFWafttpbB;sb=hxFAaQ4_EaarsaJDxgYyXggK;ps_l=1;ps_n=1;c_user=100094724526839;...
   ```

### 4. 使用工具

1. 设置线程数量（默认为1）
2. 在对应的Cookie输入框中填入Cookie字符串
3. 点击"上传文件"按钮，选择准备好的链接文件
4. 点击"开始检查"按钮
5. 等待检查完成，查看结果

## 打包成EXE

### 方法1：使用Python打包脚本（推荐）

运行Python打包脚本，它会自动完成所有步骤：

```bash
python build.py
```

脚本会自动：
1. 检查Python版本
2. 安装所有依赖包
3. 安装PyInstaller
4. 执行打包命令
5. 创建可移植的发布包
6. 生成使用说明文件

### 方法2：使用批处理脚本打包（Windows）

Windows用户可以直接双击运行 `build.bat` 文件。

### 方法3：使用spec文件打包

```bash
# 先安装依赖
pip install -r requirements.txt

# 执行打包
pyinstaller build.spec
```

### 方法4：直接打包

```bash
# 先安装依赖
pip install -r requirements.txt

# 执行打包
pyinstaller --onefile --windowed --name FacebookFriendChecker main.py
```

### 打包结果

打包完成后，可执行文件位于 `dist/FacebookFriendChecker.exe`。

**注意**：
- 首次打包可能需要较长时间（几分钟到十几分钟）
- 打包后的EXE文件较大（约100-200MB），这是正常的
- 确保已安装Python 3.8或更高版本
- 打包过程中会自动下载ChromeDriver，需要网络连接

## 注意事项

1. **Cookie有效期**：Facebook Cookie会过期，需要定期更新
2. **线程数量**：建议不要设置过多线程，以免被Facebook限制
3. **网络连接**：确保网络连接稳定
4. **浏览器驱动**：程序会自动下载ChromeDriver，首次运行可能需要一些时间
5. **账号安全**：使用Cookie时请注意账号安全，不要分享给他人

## 技术栈

- **GUI框架**: PyQt5
- **浏览器自动化**: Selenium
- **驱动管理**: undetected-chromedriver（自动处理ChromeDriver，绕过反爬虫检测）
- **打包工具**: PyInstaller

## undetected-chromedriver 优势

本项目使用 `undetected-chromedriver` 替代传统的 `webdriver-manager`，具有以下优势：

1. **自动版本匹配**：自动检测Chrome浏览器版本并下载匹配的ChromeDriver
2. **绕过检测**：自动修补ChromeDriver，绕过网站的反爬虫检测
3. **无需手动配置**：不需要手动下载或配置ChromeDriver
4. **更好的兼容性**：解决了WinError 193等常见的ChromeDriver错误
5. **持续更新**：跟随Chrome浏览器更新，保持兼容性

## 模块说明

### config/settings.py
- 存储项目配置信息
- 包括Facebook URL、浏览器配置、默认设置等

### core/cookie_manager.py
- 解析Cookie字符串
- 恢复Cookie到浏览器
- 验证Cookie有效性

### core/browser_automation.py
- 创建和管理Chrome浏览器实例
- 页面导航和加载
- 页面元素操作

### core/friend_checker.py
- 检查用户主页好友列表可见性
- 分析页面内容判断好友列表状态

### utils/file_parser.py
- 解析用户上传的链接文件
- 验证Facebook URL格式

### gui/main_window.py
- 创建主窗口界面
- 处理用户交互
- 显示检查结果

## 常见问题

### Q: 程序无法启动？
A: 请确保已安装所有依赖包，使用 `pip install -r requirements.txt` 安装。

### Q: 出现 "WinError 193 %1 不是有效的 Win32 应用程序" 错误？
A: 本项目已使用 `undetected-chromedriver`，该库会自动处理ChromeDriver的版本匹配问题。如果仍然遇到问题：

**方法1：重新安装依赖**
```bash
pip uninstall -y undetected-chromedriver
pip install undetected-chromedriver
```

**方法2：确保Chrome浏览器是最新版本**
- 访问 https://www.google.com/chrome/ 下载最新版Chrome
- 程序会自动下载匹配的ChromeDriver

**方法3：清理缓存**
```bash
# 删除目录: C:\Users\你的用户名\.wdm\drivers\chromedriver
```

### Q: Cookie无效？
A: Cookie可能已过期，请重新获取最新的Cookie。

### Q: 检查结果不准确？
A: Facebook页面结构可能发生变化，需要更新检查逻辑。

### Q: 打包后的EXE文件很大？
A: 这是正常的，因为包含了所有依赖库。可以使用UPX压缩减小体积。

## 许可证

本项目仅供学习和研究使用。

## 免责声明

使用本工具时请遵守Facebook的服务条款和用户协议。本工具不对使用本工具造成的任何后果负责。