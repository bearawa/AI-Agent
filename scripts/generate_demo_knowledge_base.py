import os
import sys
import pypdf
from typing import List

# 引入 ReportLab 库
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("错误：未找到 reportlab 依赖。请先执行 `pip install reportlab`。")
    sys.exit(1)

# 注册中文字体
def register_chinese_font() -> str:
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
        "C:/Windows/Fonts/simsun.ttc",   # 宋体
        "C:/Windows/Fonts/simsun.ttf",   # 宋体 ttf
        "C:/Windows/Fonts/msyh.ttf"      # 微软雅黑 ttf
    ]
    selected_font = None
    for fp in font_paths:
        if os.path.exists(fp):
            selected_font = fp
            break

    if not selected_font:
        print("错误：未在系统 C:/Windows/Fonts/ 路径下找到 msyh.ttc 或 simsun.ttc 中文字体。")
        print("请在 .env 中设置合适的字体或人工配置系统字体。")
        sys.exit(1)

    try:
        # ttc 需要尝试 subfontIndex
        pdfmetrics.registerFont(TTFont('ChineseFont', selected_font, subfontIndex=0))
        pdfmetrics.registerFont(TTFont('ChineseFontBold', selected_font, subfontIndex=0))
    except Exception:
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', selected_font))
            pdfmetrics.registerFont(TTFont('ChineseFontBold', selected_font))
        except Exception as e:
            print(f"注册字体失败: {e}")
            sys.exit(1)
            
    return selected_font

# 动态计算总页数的 Canvas 包装器
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("ChineseFont", 9)
        self.setFillColor(colors.HexColor('#5a6e85'))
        
        # 每页绘制统一的页脚：第 X 页 / 共 Y 页
        page_text = f"第 {self._pageNumber} 页 / 共 {page_count} 页"
        self.drawCentredString(A4[0] / 2.0, 30, page_text)
        
        # 页面顶部横线和“演示资料”标记
        self.setStrokeColor(colors.HexColor('#e1e8ed'))
        self.setLineWidth(0.5)
        self.line(54, A4[1] - 40, A4[0] - 54, A4[1] - 40)
        self.drawString(54, A4[1] - 35, "演示资料 - 仅用于系统测试")
        self.drawRightString(A4[0] - 54, A4[1] - 35, "非中南财经政法大学官方文件")
        
        self.restoreState()

# 创建通用 PDF 的函数
def build_pdf(filename: str, title: str, sections: List[List[str]]):
    """
    生成一个至少2页的演示PDF文件。
    sections: [[section_title, section_body_text_with_newlines], ...]
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # 统一定义中文字体样式
    title_style = ParagraphStyle(
        'CN_Title',
        parent=styles['Heading1'],
        fontName='ChineseFontBold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e3c72'),
        alignment=1, # 居中
        spaceAfter=20
    )
    
    h2_style = ParagraphStyle(
        'CN_H2',
        parent=styles['Heading2'],
        fontName='ChineseFontBold',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#2a5298'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'CN_Body',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10
    )
    
    warning_style = ParagraphStyle(
        'CN_Warning',
        parent=styles['Normal'],
        fontName='ChineseFont',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#d9383a'),
        backColor=colors.HexColor('#fdf2f2'),
        borderColor=colors.HexColor('#f8b4b4'),
        borderWidth=0.5,
        borderPadding=8,
        spaceAfter=15
    )

    story = []

    # 1. 标题
    story.append(Paragraph(title, title_style))
    
    # 2. 首页必须标注的演示信息
    story.append(Paragraph(
        "⚠️ <strong>重要提示：</strong> 本文档内所有内容均为演示资料，并非中南财经政法大学官方文件。文档中所载数据、政策、时间、流程、地点及联系方式仅供智能客服平台进行问答测试使用，切勿当作真实规定参考。",
        warning_style
    ))
    story.append(Spacer(1, 10))

    # 3. 逐个写入小节
    # 为了保证文档至少 2 页，我们在写完前几小节后，强制插入一个 PageBreak()
    halfway = len(sections) // 2
    if halfway == 0:
        halfway = 1

    for idx, (sec_title, sec_body) in enumerate(sections):
        if idx == halfway:
            story.append(PageBreak())  # 强制换页，保证至少两页且完美支持页码
        
        story.append(Paragraph(sec_title, h2_style))
        
        # 将换行符转换为 Paragraph 以防排版重叠
        for para_text in sec_body.strip().split('\n'):
            if para_text.strip():
                story.append(Paragraph(para_text.strip(), body_style))
        
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)

# --- 主生成脚本 ---
def main():
    print("=== 开始生成 AIZS｜校园智能咨询平台演示知识库文件 ===")
    
    # 创建目录
    target_dir = "demo_documents"
    os.makedirs(target_dir, exist_ok=True)
    
    # 注册中文字体
    selected_font_path = register_chinese_font()
    print(f"成功注册系统字体: {selected_font_path} 并命名为 'ChineseFont'")

    # --- 1. 图书馆服务指南 PDF ---
    lib_sections = [
        ["一、 图书馆开放时间表", 
         "演示资料，非学校官方文件。\n"
         "本校图书馆各校区阅览室提供统一的服务时间，具体如下：\n"
         "• 周一至周五：8:00-22:00（全功能服务，提供人工借还及咨询）\n"
         "• 周末及节假日：9:00-21:00（自助借还服务，自习阅览区开放）\n"
         "特别提醒：因清洁及闭馆准备，图书馆将在闭馆前 30 分钟停止入馆，请各位读者合理安排时间。"],
        ["二、 图书借阅规则",
         "本科生在校期间凭校园卡最多可借阅 20 册图书。\n"
         "单次普通借阅的借期为 30 天。在图书到期前，如果该书没有被其他读者预约，本科生可申请续借 1 次，续借期同样为 30 天，自操作续借当日起算。逾期将按天暂停借阅权限。"],
        ["三、 共享自习室预约方式",
         "读者可登录演示校园服务平台的“自习室预约模块”进行预约。\n"
         "预约需提前 1 天提交，每次预约最长可使用 4 小时。预约成功后，须在预约时段开始后 15 分钟内扫码签到，否则系统自动判定为违约，累计违约 3 次将暂停预约资格 7 天。"],
        ["四、 遗失物品处理说明",
         "如在馆内不慎遗失个人财物，可前往大厅综合服务台登记并查询失物招领记录。\n"
         "图书馆不对读者的遗留物品负保管责任。每日闭馆清场时清出的无主物品将暂存在前台，保留期为 30 天，逾期无人认领的将移交后勤保障部门处理。贵重物品请务必随身携带。"]
    ]
    build_pdf(
        os.path.join(target_dir, "01_演示_图书馆服务指南.pdf"),
        "图书馆服务指南",
        lib_sections
    )

    # --- 2. 奖助学金管理办法 PDF ---
    scholarship_sections = [
        ["一、 奖助学金类别概览",
         "演示资料，非学校官方文件。\n"
         "为了促进学生全面发展，校内设立了多层次的奖助学金体系，当前主要包括以下三类：\n"
         "1. 国家奖学金：奖励学习成绩特别优秀、综合表现非常突出的学生。\n"
         "2. 国家励志奖学金：奖励家庭经济困难、品学兼优的优异学生。\n"
         "3. 校级优秀学生奖学金：用于奖励每学年综合评定在各班级名列前茅的学生。"],
        ["二、 国家奖学金申请条件",
         "国家奖学金为每学年评选一次，凡申请该奖学金的学生需具备以下基本条件：\n"
         "• 学习成绩优异：学年平均学分绩点（GPA）排名在专业前 10% 以内，且无不及格科目。\n"
         "• 综合表现突出：在社会实践、创新创业或文体活动中取得突出成果。\n"
         "• 无严重违纪记录：凡是在当学年受到警告及以上纪律处分的，一律不具备申请资格。\n"
         "• 符合当年度学校评审通知中规定的其它细则与具体指标要求。"],
        ["三、 国家励志奖学金申请条件",
         "申请国家励志奖学金的学生应当符合以下要求：\n"
         "• 家庭经济困难认定：必须在当学年已通过学校家庭经济困难学生库认定。\n"
         "• 学业成绩达到基本要求：学年平均绩点（GPA）排名在专业前 30% 以内，且没有挂科记录。\n"
         "• 品行良好：尊敬师长，团结同学，积极参加集体劳动与志愿服务。"],
        ["四、 申请流程与材料清单",
         "评选采取学生个人申请与组织推荐相结合的形式，具体流程如下：\n"
         "1. 学生提交申请：登录线上服务门户填写《奖学金申请表》，并附带官方盖章的成绩单及相关荣誉、学术证明材料。\n"
         "2. 学院初审：各学院评审小组对申请材料真实性进行核验与答辩筛选，拟定学院推荐名单并公示 3 天。\n"
         "3. 学校评审：校奖助学金管理委员会对各学院提交的材料进行复核和投票终审。\n"
         "4. 校级公示：通过终审的名单将在学校官方主页进行不少于 5 个工作日的公示，公示无异议后上报发放。"]
    ]
    build_pdf(
        os.path.join(target_dir, "02_演示_奖助学金管理办法.pdf"),
        "奖助学金管理办法",
        scholarship_sections
    )

    # --- 3. 本科招生咨询手册 PDF ---
    admission_sections = [
        ["一、 招生咨询范围说明",
         "演示资料，非学校官方文件。\n"
         "本咨询手册旨在向广大考生和家长介绍报考专业、录取规则及流程等基础常识。所有录取计划与招生数据仅为系统演示设计，具体招生政策请以当年度教育部及各省招生办公室公布的官方公报为准。\n"
         "我们提供三大类招生咨询：专业咨询、录取规则咨询以及报考流程咨询。"],
        ["二、 演示专业与特色",
         "学校开设了多门特色鲜明的专业，测试用专业如下：\n"
         "• 法学：培养掌握法学基本理论，能在国家机关、企事业单位从事法律工作的专门人才。\n"
         "• 金融学：主要方向包括货币银行学、证券投资、国际金融以及商业银行经营管理。\n"
         "• 会计学：主修财务会计、管理会计、审计学及财务分析，培养高级财会人才。\n"
         "• 信息管理与信息系统：结合计算机科学与管理科学，侧重企业数字化管理。"],
        ["三、 录取规则与重要提示",
         "录取遵循“分数优先、遵循志愿”的平行志愿投档规则。专业投档时不设专业级差。\n"
         "⚠️ 录取分数线提示：具体录取分数线、投档比例以当年度官方招生公告为准，本演示资料不提供任何真实录取分数，请勿进行盲目比对。"],
        ["四、 录取后后续关注",
         "考生被正式录取后，需保持通讯畅通，密切关注以下材料的寄递与通知：\n"
         "• 录取通知书：由招生办通过邮政 EMS 寄发至考生填写的邮寄地址。\n"
         "• 报到通知与新生指南：包含具体的报到时段安排、宿舍分配及线上预报到操作流程。"]
    ]
    build_pdf(
        os.path.join(target_dir, "03_演示_本科招生咨询手册.pdf"),
        "本科招生咨询手册",
        admission_sections
    )

    # --- 4. 新生报到指南 PDF ---
    freshman_sections = [
        ["一、 报到需准备材料",
         "演示资料，非学校官方文件。\n"
         "新生前来学校现场报到前，请确保备齐以下所有关键材料，装袋妥善保管：\n"
         "1. 录取通知书：需携带原件，报到现场用于扫码核验。\n"
         "2. 身份证原件及复印件：身份证必须在有效期内，正反面复印件建议准备 3 份。\n"
         "3. 个人近期证件照：一寸蓝底及红底免冠照片各准备 8 张，体检和建档使用。\n"
         "4. 个人学籍档案：必须确保密封完好，由个人携带或通过邮寄方式转接，拆封无效。\n"
         "5. 缴费或资助申请相关材料：已线上缴费的需保存电子回单；申请绿色通道的需携带《家庭经济困难学生认定申请表》及相关贫困证明原件。"],
        ["二、 报到现场流程",
         "报到当天设有一站式服务，基本流转如下：\n"
         "• 第一步：身份核验。新生在大门口或体育馆入口出示身份证和通知书进行电子签到。\n"
         "• 第二步：学院报到登记。前往所属学院接待处，核验档案、递交照片并领取新生资料袋。\n"
         "• Third 宿舍入住。持学院出具的入住通知单到分配好的宿舍楼管理员处办理钥匙领用。\n"
         "• 第四步：校园卡激活。可在宿管站或校园卡服务中心进行人脸采集与校园卡功能激活。\n"
         "• 第五步：参加新生入学教育。关注班级通知，按时参加当晚的第一次主题班会和入学教育安排。"],
        ["三、 天气与生活温馨提示",
         "报到通常处于夏秋交替时节。请各位同学和家长提前关注学校所在城市的天气预报，准备好雨具、遮阳防晒用品以及常用生活与防蚊药物。学校寝室配有基本家具，床上用品及个人洗漱用具可自备，亦可在后勤指定的校园超市就近购买。"]
    ]
    build_pdf(
        os.path.join(target_dir, "04_演示_新生报到指南.pdf"),
        "新生报到指南",
        freshman_sections
    )

    # --- 5. 后勤与校园生活手册 PDF ---
    life_sections = [
        ["一、 宿舍报修指南",
         "演示资料，非学校官方文件。\n"
         "学生宿舍如出现水电故障、门锁损坏、家具损坏等，可通过以下渠道提请维修：\n"
         "• 自助报修：登录演示“校园服务平台”进入后勤报修模块，填写详细宿舍号、损坏部位并上传现场照片。后勤人员通常会在 24 小时内上门维修。\n"
         "• 紧急突发状况：如爆管、漏电或锁房门，请直接联系宿舍楼一楼宿管值班室，由管理员进行紧急呼叫派工。请勿自行拆卸强电设施。"],
        ["二、 食堂服务与就餐时段",
         "校内设有多个学生食堂，提供丰富的南北风味。就餐时间段统一安排如下：\n"
         "• 早餐时段：6:30 - 9:00\n"
         "• 午餐时段：11:00 - 13:30\n"
         "• 晚餐时段：17:00 - 19:30\n"
         "食堂各档口具体餐品和售价以现场公示为准。就餐请使用校园卡或线上认证绑定的二维码支付，不接受现金。"],
        ["三、 校园卡与校园网络",
         "校园卡是您在校生活的数字凭证，集成了食堂消费、图书馆门禁、宿舍进出和考勤功能。如遗失请第一时间通过微信服务号挂失，防止资金损失。\n"
         "关于校园网络：新生在完成报到手续并激活身份认证后，可登录校园网门户。我们提供基础免费流量包以及高速包月套餐。具体宽带速率和计费套餐请在线上校园网管理中心查看。"],
        ["四、 校医院医疗服务",
         "在校期间如有身体不适，可持校园卡前往校医院挂号就诊。校医院设有内科、外科、牙科及急诊。\n"
         "若遇紧急突发重症，应拨打 120 呼叫急救车，或直接送往最近的正规三甲医疗机构。校医院提供基础医疗报销和转诊审核服务，学生就医前请详细了解医疗保险报销比例。"]
    ]
    build_pdf(
        os.path.join(target_dir, "05_演示_后勤与校园生活手册.pdf"),
        "后勤与校园生活手册",
        life_sections
    )

    # --- 6. 校历与重要日期 TXT ---
    calendar_text = (
        "校历与重要日期指南\n"
        "演示资料，非中南财经政法大学官方文件。具体日期以学校每学年正式发布的校历为准，本文件仅用于系统演示。\n\n"
        "【说明加长段落】本篇校历演示手册是为了满足大语言模型检索系统对大文本分割测试的字数要求（必须大于1200个中文字符）而专门扩充的。在真实的客服问答场景中，系统往往需要处理各种动辄数千字的长篇官方公告与规章制度，本篇校历的加长设计正是为了深度测试分词器在标点换行处的平滑过渡，以及向量数据库在跨越长文本检索时的命中率和召回精度。请师生在阅读重要时间节点时，注重核实各阶段教学事务的具体时限与要求。\n\n"
        "一、 春季学期重要教学节点安排\n"
        "为了方便全体师生做好新学期的教学准备与规划，演示系统特别整理了春季学期的关键教学日程。请大家合理规划个人时间，确保各项任务按时完成：\n"
        "1. 开学准备周：在春季学期正式开课前一周，学校列为开学准备周。在此期间，教师需完成教案编写、课件上传以及教学器材的调试；学生则需要登录选课系统，完成重修、补退选课程的最终确认。图书馆及自习室在此期间恢复正常开放。\n"
        "2. 正式上课时间：春季学期第一周的周一为正式上课时间。所有课程按既定课表在线下各多媒体教室或实验室授课。请同学们提前十分钟到课，避免迟到。对于旷课或迟到的同学，任课教师有权按考勤管理条例扣减平时成绩。\n"
        "3. 期中教学检查周：通常设定在学期的第九周或第十周。在此期间，教务处及督导组将深入课堂听课，评估教师教学质量；同时各学院会召开学生座谈会，收集关于课程难度、作业负担及后勤服务的反馈意见。期中考试亦多在此阶段由各任课老师灵活组织。\n"
        "4. 期末复习与考试周：学期的第十七周为停课复习周，第十八周和第十九周为全校期末统一考试周。请同学们积极复习迎考，严防作弊行为。考场内必须服从监考老师指挥，手机等通讯工具必须处于关机状态并统一放置在指定区域。\n"
        "5. 寒暑假安排说明：春季学期结束后，暑假通常从七月上旬开始，至八月下旬结束，总时长约为六至七周；秋季学期结束后，寒假通常从一月中旬开始，至二月中旬结束，时长约为四周。具体放假与收假日期，教务处会提前一个月发布放假通知。寒暑假期间，留校学生需提前向辅导员和宿管中心提交留校申请，并服从假期集中住宿和安全防火规定。\n\n"
        "二、 选课与考试补充问答说明\n"
        "为帮助学生解答教学日常事务，在此列出常见问题：\n"
        "• 选课限制：普通本科生每学期修读的学分上限为 25 学分，下限为 15 学分，以防止课业压力过重或学分积累过慢。专业必修课在第一阶段由系统自动置课，通识选修课则需学生通过“意愿值”选课机制在选课网自主抢选。\n"
        "• 缓考申请：若在期末考试前因急性突发重病（需出示校医院或三甲医院诊断证明）或国家级重大赛事冲突无法参加考试，可在考前 24 小时前向学院教学秘书提交《缓考申请表》。缓考获批后，该门课程平时成绩保留，期末考试随下一学期的补考一同进行，成绩按期末正考记录。未申请或申请未获批而缺考的，一律按旷考处理，成绩记为零分。\n"
        "• 成绩评定与申诉：课程最终成绩由平时成绩（含考勤、作业、期中）与期末正考成绩按比例加权得出，一般比例为 3:7 或 4:6。学生若对成绩有异议，可在新学期开学后两周内，向开课学院提交书面申诉，由教务处和学院联合成立的专家小组调阅答卷进行复核。逾期不再受理申诉。\n"
    )
    with open(os.path.join(target_dir, "06_演示_校历与重要日期.txt"), 'w', encoding='utf-8') as f:
        f.write(calendar_text)

    # --- 7. 校园常见问题 TXT ---
    faq_text = (
        "校园常见问题一览表\n"
        "演示资料，非中南财经政法大学官方文件。本文件整理了校园生活中最常被学生和家长询问的问题，仅用于本客服平台进行功能性演示和测试，所有具体规则请以实际规章为准。\n\n"
        "【说明加长问答】\n"
        "问：学校的后勤保障如宿舍空调和热水如何收费与供应？\n"
        "答：新生寝室均已完成了空调安装。空调由学生在报到后登录线上服务平台的后勤卡务模块自助绑定租赁或交纳基础电费使用，电价执行本地民用电标准。学生热水供应则是通过宿舍内的智能热水计量器插卡或扫码消费，水温恒定在 50 度左右，按实际使用的升数进行阶梯计费，保障学生洗漱水温适宜。若在使用中遇到水压不足或读卡器故障，请随时通过报修平台反映。\n\n"
        "问：学校有几个食堂？各自的饮食特色是什么？\n"
        "答：为了满足来自全国各地不同籍贯学生的饮食习惯，演示校区内共设有三个学生大食堂。第一食堂偏向于南方风味，主打淮扬菜、江南精细点心及各类煨汤；第二食堂则主打北方特色面食，如大排面、兰州拉面、陕西肉夹馍以及手工水饺；第三食堂则集合了川湘菜系与各类民族风味特色档口，提供麻辣香锅、黄焖鸡米饭等快捷餐饮，各食堂均在早中晚规定时段正常运转。\n\n"
        "【问答列表】\n"
        "问：图书馆几点关门？\n"
        "答：图书馆周一至周五的闭馆时间为晚上 22:00，周末及法定节假日的闭馆时间为晚上 21:00。需要特别注意的是，为保证离馆工作的顺利进行，图书馆将在闭馆前 30 分钟（即周一五 21:30，周末 20:30）停止读者入馆，请大家妥善安排阅览时间并准时出馆。\n\n"
        "问：图书馆怎么续借图书？\n"
        "答：学生在借阅图书后，如果未到期且该图书没有被其他读者预约，可以申请续借 1 次。续借可通过线上校园服务门户的“我的图书馆”模块自助操作，或者使用馆内的自助借还机完成。续借的有效期自您操作成功当日起重新计算 30 天，请在到期前及时处理以免违约。\n\n"
        "问：奖学金有哪些？\n"
        "答：本系统演示资料所列的奖学金包括：国家奖学金（主要面向特别优秀的学生）、国家励志奖学金（主要面向家庭经济困难且品学兼优的学生），以及校级优秀学生奖学金（根据每学年的成绩和综合评议排名进行评定）。所有具体发放名额和金额以当年评审文件为准。\n\n"
        "问：奖学金申请条件是什么？\n"
        "答：不同类型的奖学金申请条件不同。申请国家奖学金需要学年 GPA 成绩在专业前 10% 以内，且综合表现突出、无任何严重违纪记录；申请国家励志奖学金则要求必须先通过当学期的家庭经济困难认定，且 GPA 排名在专业前 30% 以内；校级优秀学生奖学金则根据学生学年的 GPA 以及德育素质综测分进行班级内排序选拔。\n\n"
        "问：新生报到需要准备什么？\n"
        "答：新生现场报到必须准备好以下材料：第一是录取通知书原件，第二是本人二代身份证原件及 3 份正反面复印件，第三是 8 张一寸证件近照，第四是密封完好的个人学籍档案袋，第五是已缴费回执单或家庭经济困难绿色通道申请表。另外建议根据所在城市的气候准备防雨工具和基础药品。\n\n"
        "问：宿舍报修怎么提交？\n"
        "答：日常的宿舍设施损坏，可以通过登录线上“校园服务平台”的后勤报修系统提交。您需要准确选择宿舍楼、寝室号，描述故障详情并上传损坏照片，后勤维修人员将在 24 小时内接单上门。如果是水管爆裂、电路起火等紧急突发故障，请第一时间告知一楼宿管值班室，由值班老师呼叫值班电工或水工进行紧急抢修。\n\n"
        "问：校园卡丢失怎么办？\n"
        "答：校园卡一旦丢失，为了避免被冒刷，请立即通过微信公众号“演示校园服务号”中的“卡务大厅”进行自助挂失，或者登录线上校园网门户挂失。挂失后卡内资金将被冻结。如果随后找到了卡，可以线上解挂；如果确认卡已无法找回，请携带身份证件前往校园卡服务大厅办理补卡，补卡需缴纳工本费并重写卡片数据。\n\n"
        "问：校园网怎么开通？\n"
        "答：新生在完成线下报到和身份信息激活后，可登录校园网自服务门户（默认账号为学号，初始密码为身份证后六位）。系统默认赠送基础免费校园网套餐，适用于基础网页浏览。如果需要访问高速互联网、下载大文件或畅玩网络游戏，可在线自助开通包月高速宽带包，费用将直接从校园卡余额中扣除。\n\n"
        "问：找不到对应资料时系统应该如何回答？\n"
        "答：若用户提问的问题超出了本地知识库的参考资料范畴，或者本地知识库未提供相关的依据支持，AI 助手在回答时应该诚实、严谨地告知用户：“当前知识库未检索到相关依据”，并温和地建议用户咨询学校的有关管理部门、辅导员或登录学校的正式公告系统获取官方权威通知，绝对不得杜撰事实。\n"
    )
    with open(os.path.join(target_dir, "07_演示_校园常见问题.txt"), 'w', encoding='utf-8') as f:
        f.write(faq_text)

    # --- 8. 测试问题集 TXT ---
    questions_list = [
        "# --- 图书馆类问题 ---",
        "图书馆几点关门？",
        "图书馆周末几点开门？",
        "周末可以在图书馆自习吗？",
        "本科生最多可以借几本书？",
        "借的图书快到期了，可以续借几次？",
        "自习室怎么预约？",
        "在图书馆丢了手机去哪里找？",
        "闭馆前多久不能进图书馆？",
        "# --- 奖助学金类问题 ---",
        "奖学金有哪些？",
        "国家奖学金申请条件是什么？",
        "国家奖学金要多少绩点？",
        "受到警告处分还能拿国奖吗？",
        "国家励志奖学金申请条件是什么？",
        "拿国家励志奖学金必须是困难户吗？",
        "奖学金申请表交给谁？流程是什么？",
        "奖学金公示期是几天？",
        "# --- 招生类问题 ---",
        "本科有哪些报考专业？",
        "法学专业学什么？",
        "金融学专业学什么？",
        "平行志愿是怎么录取的？",
        "录取分数线是多少？",
        "学校今年各省录取分数线是多少？",
        "# --- 新生报到类问题 ---",
        "新生报到要准备什么？",
        "学籍档案拆开了可以交吗？",
        "报到需要带几张照片？",
        "绿色通道怎么办理？",
        "报到现场有哪些流程？第一步干什么？",
        "# --- 后勤生活类问题 ---",
        "宿舍怎么报修？",
        "自来水管爆了怎么办？",
        "食堂什么时间有早饭？",
        "食堂买饭能用微信钱包吗？",
        "校园卡丢了去哪里补办？",
        "新生怎么用校园网络？",
        "生病了怎么去校医院看病？",
        "# --- 无法从资料回答的问题（用于防编造测试） ---",
        "学校今年真实录取分数线是多少？",
        "校长办公室电话是多少？",
        "火星大学食堂的早餐几点开？",
        "校园卡里丢了 100 块钱能赔吗？"
    ]
    with open(os.path.join(target_dir, "08_演示_测试问题集.txt"), 'w', encoding='utf-8') as f:
        f.write("\n".join(questions_list))

    # --- 9. 自动生成 README_演示资料说明.md ---
    readme_md = """# AIZS｜校园智能咨询平台 演示资料库说明文档

> [!WARNING]
> **重要声明**：本目录下所有文件均为**测试演示资料**，所有政策、专业设置、时段安排、流程指引均非中南财经政法大学官方正式规定。所有内容仅用于系统功能测试，请勿作为真实规定参考。

## 📁 文件清单与功能对照

| 文件名 | 类型 | 主要内容 | 适合测试的功能点 |
| :--- | :---: | :--- | :--- |
| `01_演示_图书馆服务指南.pdf` | PDF | 开放时间、借阅借期与册数、闭馆时间、自习室预约、失物处理 | 测试 PDF 物理页码还原、借阅规则定位、时间类问答。 |
| `02_演示_奖助学金管理办法.pdf` | PDF | 国奖、励志奖学金、校级奖学金的申请条件、申请材料和评审流程 | **多轮追问测试重点**。问“奖学金有哪些”再追问“申请条件是什么”。 |
| `03_演示_本科招生咨询手册.pdf` | PDF | 专业大类特色（法学、金融等）、录取通知书寄递、录取后关注事项 | **防编造测试**（分数线免责声明）。 |
| `04_演示_新生报到指南.pdf` | PDF | 入学携带材料清单、一站式报到步骤、天气温馨提示 | 复合问题测试（材料+天气）。 |
| `05_演示_后勤与校园生活手册.pdf` | PDF | 宿舍网络自助开通、食堂营业时段、校医院就医报销流程、在线报修 | 后勤细节问答。 |
| `06_演示_校历与重要日期.txt` | TXT | 准备周、正式上课、期中教学检查、期末停课考试、假期待遇 | 测试 TXT 解析及长文本中文切片逻辑（长度约1500字）。 |
| `07_演示_校园常见问题.txt` | TXT | 图书馆、校园网、挂失、绿色通道等一问一答、知识库未命中答复词 | **基本检索与找不到答案的免责回复测试**（长度约2000字）。 |
| `08_演示_测试问题集.txt` | TXT | 分组列出 30+ 条校园咨询测试提问 | 用于批量测试或手动快速复制问题。 |

---

## 🛠️ 推荐测试方案

### 1. 推荐上传顺序
建议先在网页上依次上传：
1. `02_演示_奖助学金管理办法.pdf`
2. `01_演示_图书馆服务指南.pdf`
3. `07_演示_校园常见问题.txt`
4. `04_演示_新生报到指南.pdf`

### 2. 基础档功能验证问答序列

#### 验证项 A：多轮追问上下文关联（奖助学金）
- **第一轮提问**：`学校有哪些奖学金可以申请？`
- **预期助手回答**：列出国家奖学金、国家励志奖学金、校级优秀学生奖学金，说明出自《奖助学金管理办法.pdf》。
- **第二轮追问**：`那它们的申请条件分别是什么？`
- **预期助手回答**：应成功识别“它们”是指上一轮中的三类奖学金，并从资料中摘录各自的 GPA 比例及困难认定等条件，正确溯源。

#### 验证项 B：来源出处物理追溯（页码与片段自适应）
- **提问**：`自习室怎么预约？有次数限制吗？`
- **预期助手回答**：回答需要提前 1 天线上预约，最长 4 小时，3 次违约暂停 7 天。下方来源折叠面板展开应清晰标明：`01_演示_图书馆服务指南.pdf (第 2 页)`。
- **提问**：`校园卡丢了该怎么挂失？`
- **预期助手回答**：说明需要到微信公众号或线上挂失。下方来源展开应清晰标明：`07_演示_校园常见问题.txt (片段 6)`（因为 TXT 无物理页码，只做片段自适应编号，不能伪造页码）。

#### 验证项 C：坚守知识边界，防编造测试（无资料时不瞎编）
- **提问**：`学校今年的法学专业录取分数线是多少？`
- **预期助手回答**：依据《本科招生咨询手册》的免责声明，回答：*本演示资料不提供真实录取分数，具体分数线以当年度官方招生公告为准*；或者直接回答：*“当前知识库未检索到相关依据”*。
- **提问**：`校长办公室的电话和邮箱是多少？`
- **预期助手回答**：由于所有资料中均没有写任何电话号码，助手必须回答：*“当前知识库未检索到相关依据”*，严防幻觉编造。
"""
    with open(os.path.join(target_dir, "README_演示资料说明.md"), 'w', encoding='utf-8') as f:
        f.write(readme_md)

    print("--- 演示文件写入完毕，开始调用 pypdf 和 UTF-8 进行完整性自校验 ---")
    
    # --- 10. 自动调用 pypdf 和 UTF-8 验证 ---
    check_errors = []
    
    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        file_size = os.path.getsize(file_path)
        
        # 对 PDF 进行读取校验
        if filename.endswith(".pdf"):
            try:
                reader = pypdf.PdfReader(file_path)
                num_pages = len(reader.pages)
                
                # 校验页数是否大于等于2
                if num_pages < 2:
                    check_errors.append(f"[错误] {filename} 页数不足 2 页（实际: {num_pages} 页）")
                
                # 校验能否提取文本
                extracted_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text
                
                if not extracted_text.strip():
                    check_errors.append(f"[错误] {filename} 提取出的文本内容为空")
                else:
                    # 检索关键词测试
                    test_keywords = ["演示资料", "非学校官方文件"]
                    if filename == "01_演示_图书馆服务指南.pdf":
                        test_keywords.append("周一至周五：8:00-22:00")
                    elif filename == "02_演示_奖助学金管理办法.pdf":
                        test_keywords.append("国家奖学金")
                    elif filename == "04_演示_新生报到指南.pdf":
                        test_keywords.append("录取通知书")
                    
                    for kw in test_keywords:
                        if kw not in extracted_text:
                            check_errors.append(f"[错误] {filename} 文本中未检测到关键短语: '{kw}'")
                
                print(f"[成功] PDF 校验成功：{filename} (大小: {file_size/1024:.2f} KB, 页数: {num_pages})")
            except Exception as e:
                check_errors.append(f"[错误] PDF 解析崩溃：{filename}，错误: {e}")
        
        # 对 TXT 进行读取校验
        elif filename.endswith(".txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                text_len = len(text)
                # 校验字数要求
                if filename == "06_演示_校历与重要日期.txt" and text_len < 1200:
                    check_errors.append(f"[错误] {filename} 字符数不足 1200 字（实际: {text_len} 字）")
                elif filename == "07_演示_校园常见问题.txt" and text_len < 1800:
                    check_errors.append(f"[错误] {filename} 字符数不足 1800 字（实际: {text_len} 字）")
                
                print(f"[成功] TXT 校验成功：{filename} (大小: {file_size/1024:.2f} KB, 字符数: {text_len})")
            except UnicodeDecodeError:
                check_errors.append(f"[错误] TXT 编码错误：{filename} 无法使用 UTF-8 正确读取")
            except Exception as e:
                check_errors.append(f"[错误] TXT 读取异常：{filename}，错误: {e}")

    print("\n=== 校验报告结论 ===")
    if not check_errors:
        print("[完成] 所有演示资料全部通过自动校对！PDF 可正常提取，TXT 字符长度及编码完好。")
    else:
        print("[提示] 发现以下校验错误：")
        for err in check_errors:
            print(err)
        sys.exit(1)

if __name__ == "__main__":
    main()
