package com.example.wrongbook.service;

import com.example.wrongbook.vo.WeeklyReportVO;

/**
 * 学情报告服务（论文 5.3 类设计 (8)）：按周汇总学生的错题新增量、复习完成率、
 * 各知识点掌握度分布与变化趋势，生成可视化数据
 */
public interface ReportService {

    /**
     * 查询本周学情周报（实时聚合）。
     * 学生返回本人数据；教师返回科目维度聚合数据（教师班级视角缺口占位，见论文缺口清单 1）
     */
    WeeklyReportVO weekly();

    /** 手动触发报告生成：实时聚合并发送"周报已生成"消息（返回周报数据） */
    WeeklyReportVO generate();
}
