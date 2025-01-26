# Heck2API

基于 [@SMNETSTUDIO/Heck2API](https://github.com/SMNETSTUDIO/Heck2API) 的 go 版本改编实现。

## 功能特点
- 提供多种大型语言模型的无key访问
- 仅用于学术研究和交流学习

## 支持模型
- gpt-4o-mini
- deepseek-chat
- claude-3-haiku
- gemini-1.5-flash

## Docker部署
### 拉取
```bash
docker pull mtxyt/heck2api:1.3
```
### 运行
```bash
docker run -d -p 8802:8802 mtxyt/merlin2api:1.0
```
如果你想配置uuid或key可以用
```bash
docker run -d -p 8001:8001 -e UUID=your_uuid -e AUTH_TOKEN=your_token mtxyt/merlin2api:1.0
```

## 声明
本项目仅供学术交流使用，请勿用于商业用途。

## 致谢
感谢 [@SMNETSTUDIO](https://github.com/SMNETSTUDIO) 的原创项目支持。
