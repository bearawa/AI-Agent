from typing import Dict, Any, List

def get_school_calendar(query: str = None) -> Dict[str, Any]:
    """
    查询学校校历，包括开学、放假、考试周等时间安排。
    重要：返回数据中必须明确标注“演示校历数据”。
    
    :param query: 查询关键词，如 "放假", "开学", "考试"
    :return: 包含校历信息的字典
    """
    # 模拟校历日程表
    events = [
        {"event": "秋季学期开学报到", "date": "2026-09-05 至 2026-09-06", "description": "新生及老生报到注册，领取教材。"},
        {"event": "秋季学期正式上课", "date": "2026-09-07", "description": "全校正式开始按课表上课。"},
        {"event": "国庆节放假", "date": "2026-10-01 至 2026-10-07", "description": "国庆长假，共 7 天。"},
        {"event": "期中考试周", "date": "2026-11-09 至 2026-11-13", "description": "部分公共课及专业课进行期中考核。"},
        {"event": "元旦放假", "date": "2027-01-01 至 2027-01-03", "description": "元旦假期，共 3 天。"},
        {"event": "期末考试周", "date": "2027-01-11 至 2027-01-22", "description": "全校期末集中闭卷考试。"},
        {"event": "寒假开始", "date": "2027-01-25", "description": "学生寒假正式开始。"}
    ]
    
    # 过滤事件
    matched_events = []
    if query:
        query_lower = query.lower()
        for ev in events:
            if query_lower in ev["event"].lower() or query_lower in ev["description"].lower():
                matched_events.append(ev)
    else:
        matched_events = events
        
    return {
        "query": query,
        "matched_count": len(matched_events),
        "events": matched_events,
        "is_demo": True,
        "notice": "演示校历数据，仅用于项目功能展示"
    }
