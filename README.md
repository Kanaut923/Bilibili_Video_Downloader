# 📺 Bilibili Video Downloader (B站视频下载器)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-ttkbootstrap-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

一个基于 Python 和 Tkinter (ttkbootstrap) 开发的现代化 Bilibili 视频下载工具。支持扫码登录以获取 4K/1080P+ 高画质，支持批量下载、音频提取、封面嵌入等功能。

<img width="1097" height="1446" alt="image" src="https://github.com/user-attachments/assets/5d7f30ac-59ff-4556-883f-f326bd61629e" />


## ✨ 主要功能 (Features)

*   🎨 **现代化 GUI 界面**：基于 `ttkbootstrap` 的 Superhero 主题，操作直观简洁。
*   🔐 **扫码登录**：内置二维码登录功能，无需抓包，安全获取 Cookie。
*   💎 **解锁高画质**：登录后支持下载 **4K 超清、1080P+ 高码率、杜比视界、HDR** 等会员/登录专享画质。
*   🎵 **多种输出模式**：
    *   **合并导出 (默认)**：下载视频+音频并无损合并为 MP4。
    *   **仅音频**：提取高品质音频并保存为 M4A (支持 Hi-Res/杜比全景声)。
    *   **仅视频**：仅下载无声视频画面。
*   🖼️ **封面嵌入**：自动下载高清封面并将其**写入视频元数据**，在资源管理器中直接显示封面。
*   📂 **批量下载**：自动解析视频列表（分P），支持多选下载。
*   ⚙️ **智能配置**：自动记忆登录状态（Cookie）和上次使用的下载路径。
*   🛠️ **FFmpeg 智能检测**：自动识别内部打包的 FFmpeg、同目录文件或系统环境变量。

## 📥 下载与安装 (Download)

### 方式一：下载绿色免安装版 (推荐)
1.  进入本仓库的 [**Releases**](https://github.com/你的用户名/你的仓库名/releases) 页面。
2.  下载最新的 `BiliDownloader_v1.0.zip` (或 exe)。
3.  解压后双击 `BiliDownloader.exe` 即可直接使用。
    *   *注：发布版已内置 FFmpeg，无需额外配置环境。*

### 方式二：源码运行 (For Developers)

如果您想自己修改代码或从源码运行，请按以下步骤操作：

#### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
```

#### 2. 安装依赖
请确保已安装 Python 3.8+，然后运行：
```bash
pip install -r requirements.txt
```
*(如果没有 requirements.txt，请手动安装以下库)*：
```bash
pip install requests ttkbootstrap qrcode pillow
```

#### 3. 配置 FFmpeg
本程序依赖 **FFmpeg** 进行音视频合并。
*   下载 `ffmpeg.exe` (推荐从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载)。
*   将 `ffmpeg.exe` 放入脚本同一目录下，或者将其添加到系统的 PATH 环境变量中。

#### 4. 运行
```bash
python spider.py
```

## 📖 使用指南 (Usage)

1.  **输入链接**：在上方输入框粘贴 B 站视频链接 (支持 `BV` 号)，点击 **Analyze URL**。
2.  **扫码登录 (推荐)**：
    *   点击右上角的 **Login via QR Code**。
    *   使用手机 B站 App 扫码。
    *   登录成功后，状态栏会显示 "Logged In"，此时可解锁 1080P+ 及以上画质。
3.  **选择分P**：解析完成后，左侧列表会显示所有分 P，支持多选或全选。
4.  **选择画质与格式**：在右侧选择视频画质、音频音质以及输出模式（默认为合并）。
5.  **设置路径**：点击 Browse 选择保存文件夹。
6.  **开始下载**：点击 **Download Selected**，等待下载完成。

## 🛠️ 技术栈 (Tech Stack)

*   **GUI**: [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) (Tkinter wrapper)
*   **Network**: [Requests](https://docs.python-requests.org/)
*   **Media Processing**: [FFmpeg](https://ffmpeg.org/)
*   **QR Code**: [qrcode](https://pypi.org/project/qrcode/) & [Pillow](https://python-pillow.org/)
*   **Packaging**: PyInstaller

## ⚠️ 免责声明 (Disclaimer)

*   本项目仅供**个人学习和研究**使用。
*   下载的内容版权归原作者和 Bilibili 所有。
*   请勿将本工具用于任何商业用途或非法分发版权内容。
*   使用本工具产生的任何后果由用户自行承担。

## 📄 License

[MIT License](LICENSE)

---
**如果觉得好用，请给个 Star ⭐️ 吧！**
