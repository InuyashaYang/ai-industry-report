#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from fpdf import FPDF

FONT_PATH = os.path.expanduser("~/.local/share/fonts/windows-cjk/msyh.ttc")
OUT_PATH = os.path.expanduser("~/guozhitou_5th.pdf")

REPORT = """国智投洞见 | 第5期（2026.02.22-03.01）
出品：国智投 · OpenClaw AI 研究助手
覆盖分类：模型/Agent · 具身智能 · 算力芯片 · 投融资动态
报告周期：2026.02.22 - 2026.03.01

============================================================

信息源说明

本期报告采集自量子位、机器之心、新智元、36氪等主要AI媒体公众号，通过搜狗微信搜索引擎抓取近7天文章，覆盖大模型、Agent、具身智能、算力、投融资等核心赛道。数据截止时间：2026年3月1日上午。

============================================================

洞见

洞见一：Agent落地遭遇"真实世界税"，DevOps基准成为照妖镜
新智元援引首个真实DevOps基准测试显示，当前主流AI Agent全链路成功率近乎0%。这表明Agent从Demo到生产级落地之间存在巨大鸿沟，"AI替代程序员"的叙事过早。真正的产业机会在于细分垂直场景的半自动化，而非全自动化Agent。

洞见二：具身智能进入"量产为王"淘汰赛，融资窗口正在收窄
以因时机器人C+轮、智元进德国、智平方B轮超10亿为代表，头部企业已完成从"技术验证"到"规模量产"的跃迁。2026年将是大洗牌之年。

洞见三：AI算力范式正在从"GPU通用计算"向"模型专属芯片"迁移
字节自研芯片SeedChip量产、LPU成A股新主线——两个信号指向同一判断：英伟达主导的GPU时代正在被更高效的专用架构蚕食。

============================================================

一、模型/Agent应用

【AI Agent化浪潮席卷消费与产业】
量子位2月26日报道，从手机助手到工业OCR，AI Agent正加速渗透消费电子与产业场景。MiniMax推出MaxClaw新模式，中国企业调用大模型日均已达37万亿tokens，规模化应用进入实质爆发阶段。
引用来源：量子位（2026-02-26）
洞见：Token消耗量级验证了中国企业AI应用深度正在快速追赶西方，但消耗量高不等于ROI为正。下阶段竞争焦点将从"用量"转向"产出效率"。

【Agent DevOps基准：全链路成功率0%的警示】
新智元2月27日报道，首个真实DevOps基准测试曝出AI Agent致命短板：全链路任务完成率接近0%。测试涵盖代码提交、CI/CD、部署等完整软件工程流程，暴露出当前Agent在复杂工具链调用和错误恢复上的根本性缺陷。
引用来源：新智元（2026-02-27）
洞见：这一数据将重塑资本市场对"AI程序员"赛道的估值逻辑。短期内辅助编程（Copilot类）仍是确定性机会，全自动Agent编程需要等待下一代推理模型突破。

============================================================

二、具身智能

【2026具身智能六大趋势：量产与社会接受度成最大挑战】
机器之心2月27日报道，2026年具身智能行业六大核心趋势：多模态感知成标配、灵巧手精度大幅提升、运动控制向自然动作靠拢、工厂场景率先规模化、隐私与信任成家庭机器人最大障碍、多模型融合架构崭露头角。
引用来源：机器之心（2026-02-27）
洞见：工厂场景是当前确定性最高的落地路径，家庭场景的社会信任建立至少还需2-3年。

【因时机器人完成C+轮融资；智元正式进入德国市场】
新智元2月25日报道，因时机器人完成数亿元C+轮融资。智元机器人宣布进入德国市场，精灵G2由均普智能负责制造，实现了"研发+量产"的分工模式。
引用来源：新智元（2026-02-25）
洞见：智元进德国是中国具身智能企业走向全球化的标志性事件。均普代工模式表明专业制造能力正在成为产业链新入口。

【智平方机器人基础模型龙头获超10亿B轮】
AI轻阅社2月25日报道，智平方（AI² Robotics）完成超10亿元B轮融资，定位全球机器人基础模型龙头企业。
引用来源：AI轻阅社（2026-02-25）
洞见：机器人基础模型正在成为独立赛道，能率先建立跨硬件平台通用模型能力的企业将占据底层话语权。

============================================================

三、算力与AI芯片

【LPU成A股AI算力新主线】
2月28日，LPU（语言处理单元）成为A股AI算力板块新主线。Groq的LPU架构在推理速度上已显著领先传统GPU。
引用来源：谷溋投资（2026-02-28）
洞见：LPU崛起标志着AI推理场景开始对通用GPU形成实质性竞争。A股LPU主题炒作成分居多，价值投资窗口在具备专用芯片IP的国内企业。

【字节自研芯片SeedChip量产；国产AI芯片厂商面临新压力】
字节跳动自研AI芯片SeedChip进入量产阶段，对摩尔线程、寒武纪等国内芯片厂商的客户黏性形成冲击。英伟达GTC 2026将发布革命性新AI芯片。
引用来源：乌拉大喵喵（2026-02-20）
洞见：大厂算力自主可控战略将倒逼国产AI芯片厂商向中小客户和垂直场景拓展。

【2026年AI算力进入推理主导、效率优先新阶段】
AI算力市场正从训练主导转向推理主导：推理算力需求占比已超训练，效率芯片需求快速增长。
引用来源：飚的（2026-02-24）
洞见：端侧推理芯片（手机SoC、车载芯片）将成为下一个万亿市场，高通、联发科、华为海思值得重点关注。

============================================================

四、投融资动态

【Kimi月之暗面连续两轮融资超12亿美元】
月之暗面（Kimi）完成连续两轮融资，总额超12亿美元，创大模型行业近一年最高记录。投资方包括阿里、腾讯等战略方。
引用来源：冯站长看天下（2026-02-24）
洞见：国内大模型头部梯队融资能力已接近OpenAI级别。"强者恒强"的马太效应将在2026年显著加剧。

【AI芯片挑战者融资5亿美元；华为哈勃参投】
一家清华系AI芯片挑战者完成5亿美元融资，投资方为华为哈勃与中关村发展集团。
引用来源：量子位（2026-02-25）
洞见：华为哈勃的战略入股说明国内算力产业链资本布局正在系统化，将加速国产AI芯片在限制场景下的替代进程。

============================================================

本期「国智投洞见」由 OpenClaw AI 研究助手自动采集生成。
飞书原文：https://feishu.cn/docx/GN8BdzEGwoJqHCx4afTcaEnxnee
内容仅供参考，不构成投资建议。"""


class CJKPdf(FPDF):
    def header(self):
        self.set_font("msyh", size=9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "国智投洞见 | 第5期（2026.02.22-03.01）", align="C")
        self.ln(4)
        self.set_x(self.l_margin)

    def footer(self):
        self.set_y(-15)
        self.set_font("msyh", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"第 {self.page_no()} 页  |  内容仅供参考，不构成投资建议", align="C")


def build_pdf():
    pdf = CJKPdf(format="A4")
    pdf.set_margins(20, 25, 20)
    pdf.add_font("msyh", style="", fname=FONT_PATH)
    pdf._font_added = True
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    def mc(text, size=10, color=(30,30,30), h=7):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("msyh", size=size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, h, text)

    for line in REPORT.strip().split("\n"):
        line = line.rstrip()
        if line.startswith("国智投洞见 | 第5期"):
            mc(line, size=18, color=(30,30,80), h=12)
            pdf.ln(2)
        elif line.startswith("====="):
            pdf.set_draw_color(180, 180, 210)
            pdf.set_x(pdf.l_margin)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.epw, pdf.get_y())
            pdf.ln(3)
        elif line.startswith(("一、", "二、", "三、", "四、")):
            pdf.ln(3)
            mc(line, size=13, color=(20,60,140), h=9)
            pdf.ln(1)
        elif line.startswith("洞见一：") or line.startswith("洞见二：") or line.startswith("洞见三：") or line == "洞见":
            mc(line, size=13 if line == "洞见" else 11, color=(60,20,120), h=8)
        elif line.startswith("【") and line.endswith("】"):
            pdf.ln(2)
            mc(line, size=11, color=(10,80,50), h=8)
        elif line.startswith("引用来源："):
            mc(line, size=9, color=(130,100,40), h=7)
        elif line.startswith("洞见："):
            mc(line, size=10, color=(60,40,100), h=7)
            pdf.ln(1)
        elif line == "":
            pdf.ln(2)
        else:
            mc(line, size=10, color=(30,30,30), h=7)

    pdf.output(OUT_PATH)
    print(f"PDF generated: {OUT_PATH}")
    return OUT_PATH


def send_email(pdf_path, to_addr):
    smtp_user = os.environ.get("SMTP_USER", "2942480781@qq.com")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = "国智投洞见 | 第5期（2026.02.22-03.01）"

    body = """您好，

附件为「国智投洞见」第5期（2026.02.22-03.01）PDF版本。

本期重点：
· Agent DevOps全链路成功率0%警示
· 具身智能"量产为王"淘汰赛加剧
· AI算力从GPU向专用芯片范式迁移
· Kimi连续融资超12亿美元

飞书原文：https://feishu.cn/docx/GN8BdzEGwoJqHCx4afTcaEnxnee

——
国智投洞见 · OpenClaw AI 研究助手
内容仅供参考，不构成投资建议。"""

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="guozhitou_5th.pdf"')
    msg.attach(part)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_addr, msg.as_string())
    print(f"Email sent to {to_addr}")


if __name__ == "__main__":
    pdf = build_pdf()
    send_email(pdf, "richard_w4@163.com")
