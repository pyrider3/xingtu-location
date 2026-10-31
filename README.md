# 星图定位

Linux 桌面端 iPhone 模拟定位工具。在地图上选点或搜索地点，应用每 5 秒更新模拟位置；连接中断后自动重试。关闭窗口时停止后台并尝试恢复真实定位。

## 安装与启动

需要 Linux、Python 3、GTK 3、WebKit2GTK 4.1、PyGObject、usbmuxd 和 libimobiledevice 工具，以及已解锁并信任电脑的 iPhone。iOS 16 及以上需开启开发者模式。地图和搜索需要联网。

```sh
python3 -m venv .venv
.venv/bin/pip install pymobiledevice3
./启动.sh
```

在 Arch Linux 上，系统依赖可通过 `sudo pacman -S python-gobject gtk3 webkit2gtk-4.1 usbmuxd libimobiledevice` 安装。其他发行版的包名可能不同。

连接手机，在地图点击或搜索目的地，然后点击“开始模拟定位”。iOS 版本及应用的定位策略会影响效果，请在手机地图中确认。停止时若无法确认真实定位恢复，请重启 iPhone。

地图由 OpenStreetMap 提供，地点搜索使用 Nominatim；搜索内容会发送至 Nominatim 服务。程序在本机 127.0.0.1:8765 启动本地服务，关闭应用窗口时退出。地图通过 CDN 加载 Leaflet。

本工具基于 pymobiledevice3 的开发者模拟定位功能，iOS 27.2 曾出现连接中断，应用会尝试重连，无法保证始终生效。
