# CS329Z 学习资料

课程：Stanford CS329Z — Engineering AI Agents，Fall 2026。
资料核查与下载日期：2026-10-23（Asia/Shanghai）。
官网：https://cs329z.stanford.edu/

## 从这里开始

1. 阅读课程安排和要求，确认先修知识。
2. 阅读 Lecture 01、Lecture 02 和下方两篇入门阅读。
3. 阅读 HW1 handout，再根据 HW1 README 准备环境。

## 已发布课件

| 课件 | 主题 |
| --- | --- |
| [Lecture 01](slides/lecture01.pdf) | Introduction — What Are Agentic Systems? |
| [Lecture 02](slides/lecture02.pdf) | LLMs for Builders |
| [Lecture 03](slides/lecture03.pdf) | Retrieval-Augmented Generation (RAG) |
| [Lecture 04](slides/lecture04.pdf) | Tool Use & Function Calling |
| [Lecture 05](slides/lecture05.pdf) | Frameworks & Orchestration |
| [Lecture 06](slides/lecture06.pdf) | Agent Design Patterns & Scaffolds |
| [Lecture 07](slides/lecture07.pdf) | Agent Memory Architectures |
| [Lecture 08](slides/lecture08.pdf) | Multi-Agent Systems |
| [Lecture 09](slides/lecture09.pdf) | Optimization |

以上为下载时官网公开链接的全部九份讲义；后续课件尚未链接，不推测下载地址。

## 课程信息快照

- [课程主页与完整阅读列表](course/overview.html)
- [先修要求、作业、评分与 AI 使用规则](course/logistics.html)

HTML 保存的是页面源码快照，外部样式、图片和链接仍可能需要联网。最新安排以官网为准。
官方先修要求：CS224N、CS224U、CS224V、CS336 任一，或同等 NLP 背景。
录播要求登录课程 Canvas，本资料包不包含视频。
课程官网当前列出两份作业；HW2 尚未提供公开下载链接。

## HW1：Building an Agentic Harness

- [正式题目说明（英文 PDF）](assignment1/handout.pdf)
- [中文 PDF（按原版样式排版）](assignment1/handout.zh-CN.pdf)
- [完整中文译文 Markdown](assignment1/handout.zh-CN.md)
- [环境、运行与测试说明](assignment1/README.md)
- [官方 starter repository](https://github.com/cs329z/assignment1-harness)

本目录保存题目、译文和参考资料；作业代码与测试在仓库根目录，邮件压缩包在 `data/emails.jsonl.gz`。
环境要求：Python 3.11+、uv、OpenRouter API key。确定性测试不调用模型，live 测试收费。
初始代码的 NotImplementedError 属于预期状态。实际配置以作业 README 为准。

## 入门阅读（在线链接，未下载）

- [The Shift from Models to Compound AI Systems](https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

其他论文按每讲需要从课程主页访问，本次未批量下载。

## 来源与校验

[manifest.json](manifest.json) 逐项记录原始 URL、下载状态、文件大小和 SHA-256。
课件与课程页面保留原作者权利，公开可访问不等于允许再分发；此目录用于本地学习，未发布。
作业代码原仓库标注 MIT license，根目录保留原 LICENSE。课件和题目保留原作者权利，不因放入仓库而自动适用代码许可证；公开分发授权仍待确认。

## 学习记录

- [当前进度与待修问题](HW1_PROGRESS.md)
- [BM25 建索引与查询优化](assignment1/BM25优化笔记.md)

中文译文与笔记是个人学习辅助材料，可能存在错误，以英文原题为准。仓库外原始资料副本保留；后续优先维护仓库内本目录。
