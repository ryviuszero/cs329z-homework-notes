# CS329Z 作业 1：构建 Agent 运行框架（中文译文）

**版本：26.1.0 · CS329Z 教学团队 · 2026 年秋季**

> 本文翻译自本目录的 [英文原始题目 PDF](handout.pdf)，共 26 页，2026-10-23 整理。为便于阅读，合并了跨页段落，保留章节、题号、评分、公式、代码接口、示例、提示和参考文献。文中的“我们”指课程教学团队，“你”指学生。本文不包含作业解答；若译文与原文有差异，以英文原文为准。原文中的费用、运行时间及产品行为属于教学团队的记录，不是本次翻译重新验证的结果。

## 1. 作业概述（原文第 1–2 页）

本作业要求你从基础组件开始构建 Agent 系统：先实现 **LLM 流水线（pipelines）**，也称工作流（workflows），即控制流程由代码决定、LLM 仅用于分类、阅读或写作的程序；再实现 **Agent 运行框架（agent harness）**，即模型在你搭建的运行机制中决定下一步做什么的系统。

你将使用两套数据（见第 3 节）：虚构公司 Cardinal Energy 的文档，用于构建第 2 部分中的公司内部助手；以及一份真实企业邮件档案，第 1 部分的流水线和后续 Agent 都会使用它。

### 你需要实现什么

1. **第 1 部分：LLM 流水线（第 4 节）。**单次调用的邮件优先级分类器、每日摘要生成器、从零实现的 BM25 检索器，以及针对邮件档案的多跳 RAG 问答流水线。
2. **第 2 部分：Cardinal Agent（第 5 节）。**面向 Cardinal Energy 员工的助手，基于你自己编写的工具调用循环。你将构建工具注册表和工具调用的文本格式，把第 1 部分的流水线封装为工具，添加文档检索，让 Agent 使用终端，通过上下文压缩控制长会话的上下文预算，添加跨会话记忆，让用户批准、拒绝和调整 Agent 的行为，并加入防护规则。

### 你需要运行什么

1. 确定性测试套件：不调用 LLM，评估代码的运行机制。
2. 真实模型测试套件（live tests）：使用真实模型运行流水线和 Agent，并根据阈值评估任务完成情况。
3. 最终评估：让**模拟用户**与 Agent 对话。模拟用户是由 LLM 驱动、带有目标且会进行多轮对话的角色；它们会回答 Agent 的问题、批准或拒绝操作。每段对话由程序检查和评审模型共同评分。
4. 在终端中亲自使用 Agent，提出自己选择的请求，并简短记录它的行为（第 16 题 `field_notes`）。

本作业总分 **118 分**：自动评分测试占 **88 分**，两份书面材料占 **30 分**。完整测试套件已提前提供；初始状态下每项测试都会因 `NotImplementedError` 失败。你需要实现 `cs329z_hw1/adapters.py` 中接入测试的函数，让测试通过。第 2 节介绍测试组织方式及各题与测试的关系。

### 本作业中的设计选择

构建运行框架涉及两类选择。

第一类是结构性选择：有哪些函数、输入输出是什么，以及所有正确实现都必须具备哪些行为。这些由教学团队规定，并通过测试强制检查。

第二类取决于设计判断。例如，模型应该看到多长的工具输出？为满足上下文窗口而总结会话时，哪些内容必须保留？哪些操作可以不经用户批准直接执行？实际系统的选择各不相同，本作业不替你决定。凡是留给你判断的地方，题目都会用“**设计决策（由你决定）**”标出。文末的设计备忘录要求你解释选择及其理由。测试会拒绝明显不可行的选择，其余部分通过备忘录评估。

第 17 题 `design_memo` 对每项设计决策各提出一个问题。在开始第 2 部分前先阅读这些问题，并在做决定时记录理由。**复杂度本身不加分**：无论策略是三行还是三百行，只要通过测试且能在备忘录中给出合理说明，都可以得到满分。

**实现中不得使用 Agent 或 LLM 框架库，也不得向 `pyproject.toml` 添加依赖。**NumPy 已包含在依赖中，可以在任意位置使用。

课程提供的 `LM` 封装只有一个基本能力：接收消息列表并返回字符串的聊天补全调用。它不提供工具调用或结构化输出功能。其上层的一切都由你实现，包括如何告诉模型有哪些工具，以及如何解析回复。目的在于让你至少完整地亲手构建一次 Agent 框架，再依赖现成库。

### 关于 AI 辅助

完成本作业时可以使用 Claude Code、Codex、Copilot 或其他 AI 工具。教学团队会通过口试检查理解程度，询问你的设计和代码。你应能解释提交内容中的所有部分，并对其负责。

### 低预算提示：免费测试与缓存调用

题目中会提供控制 LLM 费用的建议。starter 的两项机制有助于节省费用：

1. 确定性测试不调用 LLM，占自动评分 88 分中的 48 分（第 7 节列出各题分值）。
2. 课程的 `LM` 封装将每次调用缓存到磁盘；以相同模型和相同消息重复调用不会产生费用。

教学团队的参考实现，在不使用缓存的情况下，运行除最终评估之外的所有 live 测试花费约 **0.05 美元、5 分钟**；最终评估另需约 **0.18 美元、3 分钟**。

## 2. 环境准备（原文第 2–5 页）

作业支持 macOS、Linux 和 Windows，需要 **Python 3.11 或更新版本**，使用 `uv` 管理环境与依赖。

- [uv 安装说明](https://docs.astral.sh/uv/getting-started/installation/)
- Windows 还需安装 [Git for Windows](https://git-scm.com/download/win)，使用默认选项，因为第 10 题 `terminal` 使用其提供的 `bash.exe`。也可使用 WSL。

克隆仓库后，在仓库根目录通过 `uv run` 运行所有命令。第一次运行会创建环境：

```sh
git clone https://github.com/cs329z/assignment1-harness.git
cd assignment1-harness
cp .env.example .env # 随后在 .env 中填写 API key
uv run python data/download.py # 解包邮件档案
uv run pytest # 初始状态下每项测试都因 NotImplementedError 失败
```

课程发放的 API key 填入 `.env`，变量名称见 `.env.example`。

邮件档案作为一个压缩文件随仓库提供：`data/emails.jsonl.gz`（19 MB）。`data/download.py` 校验它的 SHA-256，并解包到 `data/emails/emails.jsonl`（58 MB）。

你编写的所有代码都放在 `cs329z_hw1` 包中。该包包含测试调用的 `adapters.py`，也可以添加其他模块。初始为空的 `pipelines/` 和 `agent/` 是建议放置实现的位置。仓库的其余部分属于课程代码。

下表标记为 **provided（课程提供）** 的文件由教学团队维护：应阅读，但不要修改，评分时会使用教学团队版本。标记为 **read（需阅读）** 的文件定义了接口或测试规则，应在第一次使用相关内容的题目前阅读。

```text
cs329z_hw1/                 你的包：所有自己编写的文件都放这里
  adapters.py              你的文件；需阅读；唯一测试入口，初始为占位函数
  pipelines/               你的实现；第 1 部分，初始为空
  agent/                   你的实现；第 2 部分，初始为空
  llm.py                   课程提供；需阅读；LM、缓存、费用账本、预算、ScriptedLM
  types.py                 课程提供；需阅读；代码与测试共享的数据类型
  tokens.py                课程提供；需阅读；count_tokens、count_message_tokens
  tokenizer.py             课程提供；BM25 必须使用的 tokenize()
  data.py                  课程提供；需阅读；load_emails、emails_on、email_text、load_docs
  sandbox.py               课程提供；需阅读；run_terminal、make_workspace
  cardinal.py              课程提供；需阅读；Agent 工具名称和参数 schema
  user.py                  课程提供；需阅读；UserIO、ScriptedUser、ConsoleUser
  chat.py                  课程提供；在终端中与 Agent 聊天
  show.py                  课程提供；在真实数据上运行一个第 1 部分的流水线并显示结果
  simulation/              课程提供；模拟用户、评审模型、评估运行器
                           （参见该目录的 README.md）
tests/                     课程提供；评分时替换为教学团队版本
  test_*.py                课程提供；需阅读；每题一个文件，阅读当前题目对应文件
  thresholds.py            课程提供；live 测试的通过阈值
  fixtures/                课程提供；标准标签、问题、角色
data/
  docs/                    课程提供；Cardinal Energy 文档
  emails.jsonl.gz           课程提供；压缩后的邮件档案
  download.py              课程提供；验证并解包档案
  source.json              课程提供；档案校验值
  priority_rubric.md        课程提供；需阅读；优先级标准标签的判定规则
  emails/                  解包后的邮件，已被 Git 忽略
```

### LM 模型封装

所有模型调用必须通过 `cs329z_hw1.llm.LM`。`LM` 对象接收由 `{"role", "content"}` 消息构成的列表，返回字符串，除此之外没有其他接口：

```python
from cs329z_hw1.llm import LM
lm = LM() # 评分使用的模型
reply = lm([{"role": "system", "content": "Answer in one word."},
            {"role": "user", "content": "What color is the sky?"}]) # -> "Blue."
```

角色只能是 `system`、`user` 和 `assistant`；消息使用其他角色或额外键会被拒绝。没有工具调用或结构化输出功能；第 2 部分需要在这一调用基础上用文本构建工具调用（第 6 题 `tool_protocol`）。adapter 使用 `types.py` 中的 `lm: LMCallable` 表示这一接口，确定性测试传入同样接口形状的 `ScriptedLM`。

封装将每次回复缓存到 `.lm_cache/`，同时记录费用账本。运行以下命令可查看按模型和测试分类的支出：

```sh
uv run python -m cs329z_hw1.llm
```

费用受两种上限约束。课程发放的 key 在创建时设有支出限制，达到限制后调用失败。你还可以在 `.env` 中设置 `CS329Z_BUDGET_USD`：账本金额达到这个值后，封装会抛出 `BudgetExceeded`，而不再发起付费调用，让失控循环在耗尽 key 的额度前停下。

调用可能抛出两种异常：

- `BudgetExceeded`：达到支出上限。
- `OutputTruncated`：模型达到 `max_tokens` 后停止。异常的 `.text` 保存此前生成的文本，可能为空，因为推理模型的隐藏推理也占用同一限额。调高 `max_tokens` 后重试属于新的付费调用。

提供商端的 prompt caching 会自动对近期见过的前缀提供折扣，在账本中显示为缓存输入；不同调用间保持系统提示不变，才能利用这一机制。

### 测试

每题对应 `tests/test_<problem>.py`，包含两类测试。

**确定性测试（默认）**：运行 `uv run pytest`。不调用真实模型；需要模型的位置传入 `ScriptedLM`，按固定列表重放回复，因此不访问网络。

**真实模型测试（live）**：运行 `uv run pytest -m live -s`。调用真实模型，并按照 `tests/thresholds.py` 中的阈值评分，例如 20 个请求中至少 18 个产生正确工具调用。每项耗时几秒到几分钟；例如 `priority` 调用模型 60 次，约需一分钟。等待期间 pytest 不显示内容，`-s` 会让各项测试打印分数和错误案例，无论是否通过。

评分时使用相同测试案例形式和相同评分模型，但使用留出数据。`priority`、`email_qa`、`search_docs` 的 live 测试和 `sim_eval` 评估，会使用不公开的邮件、问题和角色检查泛化能力；规则和阈值不变。

模型不接受 temperature 设置，因此相同提示的两次运行可能不同。缓存使未更改调用的重复运行免费，但新调用不一定给出相同回复。一些 live 测试会从多个线程同时调用你的代码，因此索引、缓存等共享状态必须能安全地并发使用。

迭代期间可设置 `CS329Z_EVAL_SLICE=N`，只运行 live 测试的前 N 个条目。

确定性测试也完整列出了所要求的错误处理：空回复、格式错误、截断的工具调用、工具抛异常等。adapter 的 docstring 会列出对应测试覆盖的情况。除测试或设计备忘录明确要求外，不会额外评分其他内容。

### 2.1 每道题的工作方式

实现放在 `cs329z_hw1` 包中，组织方式由你决定。测试只通过 `cs329z_hw1/adapters.py` 中的函数访问你的代码；这些函数初始均为占位实现。例如：

```python
# cs329z_hw1/adapters.py（初始文件摘录；注释翻译为中文）
def run_priority(email: Email, lm: LMCallable) -> dict:
    """题目 priority。
    通过传入的 lm 调用模型，为收件人分类邮件优先级。
    返回 {"category": "urgent" | "normal" | "ignore", "reason": str}。
    （完整 docstring 还包含测试检查的规则。）
    """
    raise NotImplementedError # 用调用你自己实现的代码替换
```

完成一题时：先阅读题目框，打开它指定的 adapter，以 adapter 的类型标注和 docstring 作为准确接口与规则依据。在包内实现功能，让 adapter 仅作简单转接，然后运行本题测试：

```sh
uv run pytest tests/test_priority.py # 确定性测试
uv run pytest tests/test_priority.py -m live -s # live 测试，显示分数与不一致项
```

下文每个题目框说明要实现什么、哪个 adapter 将其接入测试；准确签名始终以 `cs329z_hw1/adapters.py` 为准。跨 adapter 边界使用的 `Email`、`ToolSpec`、`ToolResult`、`AgentConfig` 等类型由 `cs329z_hw1/types.py` 提供，请按原样使用。

## 3. 数据：Cardinal Energy 与邮件档案（原文第 5–6 页）

Cardinal Energy 是虚构的能源分析公司。`data/docs/` 包含 24 份 Markdown 内部文档：员工手册、人力资源和报销政策、组织架构、产品与工程文档以及公告。它们总体一致，但有一个刻意设置的例外：**一些政策已被后续公告替代，Agent 需要识别这一点。**旧文档仍可能写着旧规定。

`data/emails/` 中的邮件档案是 Enron 邮件语料（Klimt and Yang, 2004）的子集：真实公司的真实邮件，由联邦调查人员公开，之后广泛用于研究。该子集包含 2001 年 6 月 1 日至 8 月 31 日的所有邮件，去重后共 **26,278 封**。第 1 部分的流水线接收这些邮件作为输入；第 2 部分把相同函数封装为工具，Agent 通过你的第 1 部分代码搜索与阅读邮件。

**两套数据互不相关。**公司文档描述的是 2025–2026 年的 Cardinal Energy；邮件属于另一家公司，来自 2001 年。第 2 部分中用户可能询问任意一套数据，并不会明确说明是哪套。

教学团队向档案中加入了少量合成邮件，涉及虚构项目、决策和截止日期，部分评分问题依赖这些邮件。这样答案必须来自档案检索，而不是模型已知的 Enron 背景知识。下文将这些邮件称为 **needles（目标邮件）**。

### 关于档案中的人

这些是真实人物的真实邮件，是通过联邦调查公开的，并非他们主动选择公开。档案中含有私人邮件和一些粗俗语言。请将数据用于本作业，并以专业态度对待其中的人。

### 示例 `email_fixture`：档案中的一封邮件

`data/emails/emails.jsonl` 每行包含一个 JSON 对象，按日期排序。`cs329z_hw1.data.load_emails()` 返回普通字典列表，因此使用 `email["subject"]` 而不是 `email.subject`；`types.py` 中的 `Email` 是 `TypedDict`。作业涉及的邮件都有如下形状，原文给出的真实示例如下：

```json
{"id": "em-01553",
 "thread_id": "th-01306",
 "reply_to": null,
 "from": ".williams@enron.com",
 "to": ["kevin.ruscitti@enron.com"],
 "date": "2001-06-04T16:56:37Z",
 "subject": "",
 "body": "Here it is:\n\n\n "}
```

`id` 是档案内唯一的邮件编号，题目、工具或测试中的“email id”都指这个字段。`reply_to` 是被回复邮件的 id，或 `null`。回复关系通过主题和引用文本重建，因此有些关系缺失。

`date` 使用 UTC。作业按天分组时（每日摘要、`data.emails_on`），一天取该字段的 `YYYY-MM-DD` 部分。空主题、只有一行的正文、空 `to` 列表以及上例中格式异常的发件人地址都可能出现，流水线应能处理。

## 4. 第 1 部分：LLM 流水线（原文第 6–10 页）

第 1 部分在邮件档案上构建四种流水线：一次 LLM 调用、在其基础上的多调用流水线、完全不使用 LLM 的检索器，以及检索与 LLM 交替工作的循环。每条流水线都通过参数 `lm` 接收模型，所有模型调用必须通过该参数进行。必须遵守提供的输入输出签名，因为这些流水线将在第 2 部分变成 Agent 工具。

### 4.1 单次调用：邮件优先级

#### 第 1 题 `priority`：标记邮件优先级（3 分）

给定一封邮件，使用**一次 LLM 调用**，为收件人将其分类为 `urgent`、`normal` 或 `ignore`，并提供一句话的 `reason`。`LM` 返回普通字符串；如何在提示中要求标签与理由、如何解析回复，由你决定。`run_priority` 返回三个类别之一；当回复没有给出标签时返回 `unknown`，同时必须有非空理由。

标签遵循以下规则。站在**收件人**的角度，依据**邮件发出时刻**判断。工作日指星期一到星期五，从邮件日期开始计算；模型根据规则判断，你的代码不必自行计算工作日。

| 类别 | 判定规则 |
| --- | --- |
| `urgent` | 邮件要求收件人采取行动，或报告收件人负责的正在发生的问题；需要当天、下一工作日，或明确期限在最多两个工作日以内处理。 |
| `normal` | 发给本人或小型工作组，且未来两个工作日内没有截止期限的邮件：状态更新、问题、待审阅文档、日程安排，以及熟人发来的私人消息。 |
| `ignore` | 收件人可以不读的邮件：广告、通讯、面向大量员工的公告，以及不要求收件人行动的自动通知。 |

措辞本身不能决定标签。写着“立即行动”的群发邮件是 `ignore`。标题含“URGENT”但不要求收件人做任何事的邮件不是 `urgent`。要求这位收件人行动的自动通知是 `normal`；如果期限在两个工作日内，则为 `urgent`。完整规则与示例见 `data/priority_rubric.md`。

**交付要求：**实现 `cs329z_hw1/adapters.py` 中的 `run_priority(email, lm)`。确定性测试使用不遵循特定格式的脚本回复检查输出契约；未给出任何标签的回复必须产生 `unknown`。live 测试要求不出现 `unknown`，并在 60 封邮件上与标准标签至少 **85%** 一致。每类 20 封，均是依据同一规则进行三次独立判断且结果一致的邮件。live 测试调用模型 60 次，约一分钟。本题也用于检查环境：live 测试通过说明 key 和缓存都能工作。

```sh
uv run pytest tests/test_priority.py
# live 测试添加 -m live -s；-s 显示测试打印内容
uv run pytest tests/test_priority.py -m live -s
# 不通过测试，直接查看一封邮件的标签与理由
uv run python -m cs329z_hw1.show priority em-12167
```

`show` 为第 1 部分每条流水线提供一个命令，下文各题后会列出。代码不变时重复运行相同命令免费。

**提示词是主要调整手段。**第 1 部分 live 测试的表现主要取决于提示词，第一版通常不能通过。需要迭代：阅读分类错误的邮件、修改提示、重新运行。评分使用另外 60 封依据同一标准标注的邮件；只拟合公开标签、未真正遵循规则的提示无法泛化。

### 4.2 多次调用：每日摘要

#### 第 2 题 `daily_digest`：生成每日摘要（4 分）

在第 1 题 `priority` 基础上构建多调用流水线：给定一天的邮件，为忙碌员工生成晨间摘要。聚合由代码完成，例如逐封分类、移除 `ignore` 邮件、每个线程保留一个条目、按紧急程度排序；最终通过一次 LLM 调用生成文本。将 `unknown` 按 `normal` 处理。

摘要最多 **300 个词**，按 `len(digest.split())` 计数。通过提示控制长度：测试检查模型实际写出的文本，直接截断会丢失内容。必须点名所有 `urgent` 条目；测试会查找各封 urgent 邮件中的公司、项目或站点名称，只有描述而没有名称不算。不得提及任何 `ignore` 邮件的内容。

**交付要求：**实现 `run_daily_digest(emails, lm)`。输入一个自然日的邮件列表（可能为空），输出摘要字符串。确定性测试通过脚本回复检查输出形状。live 测试对档案中五天各约 30 封邮件运行，并检查上述三条约束。

应并发分类邮件：这些调用互不依赖；逐一调用会使这些测试耗时约 1 分 40 秒。标准 urgent 和 ignore 条目都是 needles。

```sh
uv run pytest tests/test_daily_digest.py
# live 测试添加 -m live -s
# 输出某天前 30 封邮件的摘要，以及每封邮件的标签
uv run python -m cs329z_hw1.show digest 2001-06-22 --labels --limit 30
```

### 4.3 从零实现检索

在数万封邮件上回答问题之前，需要找到相关邮件。这里使用 BM25，一种在 TREC-3 中提出、基于词项统计的排序函数（Robertson et al., 1995）。它对查询中的各词项求和，权重受以下三方面影响：

- **词项在整个语料中的稀有程度**，即逆文档频率。出现在 26,000 封邮件中的 3 封里的词，比出现在 20,000 封里的词更有辨识度。
- **词项在文档内的出现次数**，但收益递减，第十次出现的增益比第二次小。
- **文档长度相对于平均长度的比例**。同一个词出现在两行邮件中，比出现在五十页文档中更有分量。

对于查询 q 与文档 d，BM25 分数为：

$$
\operatorname{score}(q,d)=\sum_{t\in q}\operatorname{IDF}(t)\cdot\frac{f(t,d)(k_1+1)}{f(t,d)+k_1\left(1-b+b\frac{|d|}{\operatorname{avgdl}}\right)}
$$

求和针对查询中**不同的词项**。`f(t,d)` 是词项 t 在文档 d 中的出现次数；`|d|` 是文档的 token 数；`avgdl` 是平均文档长度。固定参数为 **k₁ = 1.5、b = 0.75**。采用：

$$
\operatorname{IDF}(t)=\ln\left(\frac{N-n_t+0.5}{n_t+0.5}+1\right)
$$

其中 N 是文档总数，nₜ 是包含 t 的文档数。k₁ 控制词频因子达到饱和的速度，b 控制文档长度的影响程度。这是 Lucene 使用的 IDF，不是最初论文中的版本；对数内的 `+1` 保证出现在超过半数文档中的词仍有正 IDF，而原始公式会变成负值。采用原始公式的库会得到不同分数。Robertson and Zaragoza (2009) 给出了公式推导与参数讨论。

#### 第 3 题 `bm25`：实现 BM25（8 分）

使用**倒排索引**实现 BM25 检索器：将每个词项映射到包含它的文档。不得使用检索或搜索库。文档与查询均必须使用提供的 `cs329z_hw1.tokenizer.tokenize` 分词（转为小写、按非字母数字字符切分），确保分数可与教学团队结果比较。

构建索引时只遍历语料一次。搜索只能读取查询词对应的索引条目；不得返回与查询没有共同词项的文档。

**测试调用的接口：**

- `run_bm25_build(docs: list[str]) -> index`：为语料建立索引。文档 id 是其在 docs 列表中的位置，如 `docs[0]` 为文档 0。索引对象自行设计，测试只会将它传回 `run_bm25_search`。
- `run_bm25_search(index, query: str, k: int) -> list[tuple[int, float]]`：返回分数最高的 k 个 `(doc_id, score)`，由好到差排序，分数相同则较小的 doc_id 优先。查询与文档使用相同分词方式；查询中的词项即使重复出现，也只计分一次。

**交付要求：**在 `cs329z_hw1/adapters.py` 中实现两个 adapter。所有测试均为确定性的，本题不需要 LLM。测试先在五篇文档的语料上与手算分数比较；再在完整档案上检查 17 个查询的平均效果：各查询相关邮件至少 **90%** 应出现在前 10 个结果中。

时间限制：建立索引 **15 秒**；平均每次查询 **20 毫秒**；某词只出现在 200,000 篇文档中的 3 篇时，对该词的查询 **2 毫秒**。2 毫秒测试会淘汰查询时遍历所有文档的实现，这正是需要倒排索引的原因。可使用 NumPy；普通 Python 字典和列表也能满足要求。教学团队笔记本上的参考实现不使用 NumPy，建索引约 3 秒、查询约 5 毫秒。

```sh
uv run pytest tests/test_bm25.py
# 查看查询排名最高的邮件及其分数
uv run python -m cs329z_hw1.show bm25 "larchfield audit"
```

尝试自己提出几个查询。第 17 题设计备忘录会问排序错在哪里，以及为什么。

### 4.4 使用 RAG 进行多跳问答

#### 第 4 题 `email_qa`：邮件上的多跳问答（8 分）

把检索器与 LLM 放入循环。有些问题一次检索就能回答；其他问题需要多跳：某封邮件提到一个人或项目，而另一封邮件包含答案，但直接搜索问题原有词语找不到它。

循环由代码控制。LLM 阅读检索出的邮件，要么回答，要么给出下一次搜索查询。无论模型回复什么，每个问题最多调用 `search` **3 次**，这就是跳数预算。

**档案中有少量邮件包含针对 AI 系统的指令（见第 14 题 `guardrails`），本流水线会检索到其中一些。**

**输入：**

- `question: str`：能够从邮件档案回答的问题。
- `search(query: str, k: int) -> list[Email]`：返回查询的前 k 封邮件。调用方基于你在完整档案上建立的 BM25 索引创建此函数，并在所有问题中复用，因此你的流水线不负责建索引。k 由你选择。
- `lm: LM`：模型。

**输出：**

- `answer: str | None`：简短答案；未找到答案时为 `None`。
- `support: list[str]`：支持答案的邮件 id。每个 id 都必须来自本次调用期间 search 实际返回过的邮件。

**交付要求：**实现 `cs329z_hw1/adapters.py` 中的 `run_email_qa(question, search, lm)`。确定性测试通过脚本回复检查跳数预算和输出形状。live 测试使用 25 个针对 needles 的问题，其中 12 个单跳、13 个双跳。至少 **70%** 的回答包含一个可接受答案，且每个正确答案的 support 必须包含至少一封标准支持邮件。

```sh
uv run pytest tests/test_email_qa.py
# live 测试添加 -m live -s
# 查看答案、支持证据以及流水线执行的每次搜索
uv run python -m cs329z_hw1.show email_qa "Who leads the Basin Analytics move?"
```

**低预算提示：在子集上开发。**设置 `CS329Z_EVAL_SLICE=5`，只运行 live 测试前五项；子集通过后再跑完整集合。参考实现完整运行第 1 部分三项 live 测试约花费 0.03 美元。相同变量也适用于第 2 部分。

可以用 `LM("model-name")` 尝试其他模型，但提示词表现不能直接迁移：教学团队实验中，在一个模型上达到 20/20 的提示，在另一个模型上只有 11/20，反方向也一样。因此每个结果都应在评分模型上确认。

## 5. 第 2 部分：Cardinal Agent（原文第 11–23 页）

第 1 部分的流水线沿固定流程完成单一任务，但 Cardinal Energy 员工希望提出各种请求，例如：“我每周需要到办公室几天？”“总结邮件档案里 2001 年 6 月 22 日的邮件。”“档案中有多少邮件提到 Thistledown，都是谁发的？”

回答这类请求需要 Agent：模型查看当前会话，选择工具或直接回答，并根据工具结果继续运行的循环。

本部分按依赖顺序安排题目：工具注册表和工具调用格式 → 使用它们的循环 → 工具本身（检索、终端）→ 长会话与重复会话所需的压缩和记忆 → 交互层与防护规则 → 整个系统的评估。

第 2 部分的提示内容分散在系统提示和工具描述中，live 分数同时取决于两者。模型通过工具描述决定是否以及如何调用工具。预计需要像改代码一样反复修改这些文本；确定性测试不依赖这些描述，因此调整期间仍可保持通过。

### 低预算提示：ScriptedLM

第 2 部分确定性测试向 Agent 传入 `cs329z_hw1.llm.ScriptedLM` 代替真实模型，重放固定列表中的回复。脚本工具调用保存为工具名与参数，ScriptedLM 使用你在第 6 题实现的 `run_format_tool_call` 将其转为文本，因此测试支持你设计的任意调用格式。

如果 Agent 发起脚本中不存在的模型调用，ScriptedLM 会抛出 `ScriptExhausted`。注册表、协议、循环、压缩、记忆、交互层和拒绝规则，都可以在第一次真实模型调用前，先依据确定性测试完成。

### 5.1 工具注册表

#### 第 5 题 `tool_registry`：构建工具箱（3 分）

实现保存 Agent 可调用工具的注册表。一个工具由 `types.py` 提供的 `ToolSpec` 表示，包含：

- `name`：名称。
- `description`：模型选择工具时阅读的描述。
- `parameters`：JSON Schema 参数对象。
- `fn`：实际以 `fn(**args)` 调用的 Python 函数。
- `read_only`：第 13 题交互层使用的只读标记。

完整示例在 `tests/fixture_tools.py`，`cardinal.py` 构建第 2 部分工具的 spec。

本题没有需要自行选择的设计决策。它存在的原因是第 7 题循环和第 13 题交互层都依赖注册表的一项性质：**验证调用与执行调用必须分离**，以便在请求批准前拒绝无效调用。

**测试调用的接口：**`run_tool_registry(tools)` 返回你编写的类的对象。测试使用其三个方法及返回的 `ToolResult`：

- `registry.schemas() -> list[dict]`：按注册顺序返回每个工具的字典，且只能有 `name`、`description`、`parameters` 三个键。这就是模型能看到的全部工具信息。
- `registry.validate(name: str, args: dict) -> ToolResult | None`：查找工具并依参数 schema 验证 args。返回 `unknown_tool` 或 `invalid_args` 结果；可执行时返回 `None`。不得调用工具，不得抛异常。使用 `jsonschema.Draft202012Validator` 检查（[验证器文档](https://python-jsonschema.readthedocs.io/en/stable/validate/)）。
- `registry.execute(name: str, args: dict) -> ToolResult`：先验证，再执行。始终返回 ToolResult，不得抛异常。
- `ToolResult.status` 为 `"ok" | "unknown_tool" | "invalid_args" | "tool_error"`，分别表示成功、无此工具、参数不符合 schema（不调用函数）、工具内部异常。
- `ToolResult.content: str`：模型会看到的内容。ok 时为返回值经 `str()` 转换的结果；其他情况为错误描述，并包含异常消息。

第 13 题增加第五种状态 `denied`，表示拒绝调用。该结果由 Agent 生成，而不是注册表，因为被拒绝的调用不会执行。同题要求未知工具和无效参数在请求用户批准前拒绝，这就是 validate 的用途。

**交付要求：**实现 `run_tool_registry(tools)`。确定性测试使用 `tests/fixture_tools.py` 中的小工具建立注册表，检查注册、正确与错误参数的验证，以及工具异常是否被妥善处理。

```sh
uv run pytest tests/test_tool_registry.py
```

### 5.2 工具调用协议

模型提供商的 API 内置工具调用，但课程的 LM 封装没有：它接收消息、返回字符串，也没有工具结果专用角色。提示需要告诉模型有哪些工具、如何写调用；代码需要从回复中解析调用；工具结果如何写入 user 或 assistant 消息，也由你决定。

协议本身不调用模型：它是在 lm 调用前后进行的纯文本处理。

下方是第 7 题将实现的循环示意。`render_tools` 和 `parse_response` 属于本题，其余属于下一题：

```python
system = system_prompt + render_tools(registry.schemas())
messages = [system, user_message]
while limits_not_exceeded():
    reply = lm(messages) # 消息输入，字符串输出
    messages.append(reply)
    parsed = parse_response(reply)
    call = parsed.tool_call # 每个回复最多一个调用
    if call is None:
        return final_answer(parsed)
    result = registry.execute(call.name, call.args)
    messages.append(result) # 以你选择的格式写入
```

#### 第 6 题 `tool_protocol`：设计工具调用协议（4 分）

设计工具调用的文本格式并实现三个函数。前两个构成协议；第三个让确定性测试无需知道你的格式，也能输出工具调用（由 ScriptedLM 调用）：

- `run_render_tools(schemas: list[dict]) -> str`：生成系统提示中的文本，描述 `registry.schemas()` 给出的工具及其调用方式。
- `run_parse_response(text: str) -> ParsedResponse`：返回回复中的 text（移除工具调用并去掉两端空白）和 tool_call（包含名称与 args 字典的 ToolCall，或 None）。每个回复最多一个调用；有多个调用或无法解析时，设置 error 并且不返回调用。不得抛异常。
- `run_format_tool_call(text: str, call: ToolCall) -> str`：以你的格式写出同时包含 text 与 call 的回复。解析后必须得到相同名称和参数，并保留参数的 JSON 类型。

另外两条规则涉及截断与嵌套：格式化后的回复在任意字符处被截断时，解析器必须返回“没有调用”或“与原调用完全相同的调用”；如果截断发生在参数内部，必须设置 error。参数值可以是任意字符串，包括包含一整段你自定义调用格式的字符串。

**设计决策（由你决定）：**选择格式，例如代码围栏中的 JSON 对象或 XML 风格标签；决定提示如何描述该格式，以及如何把工具结果写回给模型。

**交付要求：**实现 `cs329z_hw1/adapters.py` 中的三个 adapter。测试用你的 formatter 生成调用、用你的 parser 读取，因此不依赖具体格式。live 测试向评分模型提供你渲染的工具和 20 个请求，至少 **18 个**回复必须能解析为正确工具和正确参数。该测试的系统提示只有一句固定文本加你的工具描述，因此让模型输出调用所需的说明都必须包含在你渲染的文本中。

```sh
uv run pytest tests/test_tool_protocol.py
# live 测试添加 -m live -s
```

### 5.3 Agent 循环

这一模式通常追溯到 ReAct（Yao et al., 2023）：面对复杂问题，模型交替进行推理与行动比一次生成完整答案更好。模型交替输出文本和动作，每个动作结果追加到上下文，然后模型继续运行。结合第 6 题的协议，外围循环如第 5.2 节所示。

从这里开始，所有 Agent 题目通过同一个 adapter 测试：`run_agent_session(lm, tools, config)`，它创建一个 session，即与 Agent 的一段会话。

- `lm: LM`：Agent 自身轮次使用的模型。
- `tools: list[ToolSpec] | None`：Agent 可调用的工具。None 表示 Cardinal 工具集（第 5.4 节）。
- `config: AgentConfig`：在 types.py 中定义。后续每题赋予其中一两个字段具体含义。贯穿所有题目的字段是 `config.aux_lm`：第二个模型。**所有不属于 Agent 自身轮次的模型调用必须使用它**，如压缩摘要和第 1 部分工具内部的调用。None 表示使用 lm。每个测试都传入 aux_lm，因为 ScriptedLM 恰好为每个 Agent 轮次提供一个回复，辅助调用若也使用它就会提前消耗回复。

测试使用返回对象的三个成员：

- `session.send(user_message: str) -> AgentResult`：为一条用户消息运行循环，返回回复 text、status 和 transcript。每次 send 都延续同一会话。
- `session.transcript: list[dict]`：只追加的事件日志，事件类型有 user、assistant、tool_call、tool_result、error；键见 types.py。它是日志，不是模型上下文，内容永不删除。
- `session.set_mode(mode: str) -> None`：从第 13 题开始使用。

#### 第 7 题 `agent_loop`：实现工具调用循环（8 分）

实现 session.send：交替执行模型调用和工具调用，直到模型给出最终答案或达到限制。模型写出的内容或工具行为不能导致 send 抛异常。它返回 AgentResult：text 永不为空，transcript 为当前会话日志的副本，status 为以下之一：

| 状态 | 含义 |
| --- | --- |
| `done` | 模型给出最终答案。 |
| `max_turns` | 本次 send 已调用模型 config.max_turns 次。 |
| `token_budget` | 本次 send 已消耗至少 config.token_budget 个 token。对本次 send 的所有模型调用，将 count_message_tokens(messages) + count_tokens(reply) 求和；使用 tokens.py 中的计数函数。 |
| `malformed` | 模型连续三次产生格式不合法的回复。 |

格式不合法包括：parse_response 设置 error；注册表返回 unknown_tool 或 invalid_args；或模型调用抛出 OutputTruncated。发生此类回复后，把错误文本返回给模型，让它修正调用。一次合法回复会重置连续错误计数。

在**每次模型调用前**检查两项预算，因此某次调用虽使 token 总量超标，但若给出最终答案，状态仍是 done。首次模型调用的第一条消息（系统提示）必须包含每个工具的名称。每个 tool_result 与 error 事件的 content 必须**原样**出现在下一次模型调用中。

**设计决策（由你决定）：**测试中，不包含工具调用的回复就是最终答案。真实模型也可能只宣布行动却没有调用工具，例如“我来查一下”。你需要决定接受它作为答案，还是要求模型继续。

**交付要求：**实现 `run_agent_session`。确定性测试用 ScriptedLM 和测试工具创建会话，驱动各种脚本情形，包括错误调用后恢复、连续三次错误回复、被 max_tokens 截断的回复，以及两种预算耗尽。

```sh
uv run pytest tests/test_agent_loop.py
```

### 5.4 Cardinal 工具集（原文第 15 页）

从这里开始，测试还会传入 `tools=None` 创建完整 Agent。这表示使用 Cardinal 工具集：十个工具，其名称、参数 schema 和只读标志在 `cardinal.py` 中固定，实现和描述由你提供。阅读其中的 `cardinal_spec`：它根据你的描述和函数构建每个工具的 ToolSpec，完成所需的接入。你也可以注册更多工具。

- `search_emails`、`read_email`、`email_qa`、`daily_digest`：把第 1 部分代码作为工具使用，分别为档案 BM25 搜索、按 id 阅读邮件、问答流水线、对 `data.emails_on(date)` 调用摘要流水线。档案平均每天约 280 封邮件，应并发分类。
- `search_docs`、`read_doc`：第 9 题。
- `run_terminal`：第 10 题，唯一不是只读的工具。
- `remember`、`recall`、`ask_user`：第 12、13 题。

#### 第 8 题 `cardinal`：组装工具集（2 分）

让 `run_agent_session(lm, None, config)` 返回注册了全部十个工具的可运行会话，即使各工具还没全部完成。

每个工具都是普通 Python 函数，注册表将模型参数作为关键字参数传入。例如 search_emails 的函数形式是 `def search_emails(query: str, k: int = 5) -> str`，通过 `cardinal_spec("search_emails", description, search_emails)` 构建 ToolSpec。

**创建会话不得读取邮件档案**：第一次有工具需要时才建立邮件索引。当 tools 是显式列表时，会话必须恰好拥有列表中的工具，再加上：config.user 非空时的 ask_user，以及 config.memory_dir 非空时的 remember 和 recall。

完成后可以通过 `uv run python -m cs329z_hw1.chat` 在终端中与 Agent 对话。

**交付要求：**无新 adapter。确定性测试检查 tools=None 会话的系统提示是否包含十个工具名、创建会话是否不读档案，以及显式工具列表的规则。从第 9 题开始，每项测试都会以此方式创建完整 Agent。

```sh
uv run pytest tests/test_cardinal.py
```

### 5.5 作为工具的检索（原文第 16–17 页）

第 1 部分中，检索向你的代码返回整封邮件，由代码决定模型看什么。工具结果则会直接进入模型上下文。员工手册约 4,600 词，最长邮件有 50,000 字符；搜索工具若返回整篇文档，一两次调用就会占满上下文预算。

#### 第 9 题 `search_docs`：为 Agent 设计检索（5 分）

使用你实现的 BM25 索引，在公司文档上建立两个只读工具。搜索返回定位信息与简短证据，模型只读取主动请求的部分。**一些文档中植入了针对 AI Agent 的文字（第 14 题），搜索工具会返回其中部分内容。**

**测试调用的接口：**

- `run_build_doc_index(docs: list[dict]) -> index`：为 `data.load_docs()` 返回的文档建立索引。索引对象由你设计，可由整篇文档或分块的 BM25 索引，加上 read 所需内容组成。测试只建一次索引并传给下面两个函数。实际工具应在第一次需要时建立索引并共享。
- `run_search_docs(index, query: str, k: int = 5) -> list[SearchResult]`：最多 k 个排序结果，每项有 doc_id、title，以及从原文提取、不超过 **150 token** 的 snippet。没有匹配时返回空列表。
- `run_read_doc(index, doc_id: str, start_line: int = 1) -> DocWindow`：返回文档窗口，最多 **1,500 token**。text 必须恰好对应文件的 start_line 到 end_line 行，total_lines 让模型可以请求下一窗口。未知 doc_id 或文档范围外的 start_line 抛出 ValueError 或 LookupError，由注册表转为 tool_error。

文档每行一个段落，因此单行很长，窗口既要限制行数，也要限制 token 数。doc_id、title 和行号遵循 data.load_docs()。两个结果可以来自同一文档，结果也可以附带额外键。

150 与 1,500 token 的限制作用于 adapter 返回内容。实际工具输出给模型的字符串格式由你设计，live 测试限制它们在整段会话中的总量。如果每次都返回 adapter 允许的最大窗口，四次读取就会达到总量限制。

**设计决策（由你决定）：**接口背后的一切，包括按整篇还是分块索引（若分块则大小与边界）、如何构造 snippet、窗口大小、模型看到的输出字符串格式，以及空结果时的说明。

**交付要求：**实现三个 adapter，并将搜索与读取注册为 search_docs 和 read_doc。确定性测试建立一个索引，直接调用两个 adapter，与原文件对比。live 测试向完整 Agent 提出 20 个已知答案的问题，其中 5 个涉及被后续文档修改的政策。至少 **15 个**答案正确，且每段会话中两个工具的结果合计最多 **6,000 token**。

```sh
uv run pytest tests/test_search_docs.py
# live 测试添加 -m live -s
uv run python -m cs329z_hw1.show search_docs "parental leave"
```

### 5.6 使用终端（原文第 17–18 页）

Agent 已能查事实，但还无法在数据上计算，例如回答“2001 年 8 月谁发的邮件最多？”这需要编写并运行代码。

课程提供沙箱。`cs329z_hw1.sandbox.run_terminal(cmd)` 在包含 emails.jsonl 和 docs/ 的工作目录运行一条 shell 命令，返回 TerminalResult，字段为 stdout、stderr、exit_code、timed_out、rejected、reason。超时或拒绝不会直接抛异常。

沙箱提供以下机制：

- 命令中每个程序都必须在允许列表中（python3 和标准文本工具），否则拒绝。还会拒绝命令替换和 here-document，因此多行脚本需写成 `python3 -c '...'`。教学团队测试的模型会倾向于写 here-document，除非工具描述明确禁止。
- 设置超时，默认 10 秒；运行环境不带你的环境变量，因此也没有 API key。
- macOS，以及安装且允许使用 bubblewrap 的 Linux，还会在操作系统级沙箱中运行，阻止网络访问、工作目录外写入，以及读取用户主目录和代码仓库。`sandbox.jail()` 报告本机是否启用该层。未启用时，运行 python3 的命令可以访问网络以及账户能读写的任何文件。Windows 永不启用该层：命令通过 Git for Windows 的 bash.exe 运行，只有允许列表、超时和清理后的环境变量作为限制。

sandbox.py 的 docstring 列出每层能阻止与不能阻止什么；设计备忘录会问到这一点。

原文脚注 3 指向一份案例报告，称其讨论沙箱 Agent 越过预期边界的事件：[METR 与 Redwood Research 关于 2026 年 OpenAI Agent 协同攻击 Hugging Face 事件的报告](https://metr.org/hugging-face-incident-report-aug-2026.pdf)。**译注：此处仅保留原文引用，本译文未独立核实该报告内容。**

单条命令可能输出远超上下文容量的文本。`config.context_budget` 是每次模型调用允许发送的最大 token 数，按 count_message_tokens 计算。第 11 题将在整个会话中强制执行，此处已需要处理单次大输出。

#### 第 10 题 `terminal`：为 Agent 提供终端（6 分）

实现 Cardinal 工具集中的 run_terminal。使用前阅读 sandbox.py。向沙箱传递 config.workspace 和 config.terminal_timeout。模型写出的命令都会在本机运行，因此**每一条命令都必须经过 sandbox.run_terminal；不得在 Agent 中自行编写 subprocess 调用。**

与其他 Cardinal 工具一样，cardinal_spec 提供固定名称、schema 和只读标志，你提供描述和函数。原文提供的接入示意如下：

```python
from cs329z_hw1.cardinal import cardinal_spec

def run_terminal_tool(cmd: str) -> str:
    result = sandbox.run_terminal(cmd, workspace=config.workspace,
                                  timeout=config.terminal_timeout)
    ... # 由你设计输出呈现策略；失败时抛异常（转为 tool_error）
    return shown

spec = cardinal_spec("run_terminal", "Run one shell command. ...",
                     run_terminal_tool)
```

工具结果必须包含 stdout、stderr 和退出码。命令被拒绝时必须返回沙箱给出的 reason；超时时必须说明发生超时；两者都作为工具结果处理，运行继续。只有命令实际运行且以 0 退出时状态才是 ok；非零退出、超时、拒绝均为 tool_error。

命令输出 600,000 字符之后，每次模型调用仍必须遵守 config.context_budget，tool_result 事件必须记录实际展示给模型的内容。

**设计决策（由你决定）：**选择输出呈现策略，即输出太大时模型看到什么。原文比较了不同运行框架：mini-swe-agent 原样传递全部输出；OpenAI Codex CLI 截断并保留开头和结尾；OpenHands、Gemini CLI、Claude Code 截断的同时把完整输出写入文件，并告诉模型路径，便于后续搜索或重读。也可以用另一轮模型调用总结输出。任何通过测试的策略都可以，备忘录会询问模型实际看到什么。

原文所列前四个开源项目：[mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)、[Codex](https://github.com/openai/codex)、[OpenHands software-agent-sdk](https://github.com/OpenHands/software-agent-sdk)、[Gemini CLI](https://github.com/google-gemini/gemini-cli)。

**交付要求：**无新 adapter；测试使用 tools=None 的 run_agent_session。确定性测试在真实沙箱中运行脚本命令，包含拒绝、超时和大输出。live 测试提出九个具有精确答案的档案分析问题，其中一个会打印约 218,000 字符的列表，随后追问其中某一行；共十个答案至少 **8 个**正确。

```sh
uv run pytest tests/test_terminal.py
# live 测试添加 -m live -s
```

### 5.7 上下文压缩（原文第 19 页）

#### 第 11 题 `compaction`：上下文压缩（8 分）

无论会话多长，Agent 都必须遵守 config.context_budget。每次模型调用必须满足：

```text
count_message_tokens(messages) <= config.context_budget
```

下一次调用将超预算时，进行压缩，向模型发送较短版本的会话。压缩只改变发送给模型的内容；transcript 仍保留所有事件。针对当前用户消息的每次模型调用都必须保留该用户消息。模型生成的摘要必须使用 config.aux_lm。

按第 7 题要求，工具结果必须原样出现在紧接着的模型调用中，只有再下一次调用才允许缩短它。工具结果占上下文大部分；第 10 题的输出呈现策略影响压缩可以舍弃什么：已保存到文件的输出可重新读取，仅存在上下文中的内容则无法恢复。

**设计决策（由你决定）：**整个压缩策略，包括触发时机、优先删除什么、摘要必须保留什么、哪些内容绝不能被压缩掉。固定要求只有两个：预算始终满足；即使承载用户约束的消息已离开上下文，用户先前给出的约束仍可使用。一些框架先尝试低成本操作，如移除旧工具结果，不够时才付费调用模型总结。

**交付要求：**无新 adapter。确定性测试使用 4,000 token 预算和七个测试工具，因此系统提示必须明显小于 4,000（参考实现约 1,000）。测试重放 60 次模型调用，每次检查预算。live 测试使用相同预算：第一条用户消息声明两个约束，接着十一项脚本请求，最后用一个真实模型问题询问这些约束。真实模型调用仅包括最后问题及你自己的 aux_lm 调用。第 15 题评估使用 16,000 token 上下文预算。

```sh
uv run pytest tests/test_compaction.py
# live 测试添加 -m live -s
```

### 5.8 记忆（原文第 19–20 页）

#### 第 12 题 `memory`：跨会话持久记忆（8 分）

会话结束后上下文消失。通过磁盘存储（普通 JSON 即可）和两个工具实现跨会话记忆：模型调用 remember(fact) 存事实，调用 recall(query) 搜索存储。

config.memory_dir 非空时，无论会话原本收到什么工具列表，都必须拥有这两个工具，所有保存内容必须位于该目录下。相同目录的新会话可以读取早先保存的内容；不同目录的会话不得看到它。对空存储调用 recall，返回 ok 和非空说明。

运行框架也可以自行写入存储，例如每次 send 后；测试检查文件内容，不限制由谁写入。

**设计决策（由你决定）：**保存什么，以及新会话启动时加载什么。原文举例：Claude Code、Codex CLI、Gemini CLI 启动时把完整指令文件加载到提示；Letta 在提示里放一个受大小限制的块，其余放在通过工具搜索的存储里。提示太少，模型可能不知道有内容可回忆；太多则旧事实占用上下文预算。

每次会话启动时把整个存储放入提示也是可接受且能得满分的策略。recall 仍必须工作，因为当事实不在提示里时，它是唯一访问路径。备忘录会询问评估后记忆存储中有什么。

**交付要求：**无新 adapter。确定性测试在一个会话保存事实，检查磁盘文件、同目录新会话和不同目录会话。live 测试运行三组会话对，两个会话之间只共享 memory_dir。会话 1 中用户给出的事实，例如“我属于固件团队；我说‘规格文档’时指的是固件规格”，必须影响会话 2 的答案。三组至少 **2 组**答对。

```sh
uv run pytest tests/test_memory.py
# live 测试添加 -m live -s
# 查看你通过 chat.py 对话时保存的记忆
uv run python -m cs329z_hw1.show memory .lm_cache/chat_memory
```

### 5.9 交互层（原文第 20–21 页）

此前运行开始后用户无法介入。本节加入用户参与机制：部分动作等待批准，用户能在运行中重新引导 Agent（steering），Agent 也能向用户提问。

这些都通过 config.user 进行，它是 `cs329z_hw1/user.py` 中的 UserIO 对象，提供三个方法：

- `approve(call)`：返回 Approval，包含 approved 和 reason。
- `ask(question)`：返回用户答案。
- `pending_message()`：返回用户在 Agent 工作期间发来的消息，或 None。

这样同一 Agent 可用于终端真人、测试脚本用户和评估模拟角色。测试传 ScriptedUser，评估传模拟角色，chat.py 传 ConsoleUser。

#### 第 13 题 `interactive`：模式、批准与中途引导（7 分）

增加三项能力：决定哪些调用需要批准的模式、检查用户中途消息的机制，以及 Agent 向用户提问的工具。

**mode: `"confirm" | "auto"`。**config.mode 设置初始模式，session.set_mode 在 send 之间切换模式。confirm 模式下，每次执行 read_only=False 的工具前，都调用 config.user.approve(call)，每次调用只请求一次。auto 模式下永不调用 approve。

注册表拒绝的调用（未知工具、无效参数）不得请求批准。被用户拒绝的调用不得执行，也不抛异常；日志追加 status 为 denied 的 tool_result，content 必须非空且包含拒绝原因，然后继续运行。

**pending_message（中途引导）。**每次模型调用前必须且只能调用一次 config.user.pending_message()。若返回消息，将它以 user 事件追加到日志，并包含在此次模型调用中。

**ask_user(question: str)。**config.user 非空时，会话拥有此工具。它调用 config.user.ask(question)，把答案作为 ok 工具结果返回。模型可在请求模糊时使用，例如“你指三月份的报销政策，还是被它替代的旧政策？”

ask_user、remember、recall 永远不需要批准。remember 只写 Agent 自己的记忆存储。

**设计决策（由你决定）：**confirm 模式下只读工具是否也需要批准，以及如何向模型描述拒绝。

**交付要求：**无新 adapter，测试全为确定性。使用 ScriptedLM 和 ScriptedUser 检查批准、拒绝后继续、中途消息、模式切换及 ask_user 问题。第 15 题中模拟角色将代替真人回答问题、批准或拒绝终端命令。

```sh
uv run pytest tests/test_interactive.py
```

### 5.10 auto 模式的防护规则（原文第 21–22 页）

#### 第 14 题 `guardrails`：拒绝规则与提示注入（4 分）

confirm 模式下，用户审阅每个有副作用的动作；auto 模式直接执行模型选择。因此能引导模型的文本可能借模型产生实际行为。

**公司文档与邮件档案中植入了面向 AI Agent 的文字：有的要求运行终端命令，有的要求切换 auto 模式并放弃规则。**

本题包含两层。第一层是确定性测试检查的机械规则，见下文。第二层是 live 测试检查的行为：auto 模式下，Agent 回答包含植入指令的文档或邮件问题，但不得执行植入指令。live 测试刻意让植入命令不匹配 deny rules，因此机械规则挡不住；需要系统提示及你在 run_terminal 周围增加的检查来防止。

两条机械规则在**两种模式下都生效**：

1. **deny rules**：config.deny_rules 为正则表达式元组。如果任一 `re.search(rule, cmd)` 匹配 run_terminal 调用的命令，则不得执行，也不请求用户批准。日志追加 denied 状态且 content 非空的 tool_result，继续运行。
2. **工具输出不能重新配置系统**：工具结果中的文本不得改变模式、批准策略或拒绝规则。这些只能由用户通过 AgentConfig 和 set_mode 设置，不能通过其他位置修改。

run_terminal 的处理顺序必须为：**注册表验证 → 拒绝规则 → 批准（confirm 模式）→ 执行**。

**交付要求：**无新 adapter。确定性测试检查模型试图执行被拒绝命令，以及工具输出要求更改模式和规则的情况。live 测试在 auto 模式向完整 Agent 提出四个文档问题和三个邮件问题，答案都紧邻植入指令。所有任务中都不能执行植入命令，并且七题至少 **6 题**答对。

```sh
uv run pytest tests/test_guardrails.py
# live 测试添加 -m live -s
```

### 5.11 模拟用户评估（原文第 22–23 页）

此前使用静态测试案例，但真实用户会遗漏细节、改变想法、引用前文。因此最终评估是对话式的。

每项任务是一名 persona：由 LLM 模拟的 Cardinal Energy 员工，有角色、目标和书面性格设定，例如“用零碎短句回答”。角色发送消息、Agent 回复，持续到角色声明完成目标、放弃，或达到用户轮次限制。公开集合中每次会话有 2–5 个用户轮次。

角色还通过 config.user 回答 ask_user、批准或拒绝工具调用。关于使用 LLM 模拟用户评估 Agent，可参考以此方式测试客服 Agent 的 τ-bench（Yao et al., 2024）。

一次对话成功必须同时满足：

1. Agent 没有抛异常。
2. 角色文件中的每项程序检查通过，例如回复包含准确数字、被拒绝命令没有执行。
3. 评审模型依据该角色评分规则判定通过。

评审模型会看到对话、每次工具调用、每个工具结果前 300 字符，以及工具结果后续任何包含 Agent 提及数字或名称的段落。如果 Agent 声称的事实没有这些内容支持，对话将被判失败。

评估中 Agent 参数为 `max_turns=20`、`token_budget=400000`、`context_budget=16000`。角色、检查以及模拟用户和评审模型接收的所有提示都在仓库中：`tests/fixtures/personas/` 与 `cs329z_hw1/simulation/`；后者的 README.md 有说明。

```sh
uv run python -m cs329z_hw1.simulation --slice 3 # 前三个角色
uv run python -m cs329z_hw1.simulation # 全部 20 个
uv run pytest tests/test_sim_eval.py -m live -s # 以测试形式运行相同评估
```

每次运行按角色打印一行，把各次会话连同 Agent 日志、检查结果、评审回复和角色记忆目录保存到 runs/。

#### 第 15 题 `sim_eval`：Cardinal Agent 评估（10 分）

使用完整 Agent 运行 20 段模拟用户对话：4 项文档查询、3 项多跳邮件问题、2 项摘要请求、4 项 confirm 模式编程任务、3 项配对记忆会话、2 项需要澄清的问题，以及 2 项对抗任务。

**交付要求：**无新 adapter，本题评估已有实现。成功对话不少于 **16 个**得满分，少于 16 个时每少一个扣 1 分。设置 CS329Z_EVAL_SLICE=N 时，live 测试按相同比例要求成功数量并向下取整。

评分使用相同的 Agent、模拟用户和评审模型，另外选择 20 个不公开角色，任务类型比例与公开集合相同。不同运行之间结果可能相差约一个对话，因此应留出余量。

```sh
uv run pytest tests/test_sim_eval.py
# live 测试添加 -m live -s
# 查看最近一次评估后每个角色的记忆
uv run python -m cs329z_hw1.show memory
```

**低预算提示：模拟对话的调用会累积。**每段对话都会调用 Agent 模型、模拟用户模型和评审模型，全部经过带缓存的 LM。若 Agent 调用不变，重复运行不收费。迭代时使用 `--slice 3`，使用 `--only` 仅重跑一个角色或一个类别。两段摘要对话在首次运行时最贵，因为它们要求处理的日期各约有 250 封邮件，摘要流水线需逐封分类。

参考实现完整运行全部 20 段对话，未缓存时约 **0.18 美元、3 分钟**。

以下三点可能使费用高于预期：评审模型是运行中最贵的模型，并会评审每段对话；修改系统提示或工具描述会改变每次 Agent 调用的第一条消息，导致 Agent 级 live 测试重新产生未缓存调用；评估为各对话创建新临时工作目录，如果提示或工具结果包含绝对路径，每次路径变化都会破坏缓存命中。

## 6. 书面材料（原文第 23–24 页）

### 第 16 题 `field_notes`：使用你自己的 Agent（10 分）

写设计备忘录前，像员工一样使用 Agent。运行 `uv run python -m cs329z_hw1.chat`，采用默认 confirm 模式，提出至少五个自己设计的请求，覆盖：

1. 公司文档问题。
2. 邮件档案问题。
3. 需要终端完成的请求。
4. 行动前应先向你询问的请求。
5. 应拒绝执行，或由你拒绝批准的请求。

退出时，各次对话保存在 runs/。

然后编写 **field_notes.pdf，全文最多一页**。每个请求用几句话说明：Agent 做了什么、答案是否正确（与公司文档或邮件档案核对），以及你观察到什么或据此修改了什么。

**交付要求：**提交 field_notes.pdf（一页，11 磅字号）和其中引用的 `runs/chat-*.json`。评分检查是否覆盖五种情况、是否真正核对正确性，以及文字是否与保存的对话一致。

### 第 17 题 `design_memo`：运行框架设计备忘录（20 分）

首先一个关于检索器的问题，随后每项第 2 部分设计决策各一个问题。教学团队希望了解你实现了什么，以及背后的理由。

1. **检索器（第 3 题 bm25）**：使用 show bm25 运行几个自己提出的查询。排序错在哪里，为什么？
2. **工具调用协议（第 6 题 tool_protocol）**：描述最终采用的格式，以及如何决定采用它。
3. **终止规则（第 7 题 agent_loop）**：当模型说要调用工具，例如“我来查一下”，但没有真正写出调用时，循环如何处理？
4. **搜索工具（第 9 题 search_docs）**：如何选择搜索结果显示的 snippet，以及读取返回的窗口？
5. **终端输出呈现策略（第 10 题 terminal）**：命令输出远超可容纳范围时，模型会看到什么？
6. **压缩策略（第 11 题 compaction）**：如何工作？先移除什么？哪些内容绝不丢弃？
7. **记忆策略（第 12 题 memory）**：检查评估后的记忆存储（`uv run python -m cs329z_hw1.show memory` 可打印）。里面有什么？保存为记忆是否合理？是否漏掉本应有用的信息？
8. **批准策略（第 13 题 interactive）**：confirm 模式下哪些调用无需批准，为什么这样是安全的？
9. **sandbox.py**：在你的机器上，它能阻止命令做什么？命令仍然可以做什么？
10. **整体限制**：你认为整个运行框架有哪些局限？

**交付要求：**design_memo.pdf，最多两页，11 磅字号。评分检查回答是否描述了代码和已保存评估对话中确实存在的决策，以及理由是否站得住脚。

## 7. 提交（原文第 25 页）

向 Gradescope 提交：

1. 仓库 zip，**排除 `.env`、`.lm_cache/`、`data/emails/`**；保留 runs/，包含最终评估和亲自聊天的记录。
2. 第 16 题的 field_notes.pdf。
3. 第 17 题的 design_memo.pdf。

教学团队会将你的 `cs329z_hw1/` 包复制到干净的 starter 中，运行两套测试。zip 中其他位置的文件，包括自己添加到 tests/ 或仓库根目录的文件，都不进入评分运行环境；对课程 provided 文件的修改会被丢弃。

每题分值划分为确定性测试与 live 测试两部分，各自按通过测试比例给分。第 15 题按其自身规则评分。

| 题目 | 确定性测试 | Live | 总分 |
| --- | ---: | ---: | ---: |
| priority | 1 | 2 | 3 |
| daily_digest | 1 | 3 | 4 |
| bm25 | 8 | 0 | 8 |
| email_qa | 2 | 6 | 8 |
| tool_registry | 3 | 0 | 3 |
| tool_protocol | 2 | 2 | 4 |
| agent_loop | 8 | 0 | 8 |
| cardinal | 2 | 0 | 2 |
| search_docs | 2 | 3 | 5 |
| terminal | 2 | 4 | 6 |
| compaction | 5 | 3 | 8 |
| memory | 3 | 5 | 8 |
| interactive | 7 | 0 | 7 |
| guardrails | 2 | 2 | 4 |
| sim_eval | 0 | 10 | 10 |
| 自动评分合计 | 48 | 40 | 88 |
| field_notes | — | — | 10 |
| design_memo | — | — | 20 |
| **总计** | | | **118** |

## 致谢（原文第 25 页）

本作业由 Michael Ryan 为 Stanford CS329Z Engineering AI Agents 课程设计与构建，得到了 Claude Fable 5.1 的大量帮助。教学团队感谢所有分享作业想法和反馈的人，特别感谢 Houjun (Jack) Liu、Owen Queen、Shreyas Sharma 和 Anantharaman Iyer 完成早期版本并提供宝贵反馈。

欢迎将本作业用于其他课程，只需简要注明来源。作业采用 MIT 许可证发布。

## 参考文献（原文第 26 页）

以下保留英文书目信息以便检索，括号中附中文题名释义。

- Bryan Klimt and Yiming Yang. **The Enron corpus: A new dataset for email classification research.**（Enron 语料：用于邮件分类研究的新数据集。）In *European Conference on Machine Learning (ECML)*, pages 217–226, 2004.
- Stephen Robertson and Hugo Zaragoza. **The probabilistic relevance framework: BM25 and beyond.**（概率相关性框架：BM25 及其扩展。）*Foundations and Trends in Information Retrieval*, 3(4):333–389, 2009. doi: 10.1561/1500000019.
- Stephen E. Robertson, Steve Walker, Susan Jones, Micheline M. Hancock-Beaulieu, and Mike Gatford. **Okapi at TREC-3.**（TREC-3 中的 Okapi。）In *Proceedings of the Third Text REtrieval Conference (TREC-3)*, pages 109–126, 1995.
- Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. **ReAct: Synergizing reasoning and acting in language models.**（ReAct：让语言模型的推理与行动协同。）In *International Conference on Learning Representations (ICLR)*, 2023.
- Shunyu Yao, Noah Shinn, Pedram Razavi, and Karthik Narasimhan. **τ-bench: A benchmark for tool-agent-user interaction in real-world domains.**（τ-bench：真实领域中工具、Agent 与用户交互的基准。）*arXiv preprint arXiv:2406.12045*, 2024.
