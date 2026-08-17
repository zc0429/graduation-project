package com.example.wrongbook.vo;

import lombok.Data;

import java.time.LocalDate;

/**
 * 复习计划视图：附错题题干摘要与科目，供复习看板展示
 */
@Data
public class ReviewPlanVO {

    private Long id;

    private Long questionId;

    /** 复习阶段（第 1-5 次） */
    private Integer reviewStage;

    private LocalDate planDate;

    /** 状态：0 待复习，1 已完成，2 已过期 */
    private Integer status;

    private Long subjectId;

    /** 题干摘要（前 60 字） */
    private String stemSummary;

    /** 错题当前掌握度 */
    private Integer mastery;
}
