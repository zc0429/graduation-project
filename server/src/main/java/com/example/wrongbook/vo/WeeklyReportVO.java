package com.example.wrongbook.vo;

import lombok.Data;

import java.util.List;

/**
 * 学情周报视图（供 ECharts 渲染）
 */
@Data
public class WeeklyReportVO {

    /** 本周起始日期（周一） */
    private String weekStart;

    /** 本周新增错题数 */
    private Long newQuestionCount;

    /** 错题总数 */
    private Long totalQuestionCount;

    /** 复习完成数（本周） */
    private Long reviewFinishedCount;

    /** 复习任务总数（本周应完成） */
    private Long reviewTotalCount;

    /** 掌握度均值（0-100） */
    private Double masteryAvg;

    /** 各知识点掌握度分布（雷达图） */
    private List<KpMastery> knowledgeMastery;

    /** 薄弱知识点（掌握度最低的 top5） */
    private List<KpMastery> weakPoints;

    /** 本周每日新增错题（柱状图） */
    private List<DateCount> dailyNewQuestions;

    /** 本周每日练习量（折线图） */
    private List<DateCount> dailyPractices;

    @Data
    public static class KpMastery {
        private Long knowledgePointId;
        private String name;
        private Double mastery;
        private Long questionCount;
    }

    @Data
    public static class DateCount {
        private String date;
        private Long count;

        public DateCount(String date, Long count) {
            this.date = date;
            this.count = count;
        }
    }
}
